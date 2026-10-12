"""
Threats API routes.
Owner: Jay
Stage: Mid (Stage 2)

Endpoints:
    GET /api/threats            → threat scores per region + trend
    GET /api/threats/{region}   → 30-day history for a region
"""
from fastapi import APIRouter
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Threats"])


@router.get("/threats")
def list_threats():
    """
    Current threat scores for all regions.

    TODO (Jay):
        1. Query latest threat_scores per region
        2. Include trend direction
        3. Sort by score descending
    """
    raise NotImplementedError("Threats endpoint not yet implemented — Stage 2")


@router.get("/threats/{region}")
def get_threat_history(region: str):
    """
    30-day threat score history for a specific region (for Recharts graph).

    TODO (Jay):
        1. Query threat_scores for region, last 30 days
        2. Return time series data
    """
    raise NotImplementedError("Threat history endpoint not yet implemented — Stage 2")
