"""
Tests for Observability & Prometheus Metrics
"""
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_metrics_endpoint_scraping():
    # Make a dummy call to increment request counter
    client.get("/")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text_content = response.text
    assert "raksha_http_requests_total" in text_content
    assert "raksha_http_request_duration_seconds" in text_content


def test_metrics_recorded_for_api_endpoints():
    client.get("/api/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "raksha_http_requests_total" in response.text
