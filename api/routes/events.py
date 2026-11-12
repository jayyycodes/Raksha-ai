"""
Events API routes — Multi-month Event Threading & Timelines.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)

Endpoints:
    GET /api/events        -> ongoing events list with article count
    GET /api/events/{id}   -> event detail + full article timeline & provenance
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["Events & Threading"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def list_events(
    status: Optional[str] = Query(None, description="Filter by event status (ongoing, resolved, monitoring)"),
    region: Optional[str] = Query(None, description="Filter by strategic theatre/region"),
    event_type: Optional[str] = Query(None, description="Filter by event category"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """All tracked event threads sorted by most recently updated."""
    where_clauses = []
    params: dict = {"limit": limit}

    if status and status.lower() != "all":
        where_clauses.append("e.status = :status")
        params["status"] = status.lower()
    if region and region.lower() != "all":
        where_clauses.append("e.region ILIKE :region")
        params["region"] = f"%{region}%"
    if event_type and event_type.lower() != "all":
        where_clauses.append("e.event_type = :etype")
        params["etype"] = event_type.lower()

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = db.execute(
        text(f"""
            SELECT e.id, e.title, e.region, e.event_type, e.status,
                   COALESCE(e.threat_level, 0.0) AS threat_level,
                   e.first_seen_at, e.last_updated_at,
                   GREATEST(COALESCE(e.article_count, 0), COUNT(ea.article_id)) AS article_count,
                   e.summary
            FROM events e
            LEFT JOIN event_articles ea ON ea.event_id = e.id
            {where_sql}
            GROUP BY e.id
            ORDER BY e.last_updated_at DESC, e.threat_level DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    events = [
        {
            "id": r.id,
            "title": r.title,
            "region": r.region or "Multi-Region",
            "event_type": r.event_type or "general",
            "status": r.status or "ongoing",
            "threat_level": float(r.threat_level or 0.0),
            "first_seen_at": r.first_seen_at,
            "last_updated_at": r.last_updated_at,
            "article_count": int(r.article_count or 0),
            "summary": r.summary or r.title,
        }
        for r in rows
    ]
    return {"events": events, "total": len(events)}


@router.get("/{event_id}")
def get_event_detail(event_id: int, db=Depends(get_db)):
    """Event detail with chronological article timeline, entities, and link provenance."""
    ev = db.execute(
        text("""
            SELECT id, title, region, event_type, status, threat_level,
                   first_seen_at, last_updated_at, article_count, summary
            FROM events
            WHERE id = :eid
        """),
        {"eid": event_id},
    ).fetchone()

    if not ev:
        raise HTTPException(status_code=404, detail="Event thread not found")

    # Timeline articles linked to this event
    art_rows = db.execute(
        text("""
            SELECT a.id, a.title, a.url, a.published_at,
                   s.name AS source_name, s.ring,
                   COALESCE(aa.threat_level, 4) AS threat_level,
                   COALESCE(aa.sentiment, 'neutral') AS sentiment,
                   ea.linked_at, ea.link_method, ea.confidence, ea.is_seed,
                   ea.explanation
            FROM event_articles ea
            JOIN articles a ON a.id = ea.article_id
            LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            WHERE ea.event_id = :eid
            ORDER BY a.published_at ASC
        """),
        {"eid": event_id},
    ).fetchall()

    timeline = [
        {
            "article_id": r.id,
            "title": r.title,
            "url": r.url,
            "published_at": r.published_at,
            "source_name": r.source_name or "Open Source Wire",
            "ring": r.ring or 1,
            "threat_level": int(r.threat_level or 4),
            "sentiment": r.sentiment or "neutral",
            "link_method": r.link_method or "embedding_cosine",
            "confidence": round(float(r.confidence or 0.85), 3),
            "is_seed": bool(r.is_seed),
            "explanation": r.explanation or "Linked via semantic similarity and shared ontological entities.",
        }
        for r in art_rows
    ]

    # Collect linked entities across articles in this thread
    article_ids = [r.id for r in art_rows]
    linked_entities = []
    if article_ids:
        ent_rows = db.execute(
            text("""
                SELECT e.entity_type, e.entity_value, COUNT(*) AS mentions,
                       MAX(en.id) AS profile_id
                FROM entities e
                LEFT JOIN entity_nodes en ON LOWER(en.name) = LOWER(e.entity_value)
                WHERE e.article_id = ANY(:aids)
                GROUP BY e.entity_type, e.entity_value
                ORDER BY mentions DESC
                LIMIT 20
            """),
            {"aids": article_ids},
        ).fetchall()
        linked_entities = [
            {
                "entity_type": r.entity_type,
                "name": r.entity_value,
                "mentions": int(r.mentions),
                "profile_id": r.profile_id,
            }
            for r in ent_rows
        ]

    # Threat trajectory points ordered chronologically
    threat_trajectory = [
        {
            "date": item["published_at"].strftime("%Y-%m-%d") if item["published_at"] else "",
            "threat_level": item["threat_level"],
            "title": item["title"][:60],
        }
        for item in timeline
    ]

    return {
        "event": {
            "id": ev.id,
            "title": ev.title,
            "region": ev.region or "Multi-Region",
            "event_type": ev.event_type or "general",
            "status": ev.status or "ongoing",
            "threat_level": float(ev.threat_level or 0.0),
            "first_seen_at": ev.first_seen_at,
            "last_updated_at": ev.last_updated_at,
            "article_count": max(int(ev.article_count or 0), len(timeline)),
            "summary": ev.summary or ev.title,
        },
        "timeline": timeline,
        "entities": linked_entities,
        "threat_trajectory": threat_trajectory,
    }
