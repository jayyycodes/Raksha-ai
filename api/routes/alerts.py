"""
Alerts API routes.
Owner: Jay
Stage: Mid (Stage 2)

Endpoints:
    GET /api/alerts   → unread anomaly alerts
"""
from fastapi import APIRouter, Query
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
def list_alerts(
    unread_only: bool = Query(True),
    severity: str | None = None,
):
    """
    Anomaly alerts feed.

    TODO (Jay):
        1. Query alerts table
        2. Filter by is_read if unread_only
        3. Filter by severity if provided
        4. Sort by triggered_at descending
    """
    raise NotImplementedError("Alerts endpoint not yet implemented — Stage 2")
