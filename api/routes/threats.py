"""
Threats API routes — Regional Threat Scoring & 30-Day Timeline.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)

Endpoints:
    GET /api/threats            -> latest threat scores per region + trend
    GET /api/threats/{region}   -> 30-day history for a region (for Recharts)
    GET /api/threats/history/all -> 30-day multi-region matrix for comparative charts
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from common.constants import DEFENCE_REGIONS
from common.db import get_db as _get_db
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/threats", tags=["Threat Scoring"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def list_threats(db=Depends(get_db)):
    """Current threat scores for all monitored defence regions, sorted descending."""
    rows = db.execute(
        text("""
            SELECT DISTINCT ON (region)
                   id, region, score, trend, article_count, calculated_at
            FROM threat_scores
            ORDER BY region, calculated_at DESC
        """)
    ).fetchall()

    # If threat_scores has not been populated yet, compute once dynamically
    if not rows:
        try:
            from report.scorer import calculate_threat_scores

            calculate_threat_scores(window_hours=24)
            rows = db.execute(
                text("""
                    SELECT DISTINCT ON (region)
                           id, region, score, trend, article_count, calculated_at
                    FROM threat_scores
                    ORDER BY region, calculated_at DESC
                """)
            ).fetchall()
        except Exception as exc:
            logger.warning("Dynamic threat score computation skipped: %s", exc)

    items = [
        {
            "region": r.region,
            "score": round(float(r.score), 2),
            "trend": r.trend or "stable",
            "article_count": int(r.article_count or 0),
            "calculated_at": r.calculated_at,
        }
        for r in rows
    ]
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"regions": items, "total": len(items)}


@router.get("/history/all")
def get_all_threat_history(
    days: int = Query(30, ge=1, le=90),
    db=Depends(get_db),
):
    """30-day daily average threat score series grouped by date across all regions."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        text("""
            SELECT DATE(calculated_at AT TIME ZONE 'Asia/Kolkata') AS day,
                   region,
                   ROUND(AVG(score)::numeric, 2) AS avg_score,
                   MAX(article_count) AS max_articles
            FROM threat_scores
            WHERE calculated_at >= :cutoff
            GROUP BY day, region
            ORDER BY day ASC
        """),
        {"cutoff": cutoff},
    ).fetchall()

    by_date: dict = {}
    for r in rows:
        day_str = r.day.isoformat()
        if day_str not in by_date:
            by_date[day_str] = {"date": day_str}
        by_date[day_str][r.region] = float(r.avg_score)

    return {
        "days": days,
        "regions": list(DEFENCE_REGIONS),
        "series": list(by_date.values()),
    }


@router.get("/{region}")
def get_threat_history(
    region: str,
    days: int = Query(30, ge=1, le=90),
    db=Depends(get_db),
):
    """30-day threat score history for a specific region (for Recharts graph)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        text("""
            SELECT DATE(calculated_at AT TIME ZONE 'Asia/Kolkata') AS day,
                   ROUND(AVG(score)::numeric, 2) AS score,
                   MAX(article_count) AS article_count,
                   (ARRAY_AGG(trend ORDER BY calculated_at DESC))[1] AS trend
            FROM threat_scores
            WHERE LOWER(region) = LOWER(:region)
              AND calculated_at >= :cutoff
            GROUP BY day
            ORDER BY day ASC
        """),
        {"region": region, "cutoff": cutoff},
    ).fetchall()

    history = [
        {
            "date": r.day.isoformat(),
            "score": float(r.score),
            "article_count": int(r.article_count or 0),
            "trend": r.trend or "stable",
        }
        for r in rows
    ]

    return {
        "region": region,
        "days": days,
        "history": history,
        "total_points": len(history),
    }
