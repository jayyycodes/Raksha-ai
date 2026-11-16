"""
Tests for Sandboxed BYOD Upload Service and Routes
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from common.auth import create_access_token

client = TestClient(app)

ANALYST_TOKEN = create_access_token(
    data={"sub": "2", "email": "analyst@raksha.ai", "role": "analyst", "workspace_id": 1}
)
VIEWER_TOKEN = create_access_token(
    data={"sub": "3", "email": "viewer@raksha.ai", "role": "viewer", "workspace_id": 1}
)


def test_upload_valid_csv():
    csv_content = b"date,headline,source,region\n2026-11-16,Indian Navy tests hypersonic glide vehicle,PIB India,Indian Ocean\n2026-11-15,Border post strengthened in Ladakh sector,ANI,LAC-Ladakh\n"
    response = client.post(
        "/api/uploads",
        files={"file": ("border_reports.csv", csv_content, "text/csv")},
        data={"workspace_id": 1},
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "ok"
    upload = data["upload"]
    assert upload["filename"] == "border_reports.csv"
    assert upload["source_type"] == "user_upload"
    assert upload["parse_summary"]["format"] == "csv"
    assert upload["parse_summary"]["row_count"] == 2


def test_upload_valid_txt():
    txt_content = b"Strategic report: Surveillance UAV detected movement near coordinates 34.12, 77.58. Ground units dispatched."
    response = client.post(
        "/api/uploads",
        files={"file": ("uav_recon.txt", txt_content, "text/plain")},
        data={"workspace_id": 1},
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert response.status_code == 200, response.text
    upload = response.json()["upload"]
    assert upload["filename"] == "uav_recon.txt"
    assert upload["parse_summary"]["format"] == "txt"
    assert upload["parse_summary"]["word_count"] > 10


def test_upload_reject_executable_binary():
    # MZ DOS/PE executable header
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00malicious_code_here"
    response = client.post(
        "/api/uploads",
        files={"file": ("malware.exe", exe_content, "application/octet-stream")},
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert response.status_code == 400
    assert "Executable files" in response.json()["detail"]


def test_upload_reject_script_tags():
    script_content = b"<script>alert('xss');</script><h1>Malicious</h1>"
    response = client.post(
        "/api/uploads",
        files={"file": ("exploit.html", script_content, "text/html")},
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert response.status_code == 400
    assert "Script files and HTML executables are strictly prohibited" in response.json()["detail"]


def test_upload_viewer_forbidden():
    csv_content = b"id,val\n1,2"
    response = client.post(
        "/api/uploads",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {VIEWER_TOKEN}"},
    )
    assert response.status_code == 403


def test_list_and_delete_uploads():
    response = client.get(
        "/api/uploads?workspace_id=1",
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1

    first_id = data["items"][0]["id"]
    del_res = client.delete(
        f"/api/uploads/{first_id}",
        headers={"Authorization": f"Bearer {ANALYST_TOKEN}"},
    )
    assert del_res.status_code == 200
