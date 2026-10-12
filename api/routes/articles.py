"""
Articles API routes.
Owner: Jay
Stage: MVP

Endpoints:
    GET /api/articles        → paginated article list
    GET /api/articles/{id}   → article detail with analysis
"""
from fastapi import APIRouter, Query
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Articles"])


@router.get("/articles")
def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    ring: int | None = Query(None, ge=1, le=4),
    event_type: str | None = None,
):
    """
    Paginated article list with optional filters.

    TODO (Jay):
        1. Query articles table with pagination
        2. Join with sources for ring info
        3. Join with article_analysis for event_type filter
        4. Return total count for frontend pagination
    """
    raise NotImplementedError("Articles endpoint not yet implemented")


@router.get("/articles/{article_id}")
def get_article(article_id: int):
    """
    Article detail with NLP analysis and entities.

    TODO (Jay):
        1. Fetch article by ID
        2. Join article_analysis + entities
        3. Include linked event info if any
    """
    raise NotImplementedError("Article detail endpoint not yet implemented")
