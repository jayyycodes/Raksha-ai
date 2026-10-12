"""
Map API routes.
Owner: Jay
Stage: Mid (Stage 2)

Endpoints:
    GET /api/map   → geo-tagged incidents for Leaflet.js
"""
from fastapi import APIRouter, Query
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Map"])


@router.get("/map")
def get_map_data(
    days: int = Query(7, ge=1, le=90),
):
    """
    Geo-tagged incidents for Leaflet.js map overlay.

    TODO (Jay):
        1. Query articles with location entities
        2. Geocode locations → lat/lng (cache results)
        3. Include event_type, threat_level, source ring
        4. Group nearby incidents into clusters
    """
    raise NotImplementedError("Map endpoint not yet implemented — Stage 2")
