"""
Test Suite: Stage 3 Solid — Cases, Evidence Pinning, and Investigation Dossiers
Owner: Jay (Lead & Platform) | Milestone: M9b
"""
from fastapi.testclient import TestClient
from api.main import app
from common.auth import create_access_token

client = TestClient(app)
analyst_token = create_access_token({"sub": "2", "email": "analyst@raksha.ai", "role": "analyst"})
auth_headers = {"Authorization": f"Bearer {analyst_token}"}


def test_list_cases_endpoint():
    """Verify listing cases and summary evidence counters."""
    resp = client.get("/api/cases", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "cases" in data
    assert "total" in data
    assert data["total"] >= 1
    sample = data["cases"][0]
    assert "title" in sample
    assert "status" in sample
    assert "evidence_count" in sample


def test_create_and_update_case():
    """Verify creating a new analytical case and updating priority/status."""
    create_payload = {
        "title": "Sir Creek Hydrographic & Border Posture Review",
        "description": "Cross-checking marshland border posts and hovercraft patrols along Gujarat-Sindh border.",
        "priority": "high",
        "classification": "restricted",
        "tags": ["Sir Creek", "Gujarat", "Sindh", "Coast Guard"],
    }
    create_resp = client.post("/api/cases", json=create_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    # Update case
    update_payload = {"status": "in_review", "priority": "critical"}
    update_resp = client.put(f"/api/cases/{case_id}", json=update_payload, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "in_review"
    assert update_resp.json()["priority"] == "critical"


def test_attach_evidence_and_add_note():
    """Verify attaching an article item and appending an analyst hypothesis."""
    # List cases to get an ID
    list_resp = client.get("/api/cases", headers=auth_headers)
    case_id = list_resp.json()["cases"][0]["id"]

    # Attach item
    item_payload = {
        "item_type": "entity",
        "item_id": "Western Theater Command",
        "title": "Adversary Operational Command",
        "analyst_notes": "Identified as primary operational node in western theatre.",
    }
    item_resp = client.post(f"/api/cases/{case_id}/items", json=item_payload, headers=auth_headers)
    assert item_resp.status_code == 200
    item_data = item_resp.json()
    assert item_data["title"] == "Adversary Operational Command"

    # Add Note
    note_payload = {
        "note_text": "Satellite pass confirms enhanced runway reinforcement.",
        "hypothesis": "Possible rotation of multi-role fighter squadron.",
    }
    note_resp = client.post(f"/api/cases/{case_id}/notes", json=note_payload, headers=auth_headers)
    assert note_resp.status_code == 200
    assert "hypothesis" in note_resp.json()


def test_export_case_dossier():
    """Verify exporting structured case dossier bundle."""
    list_resp = client.get("/api/cases", headers=auth_headers)
    case_id = list_resp.json()["cases"][0]["id"]

    export_resp = client.get(f"/api/cases/{case_id}/export", headers=auth_headers)
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert data["format"] == "raksha_intelligence_dossier_v1"
    assert "dossier" in data
    assert "evidence_items" in data["dossier"]
    assert "notes" in data["dossier"]
