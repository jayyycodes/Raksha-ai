"""
SitRep API routes.
Owner: Jay
Stage: Mid (Stage 2)

Endpoints:
    GET /api/sitrep/today    → today's AI-generated report
    GET /api/sitrep/{date}   → historical SitRep by date
"""
from fastapi import APIRouter
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["SitRep"])


@router.get("/sitrep/today")
def get_today_sitrep():
    """
    Today's SitRep.

    TODO (Jay):
        1. Query sitreps WHERE report_date = today
        2. Return content + top_threats + article_count
        3. Return 404 if not yet generated
    """
    raise NotImplementedError("SitRep endpoint not yet implemented — Stage 2")


@router.get("/sitrep/{date}")
def get_sitrep_by_date(date: str):
    """
    Historical SitRep by date (YYYY-MM-DD).

    TODO (Jay):
        1. Parse and validate date
        2. Query sitreps WHERE report_date = date
        3. Return 404 if not found
    """
    raise NotImplementedError("Historical SitRep endpoint not yet implemented — Stage 2")
