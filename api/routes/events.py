"""
Events API routes.
Owner: Jay
Stage: Mid (Stage 2)

Endpoints:
    GET /api/events        → ongoing events list with article count
    GET /api/events/{id}   → event detail + full article timeline
"""
from fastapi import APIRouter
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Events"])


@router.get("/events")
def list_events():
    """
    All tracked events with article counts.

    TODO (Jay):
        1. Query events table, filter by status
        2. Include article_count, threat_level, region
        3. Sort by last_updated_at descending
    """
    raise NotImplementedError("Events endpoint not yet implemented — Stage 2")


@router.get("/events/{event_id}")
def get_event(event_id: int):
    """
    Event detail with full article timeline.

    TODO (Jay):
        1. Fetch event by ID
        2. Join event_articles → articles for timeline
        3. Include linked entities and threat trajectory
    """
    raise NotImplementedError("Event detail endpoint not yet implemented — Stage 2")
