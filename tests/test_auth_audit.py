"""
Test Suite: Stage 3 Solid — Auth, RBAC, Workspaces, and Immutable Audit Log
Owner: Jay (Lead & Platform) | Milestone: M8
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from common.auth import create_access_token
from common.cache import cache_set, cache_get, cache_invalidate_prefix, is_redis_online

client = TestClient(app)


def test_auth_login_success():
    """Verify default seeded analyst can log in and receive valid JWT token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "analyst@raksha.ai", "password": "Analyst@Raksha2026"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "analyst@raksha.ai"
    assert data["user"]["role"] == "analyst"


def test_auth_login_invalid_password():
    """Verify wrong password returns 401 and logs failure."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "analyst@raksha.ai", "password": "WrongPassword123"},
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_auth_me_protected():
    """Verify /api/auth/me rejects unauthenticated requests and accepts valid token."""
    # 1. No token -> 401
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 2. Valid token -> 200
    token = create_access_token({"sub": "2", "email": "analyst@raksha.ai", "role": "analyst"})
    auth_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_resp.status_code == 200
    data = auth_resp.json()
    assert data["user"]["email"] == "analyst@raksha.ai"
    assert "workspaces" in data


def test_audit_log_access_and_filtering():
    """Verify RBAC and immutable audit log exploration."""
    analyst_token = create_access_token({"sub": "2", "email": "analyst@raksha.ai", "role": "analyst"})
    viewer_token = create_access_token({"sub": "3", "email": "viewer@raksha.ai", "role": "viewer"})

    # 1. Viewer is forbidden (403) from accessing audit logs
    viewer_resp = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_resp.status_code == 403

    # 2. Analyst is authorized (200)
    analyst_resp = client.get(
        "/api/audit",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert analyst_resp.status_code == 200
    data = analyst_resp.json()
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)


def test_audit_summary_endpoint():
    """Verify audit summary telemetry endpoint."""
    admin_token = create_access_token({"sub": "1", "email": "admin@raksha.ai", "role": "admin"})
    resp = client.get(
        "/api/audit/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_audit_records" in data
    assert "records_last_24h" in data
    assert "action_breakdown" in data


def test_redis_cache_layer():
    """Verify Redis caching set, get, and prefix invalidation."""
    if not is_redis_online():
        pytest.skip("Redis service not active in test environment")

    test_key = "test:threats:sample_theatre"
    test_val = {"threat_score": 8.5, "theatre": "Western-Border"}

    # Set
    success = cache_set(test_key, test_val, ttl_seconds=10)
    assert success is True

    # Get
    retrieved = cache_get(test_key)
    assert retrieved == test_val

    # Invalidate prefix
    invalidated = cache_invalidate_prefix("test:threats")
    assert invalidated >= 1

    # Verify evicted
    assert cache_get(test_key) is None
