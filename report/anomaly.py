"""
Anomaly Detector & Watchlist Matcher — detects unusual spikes in article volume,
sentiment, or threat levels, and triggers alerts for analyst watchlists.
Owner: Jay (Lead)
Stage: 2 (Mid)
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import text

from agents.scoring.anomaly_agent import AnomalyAgent
from agents.scoring.regional_scorer import map_article_to_regions
from common.constants import DEFENCE_REGIONS, SEVERITY_MEDIUM, SEVERITY_HIGH
from common.db import get_db
from common.logger import get_logger

logger = get_logger(__name__)


def _insert_alert_if_recent_absent(
    db,
    alert_type: str,
    region: str,
    description: str,
    severity: str,
    watchlist_id: int | None = None,
    source_article_ids: list[int] | None = None,
    dedup_hours: int = 6,
) -> bool:
    """Insert an alert unless an identical alert was triggered within `dedup_hours`."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=dedup_hours)
    exists = db.execute(
        text("""
            SELECT 1 FROM alerts
            WHERE alert_type = :atype
              AND COALESCE(region, '') = COALESCE(:region, '')
              AND COALESCE(watchlist_id, -1) = COALESCE(:wid, -1)
              AND triggered_at >= :cutoff
            LIMIT 1
        """),
        {"atype": alert_type, "region": region, "wid": watchlist_id, "cutoff": cutoff},
    ).fetchone()
    if exists:
        return False

    try:
        db.execute(
            text("""
                INSERT INTO alerts (
                    alert_type, region, description, severity,
                    is_read, triggered_at, watchlist_id, source_article_ids
                ) VALUES (
                    :atype, :region, :desc, :sev,
                    FALSE, NOW(), :wid, :sids
                )
            """),
            {
                "atype": alert_type,
                "region": region,
                "desc": description,
                "sev": severity,
                "wid": watchlist_id,
                "sids": source_article_ids or [],
            },
        )
    except Exception:
        # Fallback if migration 004 optional columns have not been applied yet
        db.execute(
            text("""
                INSERT INTO alerts (alert_type, region, description, severity, is_read, triggered_at)
                VALUES (:atype, :region, :desc, :sev, FALSE, NOW())
            """),
            {"atype": alert_type, "region": region, "desc": description, "sev": severity},
        )
    return True


def detect_anomalies(window_hours: int = 24) -> list[dict]:
    """
    Scan recent data for statistical anomalies and active watchlist triggers,
    storing newly detected alerts in the `alerts` table.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    baseline_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    agent = AnomalyAgent()
    generated: List[dict] = []

    with get_db() as db:
        recent_rows = db.execute(
            text("""
                SELECT a.id, a.title, a.content, s.ring,
                       COALESCE(aa.event_type, 'general') AS event_type,
                       COALESCE(aa.sentiment, 'neutral') AS sentiment,
                       COALESCE(aa.threat_level, 2) AS threat_level
                FROM articles a
                LEFT JOIN sources s ON s.id = a.source_id
                LEFT JOIN article_analysis aa ON aa.article_id = a.id
                WHERE a.published_at >= :cutoff
                ORDER BY a.published_at DESC
                LIMIT 500
            """),
            {"cutoff": cutoff},
        ).mappings().all()

        recent_articles = [dict(r) for r in recent_rows]

        # Partition by region
        region_buckets: Dict[str, List[Dict[str, Any]]] = {reg: [] for reg in DEFENCE_REGIONS}
        for art in recent_articles:
            for reg in map_article_to_regions(art.get("title", ""), art.get("content") or ""):
                if reg in region_buckets:
                    region_buckets[reg].append(art)

        # Estimate 30-day baselines per region from threat_scores history (fallback 2.0)
        baseline_rows = db.execute(
            text("""
                SELECT region, AVG(GREATEST(article_count, 1)) AS avg_count
                FROM threat_scores
                WHERE calculated_at >= :bcutoff
                GROUP BY region
            """),
            {"bcutoff": baseline_cutoff},
        ).fetchall()
        baselines = {r.region: float(r.avg_count) for r in baseline_rows}

        checks = agent.scan_all_regions(region_buckets, baselines=baselines)
        for chk in checks:
            if chk.is_anomaly:
                sev = chk.alert_severity or SEVERITY_MEDIUM
                atype = (
                    "THREAT_ESCALATION"
                    if "high-severity" in (chk.description or "").lower()
                    else ("SENTIMENT_ANOMALY" if "sentiment" in (chk.description or "").lower() else "VOLUME_SPIKE")
                )
                src_ids = chk.provenance.source_ids if chk.provenance else []
                inserted = _insert_alert_if_recent_absent(
                    db=db,
                    alert_type=atype,
                    region=chk.region,
                    description=chk.description or f"Anomaly detected in {chk.region}",
                    severity=sev,
                    source_article_ids=src_ids[:20],
                )
                if inserted:
                    generated.append(
                        {
                            "alert_type": atype,
                            "region": chk.region,
                            "description": chk.description,
                            "severity": sev,
                        }
                    )

        # Check active analyst watchlists against recent articles
        try:
            watchlists = db.execute(
                text("SELECT id, name, query_type, query_value FROM watchlists WHERE is_active = TRUE")
            ).fetchall()
        except Exception:
            watchlists = []

        for wl in watchlists:
            qval = (wl.query_value or "").strip().lower()
            if not qval:
                continue

            matched_articles = []
            for art in recent_articles:
                haystack = f"{art.get('title', '')} {art.get('content', '')}".lower()
                if qval in haystack:
                    matched_articles.append(art)
                elif wl.query_type == "region":
                    art_regions = [
                        r.lower()
                        for r in map_article_to_regions(art.get("title", ""), art.get("content") or "")
                    ]
                    if qval in art_regions:
                        matched_articles.append(art)

            if matched_articles:
                high_sev = any(a.get("threat_level", 0) >= 7 for a in matched_articles)
                sev = SEVERITY_HIGH if high_sev else SEVERITY_MEDIUM
                desc = (
                    f"Watchlist '{wl.name}' ({wl.query_type}: {wl.query_value}) matched "
                    f"{len(matched_articles)} recent report(s): \"{matched_articles[0]['title'][:110]}\""
                )
                region_label = wl.query_value if wl.query_type == "region" else "Multi-Region"
                inserted = _insert_alert_if_recent_absent(
                    db=db,
                    alert_type="WATCHLIST_MATCH",
                    region=region_label,
                    description=desc,
                    severity=sev,
                    watchlist_id=wl.id,
                    source_article_ids=[a["id"] for a in matched_articles[:10] if a.get("id")],
                )
                if inserted:
                    generated.append(
                        {
                            "alert_type": "WATCHLIST_MATCH",
                            "region": region_label,
                            "description": desc,
                            "severity": sev,
                        }
                    )

    logger.info(f"Anomaly & Watchlist Monitor: triggered {len(generated)} new alert(s).")
    return generated
