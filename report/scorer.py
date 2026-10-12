"""
Threat Scorer — calculates regional threat scores (1–10).
Owner: Ary
Stage: 3

Computes a weighted threat score per region based on:
    - Article volume (spike = higher threat)
    - Sentiment distribution (alarming articles weight more)
    - Event type severity (nuclear > diplomatic)
    - Source ring (Ring 2 adversary signals weight highest)
    - Trend direction (rising / stable / falling)

Stores results in threat_scores table.

Usage:
    from report.scorer import calculate_threat_scores
    scores = calculate_threat_scores()
    # [{"region": "LAC-Ladakh", "score": 7.2, "trend": "rising", "article_count": 14}, ...]
"""
from common.logger import get_logger

logger = get_logger(__name__)

# Regions to track
REGIONS = [
    "LAC-Ladakh",
    "LAC-Arunachal",
    "LoC-Kashmir",
    "Western-Border",
    "Indian-Ocean",
    "Northeast",
    "Internal-Security",
    "Cyber",
    "Global-Strategic",
]


def calculate_threat_scores(window_hours: int = 24) -> list[dict]:
    """
    Calculate threat scores for all regions based on recent articles.

    Args:
        window_hours: How many hours of data to analyze (default 24)

    Returns:
        List of {"region": str, "score": float, "trend": str, "article_count": int}

    TODO (Ary):
        1. Query articles + article_analysis from last N hours
        2. Group by region (from entities table — LOCATION → region mapping)
        3. Apply weighted scoring formula
        4. Compare with previous score to determine trend
        5. Store in threat_scores table
    """
    raise NotImplementedError("Threat scorer not yet implemented — Stage 3")
