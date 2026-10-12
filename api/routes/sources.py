"""
Sources API routes.
Owner: Jay
Stage: MVP

Endpoints:
    GET /api/sources   → all sources with last scraped time and status
"""
from fastapi import APIRouter
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Sources"])


@router.get("/sources")
def list_sources():
    """
    All monitored sources with status info.

    TODO (Jay):
        1. Query sources table
        2. Include: name, url, ring, country, is_active, last_scraped_at
        3. Include article count per source (today and total)
    """
    raise NotImplementedError("Sources endpoint not yet implemented")
