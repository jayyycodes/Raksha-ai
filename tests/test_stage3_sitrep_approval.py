"""
Unit Tests for SitRep Analyst Approval Workflow (Stage 3 Solid - Milestone M9).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app


def test_sitrep_approval_endpoint_mocked():
    """Analyst can approve a SitRep, persisting status and approval metadata."""
    client = TestClient(app)

    mock_db = MagicMock()
    # Simulate existing sitrep row
    mock_row = MagicMock()
    mock_row.id = 1
    mock_db.execute.return_value.fetchone.return_value = mock_row

    with patch("api.routes.sitrep._get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_db

        payload = {
            "analyst_name": "Lead Analyst (Jaish)",
            "notes": "Verified against PIB releases.",
        }
        res = client.post("/api/sitreps/2026-11-16/approve", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "approved"
        assert data["approved_by"] == "Lead Analyst (Jaish)"
        assert "approved_at" in data


def test_sitrep_rejection_endpoint_mocked():
    """Analyst can reject/request revisions for a SitRep with remarks."""
    client = TestClient(app)

    mock_db = MagicMock()
    with patch("api.routes.sitrep._get_db") as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_db

        payload = {
            "analyst_name": "Senior Reviewer",
            "reason": "Re-check casualty discrepancy in sector 4.",
        }
        res = client.post("/api/sitreps/2026-11-16/reject", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "Re-check casualty discrepancy in sector 4."
