"""
Integration tests for Stage 2 Intelligence & Graph API Endpoints.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_graph_endpoint(client):
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["total_nodes"] > 0
    assert data["total_edges"] > 0

    first_node = data["nodes"][0]
    assert "id" in first_node
    assert "label" in first_node
    assert "entity_type" in first_node
    assert "primary_ring" in first_node


def test_graph_filtering(client):
    # Filter by entity_type
    res = client.get("/api/graph?entity_type=LOCATION")
    assert res.status_code == 200
    data = res.json()
    for n in data["nodes"]:
        assert n["entity_type"] == "LOCATION"


def test_map_incidents_endpoint(client):
    res = client.get("/api/map/incidents?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "incidents" in data
    assert data["total"] > 0
    assert len(data["incidents"]) <= 10

    first = data["incidents"][0]
    assert "latitude" in first
    assert "longitude" in first
    assert "location_name" in first
    assert "threat_level" in first
    assert 1 <= first["threat_level"] <= 10


def test_profiles_list_and_detail(client):
    res = client.get("/api/profiles")
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) > 0

    profile_id = profiles[0]["id"]
    detail_res = client.get(f"/api/profiles/{profile_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "header" in detail
    assert "facts" in detail
    assert "associates" in detail
    assert "timeline" in detail
    assert detail["header"]["id"] == profile_id


def test_review_queue_and_action(client):
    res = client.get("/api/review")
    assert res.status_code == 200
    data = res.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0

    sug_id = data["suggestions"][0]["id"]
    action_res = client.post(
        f"/api/review/{sug_id}/action",
        json={"action": "accept", "analyst_name": "lead_analyst", "notes": "Verified verified alias"}
    )
    assert action_res.status_code == 200
    assert action_res.json()["status"] == "accepted"


def test_sitrep_latest(client):
    res = client.get("/api/sitreps/latest")
    assert res.status_code == 200
    data = res.json()
    assert "report_date" in data
    assert "executive_summary" in data
    assert "theatre_assessments" in data
    assert "citations" in data


def test_unified_search(client):
    res = client.get("/api/search?q=Army")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "Army"
    assert "articles" in data
    assert "entities" in data
