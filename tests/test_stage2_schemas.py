"""
Tests for Stage 2 Ontology Schemas & Database Migration 003.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from common.db import get_db
from common.schemas import (
    GraphNode,
    GraphEdge,
    GraphResponse,
    MapIncident,
    MapResponse,
    MergeSuggestionOut,
    ReviewActionIn,
    ReviewQueueResponse,
    ProfileHeader,
    ProfileDetailOut,
    ProfileTimelineEvent,
)


def test_graph_schemas():
    node = GraphNode(
        id="node_1",
        label="Indian Army",
        entity_type="ORGANISATION",
        primary_ring=1,
        mention_count=45,
        source_count=5,
        is_profile=True,
    )
    edge = GraphEdge(
        id="edge_1_2",
        source="node_1",
        target="node_2",
        link_type="INVOLVES",
        confidence=0.95,
    )
    resp = GraphResponse(
        nodes=[node],
        edges=[edge],
        total_nodes=1,
        total_edges=1,
    )
    assert resp.total_nodes == 1
    assert resp.nodes[0].label == "Indian Army"
    assert resp.edges[0].link_type == "INVOLVES"


def test_map_schemas():
    incident = MapIncident(
        id=101,
        title="Disengagement monitoring along Line of Actual Control",
        event_type="border_incident",
        threat_level=4,
        threat_category="medium",
        ring=1,
        latitude=34.25,
        longitude=78.33,
        location_name="Eastern Ladakh",
        region="Ladakh",
    )
    resp = MapResponse(incidents=[incident], total=1)
    assert resp.total == 1
    assert resp.incidents[0].location_name == "Eastern Ladakh"


def test_review_schemas():
    suggestion = MergeSuggestionOut(
        id=1,
        source_node_id=10,
        source_name="JeM",
        target_node_id=11,
        target_name="Jaish-e-Mohammed",
        entity_type="ORGANISATION",
        similarity_score=0.92,
        reason="Acronym alias match with high co-occurrence",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    action = ReviewActionIn(action="accept", analyst_name="jay_analyst")
    assert suggestion.similarity_score == 0.92
    assert action.action == "accept"


def test_profile_schemas():
    header = ProfileHeader(
        id=1,
        name="General Upendra Dwivedi",
        entity_type="PERSON",
        aliases=["COAS"],
        primary_ring=1,
        mention_count=12,
        source_count=4,
        is_profile=True,
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    profile = ProfileDetailOut(
        header=header,
        facts=[],
        timeline=[],
        associates=[],
        locations=[],
    )
    assert profile.header.is_profile is True
    assert "COAS" in profile.header.aliases


def test_db_migration_003_tables_exist():
    with get_db() as db:
        res = db.execute(
            text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('entity_nodes', 'entity_links', 'merge_suggestions', 'profile_facts', 'watchlists')
            """)
        ).fetchall()
        tables = set(r[0] for r in res)
        assert "entity_nodes" in tables
        assert "entity_links" in tables
        assert "merge_suggestions" in tables
        assert "profile_facts" in tables
        assert "watchlists" in tables

