"""
Unified Search API — Multi-modal search across articles, entities, and event threads.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Unified Search"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def unified_search(
    q: str = Query(..., min_length=2, description="Search term for entities, articles, events, or locations"),
    semantic: bool = Query(False, description="Include pgvector semantic similarity results when model is loaded"),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """Unified search matching articles, entity ontology nodes, and event threads."""
    term = f"%{q}%"

    # 1. Search Articles (keyword match)
    art_rows = db.execute(
        text("""
            SELECT a.id, a.title, a.url, a.published_at, s.name AS source_name, s.ring,
                   aa.event_type, aa.threat_level, 'keyword' AS match_mode
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
            "match_mode": r.match_mode,
        }
        for r in art_rows
    ]

    # Optional pgvector semantic similarity augmentation
    if semantic:
        try:
            from engine.embeddings import generate_embedding

            q_vec = generate_embedding(q)
            vec_literal = "[" + ",".join(f"{x:.6f}" for x in q_vec) + "]"
            sem_rows = db.execute(
                text("""
                    SELECT a.id, a.title, a.url, a.published_at, s.name AS source_name, s.ring,
                           aa.event_type, aa.threat_level,
                           (1 - (ae.embedding <=> CAST(:vec AS vector))) AS similarity
                    FROM article_embeddings ae
                    JOIN articles a ON a.id = ae.article_id
                    JOIN sources s ON s.id = a.source_id
                    LEFT JOIN article_analysis aa ON aa.article_id = a.id
                    ORDER BY ae.embedding <=> CAST(:vec AS vector) ASC
                    LIMIT :limit
                """),
                {"vec": vec_literal, "limit": limit},
            ).fetchall()

            seen_ids = {a["id"] for a in articles}
            for r in sem_rows:
                if r.id not in seen_ids and float(r.similarity or 0.0) >= 0.35:
                    articles.append(
                        {
                            "id": r.id,
                            "title": r.title,
                            "url": r.url,
                            "published_at": r.published_at,
                            "source_name": r.source_name,
                            "ring": r.ring,
                            "event_type": r.event_type or "general",
                            "threat_level": r.threat_level or 4,
                            "match_mode": f"semantic ({float(r.similarity):.2f})",
                        }
                    )
                    seen_ids.add(r.id)
        except Exception as exc:
            logger.debug("Semantic vector search skipped (%s); returning keyword results.", exc)

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

    # 3. Search Ongoing Events
    evt_rows = db.execute(
        text("""
            SELECT id, title, region, event_type, status,
                   COALESCE(threat_level, 0.0) AS threat_level,
                   article_count, last_updated_at
            FROM events
            WHERE title ILIKE :q OR summary ILIKE :q OR region ILIKE :q
            ORDER BY last_updated_at DESC
            LIMIT :limit
        """),
        {"q": term, "limit": limit},
    ).fetchall()

    events = [
        {
            "id": r.id,
            "title": r.title,
            "region": r.region or "Multi-Region",
            "event_type": r.event_type or "general",
            "status": r.status or "ongoing",
            "threat_level": float(r.threat_level or 0.0),
            "article_count": int(r.article_count or 0),
            "last_updated_at": r.last_updated_at,
        }
        for r in evt_rows
    ]

    return {
        "query": q,
        "total_matches": len(articles) + len(entities) + len(events),
        "articles": articles,
        "entities": entities,
        "events": events,
    }
