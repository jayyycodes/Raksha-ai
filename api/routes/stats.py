"""
Stats API routes.
Owner: Jay
Stage: MVP

Endpoints:
    GET /api/stats   → dashboard summary statistics
"""
from fastapi import APIRouter
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Stats"])


@router.get("/stats")
def get_stats():
    """
    Dashboard summary: article counts, per-source breakdown, last scrape time.

    TODO (Jay):
        1. Total articles, articles today, articles this week
        2. Per-ring breakdown
        3. Per-source article counts
        4. Last successful scrape timestamp
        5. Processed vs unprocessed ratio
    """
    raise NotImplementedError("Stats endpoint not yet implemented")
