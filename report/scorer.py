"""
Threat Scorer — calculates regional threat scores (1–10).
Owner: Ary / Jay (Lead)
Stage: 2 (Mid)

Computes a weighted threat score per region via ThreatScoringAgent and stores
time-series snapshots in `threat_scores` for the 30-day Recharts timeline.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import text

from agents.scoring.regional_scorer import ThreatScoringAgent
from common.constants import DEFENCE_REGIONS
from common.db import get_db
from common.logger import get_logger

logger = get_logger(__name__)

REGIONS = list(DEFENCE_REGIONS)


def calculate_threat_scores(window_hours: int = 24) -> list[dict]:
    """
    Calculate threat scores for all regions based on recent articles and store
    updated regional snapshots in the `threat_scores` table.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    scorer = ThreatScoringAgent()

    with get_db() as db:
        rows = db.execute(
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

        # Fallback to most recent corpus if narrow window has zero articles (e.g. cold startup)
        if not rows:
            rows = db.execute(
                text("""
                    SELECT a.id, a.title, a.content, s.ring,
                           COALESCE(aa.event_type, 'general') AS event_type,
                           COALESCE(aa.sentiment, 'neutral') AS sentiment,
                           COALESCE(aa.threat_level, 2) AS threat_level
                    FROM articles a
                    LEFT JOIN sources s ON s.id = a.source_id
                    LEFT JOIN article_analysis aa ON aa.article_id = a.id
                    ORDER BY a.published_at DESC
                    LIMIT 200
                """)
            ).mappings().all()

        articles = [dict(r) for r in rows]

        # Retrieve previous latest score per region for trend comparison
        prev_rows = db.execute(
            text("""
                SELECT DISTINCT ON (region) region, score
                FROM threat_scores
                ORDER BY region, calculated_at DESC
            """)
        ).fetchall()
        previous_scores: Dict[str, float] = {r.region: float(r.score) for r in prev_rows}

        scored = scorer.calculate_all_regions(articles, previous_scores=previous_scores)

        now_utc = datetime.now(timezone.utc)
        output: List[dict] = []
        for s in scored:
            db.execute(
                text("""
                    INSERT INTO threat_scores (region, score, trend, article_count, calculated_at)
                    VALUES (:region, :score, :trend, :article_count, :calculated_at)
                """),
                {
                    "region": s.region,
                    "score": float(s.score),
                    "trend": s.trend,
                    "article_count": int(s.article_count),
                    "calculated_at": now_utc,
                },
            )
            output.append(
                {
                    "region": s.region,
                    "score": float(s.score),
                    "trend": s.trend,
                    "article_count": int(s.article_count),
                }
            )

    logger.info(f"Threat Scorer: stored {len(output)} regional threat scores.")
    return output
