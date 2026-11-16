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
    # Normalize Query objects when invoked directly in tests/scripts
    if not isinstance(ring, int):
        ring = None
    if not isinstance(event_type, str):
        event_type = None
    if not isinstance(date_from, str):
        date_from = None
    if not isinstance(page, int):
        page = 1
    if not isinstance(size, int):
        size = 20

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
            SELECT a.id, a.title, a.url, a.content, a.language, a.published_at, a.is_processed,
                   s.name AS source_name, s.ring,
                   aa.summary, aa.positive_impact_in, aa.negative_impact_in, aa.strategic_implications,
                   aa.event_type, aa.sentiment, aa.threat_level, aa.confidence,
                   aa.translated_text, aa.method, aa.model_version
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
                   aa.summary, aa.positive_impact_in, aa.negative_impact_in, aa.strategic_implications,
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


# ── Stage 3 Disinformation Scoring (Milestone M9) ──────────────────────

@router.get("/{article_id}/disinformation")
def get_article_disinformation_score(article_id: int, db=Depends(get_db)):
    """
    Evaluates cross-source narrative divergence and disinformation risk (Stage 3).
    Cross-checks the article against related contemporaneous articles across Rings 1–4.
    """
    from agents.corroboration.disinformation import DisinformationScorer

    target = db.execute(
        text("""
            SELECT a.id, a.title, a.content, s.name AS source_name, s.ring
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            WHERE a.id = :id
        """),
        {"id": article_id},
    ).fetchone()

    if not target:
        raise HTTPException(status_code=404, detail="Article not found")

    # Fetch up to 10 temporally proximate articles for cross-source comparison
    peers = db.execute(
        text("""
            SELECT a.id, a.title, a.content, s.name AS source_name, s.ring
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            WHERE a.id != :id
            ORDER BY a.published_at DESC
            LIMIT 10
        """),
        {"id": article_id},
    ).fetchall()

    cluster = [dict(target._mapping)] + [dict(p._mapping) for p in peers]
    scorer = DisinformationScorer()
    return scorer.evaluate_cluster(cluster)
