"""
GET /api/graph — Cytoscape-compatible Entity Knowledge Graph
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.schemas.graph import GraphNode, GraphEdge, GraphResponse

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


def get_db():
    with _get_db() as db:
        yield db


# Fallback strategic seed entities for initial cold-start before full batch NER completes
INITIAL_STRATEGIC_ENTITIES = [
    {"name": "Indian Army", "type": "ORGANISATION", "ring": 1, "mentions": 48, "sources": 6, "is_profile": True, "aliases": ["IA", "Indian Army", "Army"]},
    {"name": "Indian Air Force", "type": "ORGANISATION", "ring": 1, "mentions": 32, "sources": 5, "is_profile": True, "aliases": ["IAF", "Indian Air Force", "Air Force"]},
    {"name": "DRDO", "type": "ORGANISATION", "ring": 1, "mentions": 28, "sources": 4, "is_profile": True, "aliases": ["DRDO", "Defence Research and Development Organisation"]},
    {"name": "General Upendra Dwivedi", "type": "PERSON", "ring": 1, "mentions": 14, "sources": 4, "is_profile": True, "aliases": ["Upendra Dwivedi", "Gen Upendra Dwivedi", "COAS", "Army Chief"]},
    {"name": "Eastern Ladakh", "type": "LOCATION", "ring": 1, "mentions": 65, "sources": 7, "is_profile": True, "aliases": ["Eastern Ladakh", "Ladakh", "Galwan", "Pangong", "Demchok", "Depsang"]},
    {"name": "Line of Actual Control", "type": "LOCATION", "ring": 1, "mentions": 78, "sources": 7, "is_profile": True, "aliases": ["LAC", "Line of Actual Control", "Sino-Indian LAC", "LAC border"]},
    {"name": "PLA Ground Force", "type": "ORGANISATION", "ring": 2, "mentions": 52, "sources": 5, "is_profile": True, "aliases": ["PLA", "PLA Ground Force", "People's Liberation Army"]},
    {"name": "Western Theater Command", "type": "ORGANISATION", "ring": 2, "mentions": 29, "sources": 4, "is_profile": True, "aliases": ["WTC", "Western Theater Command", "Western Theatre Command"]},
    {"name": "Rawalpindi GHQ", "type": "ORGANISATION", "ring": 2, "mentions": 24, "sources": 3, "is_profile": True, "aliases": ["GHQ", "Rawalpindi", "Pakistan Army"]},
    {"name": "Depsang Plains", "type": "LOCATION", "ring": 1, "mentions": 38, "sources": 5, "is_profile": True, "aliases": ["Depsang", "Depsang Plains", "Y-junction"]},
    {"name": "Demchok", "type": "LOCATION", "ring": 1, "mentions": 35, "sources": 5, "is_profile": True, "aliases": ["Demchok", "Demchok sector"]},
    {"name": "Rafale", "type": "EQUIPMENT", "ring": 4, "mentions": 18, "sources": 3, "is_profile": False, "aliases": ["Rafale", "Dassault Rafale", "IAF Rafale"]},
    {"name": "S-400 Triumf", "type": "EQUIPMENT", "ring": 4, "mentions": 15, "sources": 3, "is_profile": False, "aliases": ["S-400", "S-400 Triumf", "Air Defence System"]},
]

INITIAL_STRATEGIC_LINKS = [
    ("Indian Army", "Eastern Ladakh", "LOCATED_IN", 0.95),
    ("Indian Army", "Line of Actual Control", "INVOLVES", 0.98),
    ("PLA Ground Force", "Line of Actual Control", "INVOLVES", 0.98),
    ("Western Theater Command", "PLA Ground Force", "PART_OF_EVENT", 0.92),
    ("Eastern Ladakh", "Depsang Plains", "LOCATED_IN", 0.90),
    ("Eastern Ladakh", "Demchok", "LOCATED_IN", 0.90),
    ("General Upendra Dwivedi", "Indian Army", "ASSOCIATED_WITH", 0.99),
    ("General Upendra Dwivedi", "COAS", "TITLE_OF", 0.99),
    ("Indian Air Force", "Rafale", "EQUIPPED_WITH", 0.94),
    ("Indian Air Force", "S-400 Triumf", "EQUIPPED_WITH", 0.98),
    ("Indian Air Force", "IAF", "ALIAS_OF", 0.99),
    ("DRDO", "Indian Army", "ASSOCIATED_WITH", 0.88),
    ("Western Theater Command", "WTC", "ALIAS_OF", 0.99),
    ("Rawalpindi GHQ", "Pakistan Air Force", "COMMANDS", 0.92),
    ("Pakistan Air Force", "PAF", "ALIAS_OF", 0.99),
    ("Rawalpindi GHQ", "Jaish-e-Mohammed", "INVOLVES", 0.85),
    ("Jaish-e-Mohammed", "JeM", "ALIAS_OF", 0.99),
    ("Rawalpindi GHQ", "Lashkar-e-Taiba", "INVOLVES", 0.86),
    ("Lashkar-e-Taiba", "LeT", "ALIAS_OF", 0.99),
    ("PLA Ground Force", "Western Theater Command", "REPORTS_TO", 0.95),
]


def _ensure_seed_graph_if_empty(db):
    """Seed key strategic entities and ensure all inter-entity links are present."""
    count = db.execute(text("SELECT COUNT(*) FROM entity_nodes")).scalar()
    if count == 0:
        for ent in INITIAL_STRATEGIC_ENTITIES:
            db.execute(
                text("""
                    INSERT INTO entity_nodes (name, entity_type, primary_ring, mention_count, source_count, is_profile, aliases)
                    VALUES (:name, :type, :ring, :mentions, :sources, :is_profile, :aliases)
                    ON CONFLICT (name, entity_type) DO NOTHING
                """),
                ent,
            )

    # Always ensure strategic links exist so the knowledge graph is richly connected
    for src_name, tgt_name, ltype, conf in INITIAL_STRATEGIC_LINKS:
        db.execute(
            text("""
                INSERT INTO entity_links (source_node_id, target_node_id, link_type, confidence)
                SELECT s.id, t.id, :ltype, :conf
                FROM entity_nodes s, entity_nodes t
                WHERE s.name = :src AND t.name = :tgt
                  AND NOT EXISTS (
                      SELECT 1 FROM entity_links el
                      WHERE el.source_node_id = s.id AND el.target_node_id = t.id AND el.link_type = :ltype
                  )
            """),
            {"src": src_name, "tgt": tgt_name, "ltype": ltype, "conf": conf},
        )
    
    # Enrich aliases for existing nodes if empty
    for ent in INITIAL_STRATEGIC_ENTITIES:
        db.execute(
            text("""
                UPDATE entity_nodes
                SET aliases = :aliases
                WHERE name = :name AND (aliases IS NULL OR array_length(aliases, 1) IS NULL)
            """),
            {"name": ent["name"], "aliases": ent["aliases"]},
        )
    db.commit()


@router.get("", response_model=GraphResponse)
def get_entity_graph(
    ring: Optional[int] = Query(None, ge=1, le=4, description="Filter nodes by primary security ring"),
    entity_type: Optional[str] = Query(None, description="PERSON, ORGANISATION, LOCATION, EQUIPMENT, EVENT"),
    q: Optional[str] = Query(None, description="Search node name or alias"),
    limit: int = Query(100, ge=5, le=500),
    db=Depends(get_db),
):
    """Interactive entity network graph for Cytoscape.js exploration."""
    _ensure_seed_graph_if_empty(db)

    where_clauses = []
    params: dict = {"limit": limit}

    if ring is not None:
        where_clauses.append("primary_ring = :ring")
        params["ring"] = ring
    if entity_type:
        where_clauses.append("entity_type = :entity_type")
        params["entity_type"] = entity_type.upper()
    if q:
        where_clauses.append("name ILIKE :q")
        params["q"] = f"%{q}%"

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    node_rows = db.execute(
        text(f"""
            SELECT id, name, entity_type, primary_ring, mention_count, source_count,
                   is_profile, metadata
            FROM entity_nodes
            {where_sql}
            ORDER BY mention_count DESC, id ASC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    if not node_rows:
        return GraphResponse(nodes=[], edges=[], total_nodes=0, total_edges=0)

    nodes = [
        GraphNode(
            id=f"node_{r.id}",
            label=r.name,
            entity_type=r.entity_type,
            primary_ring=r.primary_ring,
            mention_count=r.mention_count,
            source_count=r.source_count,
            is_profile=r.is_profile,
            metadata=r.metadata or {},
        )
        for r in node_rows
    ]

    node_id_map = {r.id: f"node_{r.id}" for r in node_rows}
    allowed_ids = list(node_id_map.keys())

    # Fetch connecting edges
    edge_rows = db.execute(
        text("""
            SELECT id, source_node_id, target_node_id, link_type, confidence, article_id, method
            FROM entity_links
            WHERE source_node_id = ANY(:ids) AND target_node_id = ANY(:ids)
            ORDER BY confidence DESC
            LIMIT 500
        """),
        {"ids": allowed_ids},
    ).fetchall()

    edges = [
        GraphEdge(
            id=f"edge_{r.id}",
            source=node_id_map[r.source_node_id],
            target=node_id_map[r.target_node_id],
            link_type=r.link_type,
            confidence=r.confidence,
            article_id=r.article_id,
            method=r.method or "ner_co_occurrence",
        )
        for r in edge_rows
        if r.source_node_id in node_id_map and r.target_node_id in node_id_map
    ]

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )

