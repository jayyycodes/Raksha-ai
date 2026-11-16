"""
Tests for DPDP Act Correction & Takedown Requests
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from common.auth import create_access_token

client = TestClient(app)

ANALYST_TOKEN = create_access_token(
    data={"sub": "2", "email": "analyst@raksha.ai", "role": "analyst", "workspace_id": 1}
)


def test_submit_correction_success():
    payload = {
        "target_type": "entity",
        "target_id": "1",
        "requester_email": "citizen@gov.in",
        "claim_details": "Entity affiliation was updated in 2025; please reflect non-combatant status.",
        "supporting_evidence": "Gazette notification dated 2025-08-14.",
    }
    response = client.post("/api/corrections", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "ok"
    assert "id" in data


def test_submit_correction_invalid_type():
    payload = {
        "target_type": "invalid_kind",
        "target_id": "999",
        "requester_email": "citizen@gov.in",
        "claim_details": "Bad classification",
    }
    response = client.post("/api/corrections", json=payload)
    assert response.status_code == 400
    assert "Invalid target_type" in response.json()["detail"]


def test_list_and_resolve_correction():
    # Submit first
    payload = {
        "target_type": "article",
        "target_id": "42",
        "requester_email": "editor@defensenews.in",
        "claim_details": "Headline retraction occurred on wire.",
    }
    submit_res = client.post("/api/corrections", json=payload)
    corr_id = submit_res.json()["id"]

    # List
    list_res = client.get(
        f"/api/corrections?target_type=article",
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(i["id"] == corr_id for i in items)

    # Resolve
    resolve_res = client.put(
        f"/api/corrections/{corr_id}",
        json={
            "status": "accepted",
            "resolution_notes": "Verified against press release, article metadata amended.",
        },
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "ok"
