"""
Unified Search API — Multi-modal search across articles and entity profiles.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from common.db import get_db as _get_db

router = APIRouter(prefix="/search", tags=["Unified Search"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def unified_search(
    q: str = Query(..., min_length=2, description="Search term for entities, articles, or locations"),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """Unified search matching both article text and entity ontology nodes."""
    term = f"%{q}%"

    # 1. Search Articles
    art_rows = db.execute(
        text("""
            SELECT a.id, a.title, a.url, a.published_at, s.name AS source_name, s.ring,
                   aa.event_type, aa.threat_level
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            WHERE a.title ILIKE :q OR a.content ILIKE :q
            ORDER BY a.published_at DESC
            LIMIT :limit
        """),
        {"q": term, "limit": limit},
    ).fetchall()

    articles = [
        {
            "id": r.id,
            "title": r.title,
            "url": r.url,
            "published_at": r.published_at,
            "source_name": r.source_name,
            "ring": r.ring,
            "event_type": r.event_type or "general",
            "threat_level": r.threat_level or 4,
        }
        for r in art_rows
    ]

    # 2. Search Entity Nodes
    ent_rows = db.execute(
        text("""
            SELECT id, name, entity_type, primary_ring, mention_count, is_profile
            FROM entity_nodes
            WHERE name ILIKE :q OR :raw_q = ANY(aliases)
            ORDER BY mention_count DESC
            LIMIT :limit
        """),
        {"q": term, "raw_q": q, "limit": limit},
    ).fetchall()

    entities = [
        {
            "id": r.id,
            "name": r.name,
            "entity_type": r.entity_type,
            "primary_ring": r.primary_ring,
            "mention_count": r.mention_count,
            "is_profile": r.is_profile,
        }
        for r in ent_rows
    ]

    return {
        "query": q,
        "total_matches": len(articles) + len(entities),
        "articles": articles,
        "entities": entities,
    }
