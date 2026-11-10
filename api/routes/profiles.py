"""
GET /api/profiles — Entity Profiles (Object Views)
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.schemas.provenance import ClaimStatus
from common.schemas.profiles import (
    ProfileHeader,
    ProfileFactOut,
    ProfileTimelineEvent,
    ProfileDetailOut,
)

router = APIRouter(prefix="/profiles", tags=["Entity Profiles"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("", response_model=List[ProfileHeader])
def list_profiles(
    entity_type: Optional[str] = Query(None, description="PERSON, ORGANISATION, LOCATION, EQUIPMENT"),
    ring: Optional[int] = Query(None, ge=1, le=4),
    q: Optional[str] = Query(None, description="Search profile name or alias"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """List established entity profiles (candidates with repeated cross-source coverage)."""
    # Seed default entities if table is empty
    from api.routes.graph import _ensure_seed_graph_if_empty
    _ensure_seed_graph_if_empty(db)

    where_clauses = ["is_profile = TRUE"]
    params: dict = {"limit": size, "offset": (page - 1) * size}

    if entity_type:
        where_clauses.append("entity_type = :entity_type")
        params["entity_type"] = entity_type.upper()
    if ring:
        where_clauses.append("primary_ring = :ring")
        params["ring"] = ring
    if q:
        where_clauses.append("name ILIKE :q")
        params["q"] = f"%{q}%"

    where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = db.execute(
        text(f"""
            SELECT id, name, entity_type, aliases, primary_ring, mention_count,
                   source_count, is_profile, description, first_seen_at, last_seen_at
            FROM entity_nodes
            {where_sql}
            ORDER BY mention_count DESC, id ASC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    return [
        ProfileHeader(
            id=r.id,
            name=r.name,
            entity_type=r.entity_type,
            aliases=r.aliases or [],
            primary_ring=r.primary_ring,
            mention_count=r.mention_count,
            source_count=r.source_count,
            is_profile=r.is_profile,
            description=r.description or f"Established {r.entity_type.lower()} profile with cross-source OSINT tracking.",
            first_seen_at=r.first_seen_at or datetime.now(timezone.utc),
            last_seen_at=r.last_seen_at or datetime.now(timezone.utc),
        )
        for r in rows
    ]


@router.get("/{profile_id}", response_model=ProfileDetailOut)
def get_profile_detail(profile_id: int, db=Depends(get_db)):
    """Full object view: header, aliases, attributed facts, timeline, associates, and locations."""
    node = db.execute(
        text("""
            SELECT id, name, entity_type, aliases, primary_ring, mention_count,
                   source_count, is_profile, description, first_seen_at, last_seen_at
            FROM entity_nodes
            WHERE id = :id
        """),
        {"id": profile_id},
    ).fetchone()

    if not node:
        raise HTTPException(status_code=404, detail="Entity profile not found")

    header = ProfileHeader(
        id=node.id,
        name=node.name,
        entity_type=node.entity_type,
        aliases=node.aliases or [],
        primary_ring=node.primary_ring,
        mention_count=node.mention_count,
        source_count=node.source_count,
        is_profile=node.is_profile,
        description=node.description or f"Attributed intelligence profile for {node.name}.",
        first_seen_at=node.first_seen_at or datetime.now(timezone.utc),
        last_seen_at=node.last_seen_at or datetime.now(timezone.utc),
    )

    # 1. Attributed facts from profile_facts
    fact_rows = db.execute(
        text("""
            SELECT id, fact, claim_status, article_id, source_name, confidence, created_at
            FROM profile_facts
            WHERE entity_id = :id
            ORDER BY created_at DESC
        """),
        {"id": profile_id},
    ).fetchall()

    facts = [
        ProfileFactOut(
            id=f.id,
            fact=f.fact,
            claim_status=ClaimStatus(f.claim_status) if f.claim_status in [c.value for c in ClaimStatus] else ClaimStatus.REPORTED,
            article_id=f.article_id,
            source_name=f.source_name or "Open Source Wire",
            confidence=f.confidence or 0.85,
            created_at=f.created_at or datetime.now(timezone.utc),
        )
        for f in fact_rows
    ]

    # If no explicitly seeded facts yet, derive from recent articles mentioning this entity
    if not facts:
        recent_articles = db.execute(
            text("""
                SELECT a.id, a.title, s.name AS source_name, a.published_at
                FROM articles a
                JOIN sources s ON s.id = a.source_id
                WHERE a.title ILIKE :q OR a.content ILIKE :q
                ORDER BY a.published_at DESC
                LIMIT 3
            """),
            {"q": f"%{node.name}%"},
        ).fetchall()

        facts = [
            ProfileFactOut(
                id=1000 + i,
                fact=f"Reported in public wire: {art.title}",
                claim_status=ClaimStatus.REPORTED,
                article_id=art.id,
                source_name=art.source_name,
                confidence=0.88,
                created_at=art.published_at or datetime.now(timezone.utc),
            )
            for i, art in enumerate(recent_articles)
        ]

    # 2. Associates from entity_links
    associate_rows = db.execute(
        text("""
            SELECT en.id, en.name, en.entity_type, el.link_type, el.confidence
            FROM entity_links el
            JOIN entity_nodes en ON (
                CASE WHEN el.source_node_id = :id THEN el.target_node_id = en.id
                     ELSE el.source_node_id = en.id END
            )
            WHERE el.source_node_id = :id OR el.target_node_id = :id
            ORDER BY el.confidence DESC
            LIMIT 15
        """),
        {"id": profile_id},
    ).fetchall()

    associates = [
        {
            "id": r.id,
            "name": r.name,
            "entity_type": r.entity_type,
            "relationship": r.link_type,
            "confidence": r.confidence,
        }
        for r in associate_rows
    ]

    # 3. Chronological timeline
    timeline_rows = db.execute(
        text("""
            SELECT a.id, a.title, a.published_at, s.name AS source_name,
                   aa.event_type, aa.threat_level
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
            WHERE a.title ILIKE :q OR a.content ILIKE :q
            ORDER BY a.published_at DESC
            LIMIT 10
        """),
        {"q": f"%{node.name}%"},
    ).fetchall()

    timeline = [
        ProfileTimelineEvent(
            date=t.published_at or datetime.now(timezone.utc),
            title=t.title,
            event_type=t.event_type or "general",
            threat_level=t.threat_level or 4,
            article_id=t.id,
            source_name=t.source_name,
        )
        for t in timeline_rows
    ]

    # 4. Associated Locations
    locations = [
        {"name": a["name"], "relationship": a["relationship"]}
        for a in associates
        if a["entity_type"] == "LOCATION"
    ]

    return ProfileDetailOut(
        header=header,
        facts=facts,
        timeline=timeline,
        associates=associates,
        locations=locations,
    )
