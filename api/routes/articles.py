"""
GET /api/articles  — paginated article list
GET /api/articles/{id} — article detail with analysis and provenance
Owner: Jay | Stage: 1 MVP
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from common.db import get_db as _get_db
from contextlib import contextmanager

router = APIRouter(prefix="/articles", tags=["Articles"])


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session."""
    with _get_db() as db:
        yield db


@router.get("")
def list_articles(
    ring: Optional[int] = Query(None, ge=1, le=4, description="Filter by source ring"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    date_from: Optional[str] = Query(None, description="ISO date e.g. 2026-10-01"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """Paginated article feed with optional filters."""
    filters = []
    params: dict = {"limit": size, "offset": (page - 1) * size}

    if ring is not None:
        filters.append("s.ring = :ring")
        params["ring"] = ring
    if event_type:
        filters.append("aa.event_type = :event_type")
        params["event_type"] = event_type
    if date_from:
        filters.append("a.published_at >= :date_from")
        params["date_from"] = date_from

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    rows = db.execute(
        text(f"""
            SELECT a.id, a.title, a.url, a.language, a.published_at, a.is_processed,
                   s.name AS source_name, s.ring,
                   aa.event_type, aa.sentiment, aa.threat_level, aa.confidence,
                   aa.method, aa.model_version
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            {where}
            ORDER BY a.published_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    count_row = db.execute(
        text(f"""
            SELECT COUNT(*) FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            {where}
        """),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).scalar()

    return {
        "total": count_row,
        "page": page,
        "size": size,
        "articles": [dict(r._mapping) for r in rows],
    }


@router.get("/{article_id}")
def get_article(article_id: int, db=Depends(get_db)):
    """Article detail with NLP analysis and provenance."""
    row = db.execute(
        text("""
            SELECT a.id, a.title, a.url, a.content, a.language, a.published_at, a.is_processed,
                   a.url_hash,
                   s.name AS source_name, s.ring, s.country,
                   aa.event_type, aa.sentiment, aa.threat_level, aa.confidence,
                   aa.translated_text, aa.method, aa.model_version, aa.source_ids,
                   aa.created_at AS analyzed_at
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            WHERE a.id = :id
        """),
        {"id": article_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    return dict(row._mapping)
