"""
FastAPI Route Integration Tests for Raksha AI MVP.
Tests:
- Root and health endpoints
- Articles endpoint (pagination & filtering structure)
- Sources endpoint
- Stats endpoint
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "raksha-ai"
    assert data["stage"] == "mvp"


def test_health_check_endpoint():
    with patch("common.db.check_connection", return_value=True):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "database": "connected"}


def test_health_check_degraded():
    with patch("common.db.check_connection", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "degraded", "database": "disconnected"}


def test_list_articles_mocked_db():
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": 1,
        "title": "Border patrol reports calm along sector",
        "url": "https://example.com/news/1",
        "language": "en",
        "published_at": "2026-10-31T10:00:00Z",
        "is_processed": True,
        "source_name": "The Hindu",
        "ring": 1,
        "event_type": "border_incident",
        "sentiment": "neutral",
        "threat_level": 3,
        "confidence": 0.85,
        "method": "stub_pipeline_v0",
        "model_version": "0.1.0",
    }
    mock_db.execute.return_value.fetchall.return_value = [mock_row]
    mock_db.execute.return_value.scalar.return_value = 1

    from api.routes.articles import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/articles?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["articles"]) == 1
    assert data["articles"][0]["title"] == "Border patrol reports calm along sector"
    assert data["articles"][0]["threat_level"] == 3

    app.dependency_overrides.clear()


def test_list_sources_mocked_db():
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_row._mapping = {
        "id": 1,
        "name": "The Hindu",
        "url": "https://www.thehindu.com",
        "rss_url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "ring": 1,
        "country": "India",
        "language": "en",
        "is_active": True,
        "last_scraped_at": "2026-10-31T10:00:00Z",
        "total_articles": 42,
        "articles_today": 5,
    }
    mock_db.execute.return_value.fetchall.return_value = [mock_row]

    from api.routes.sources import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "The Hindu"
    assert data[0]["total_articles"] == 42

    app.dependency_overrides.clear()


def test_stats_mocked_db():
    mock_db = MagicMock()
    # Mocking total, today, processed, per_ring, per_source, last_scrape, event_types
    mock_db.execute.return_value.scalar.side_effect = [150, 25, 140, "2026-10-31 12:00:00"]
    mock_ring = MagicMock(ring=1, count=80)
    mock_source = MagicMock(id=1, name="PIB India", count=50)
    mock_event = MagicMock(event_type="diplomatic", count=30)
    mock_db.execute.return_value.fetchall.side_effect = [
        [mock_ring],
        [mock_source],
        [mock_event],
    ]

    from api.routes.stats import get_db
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_articles"] == 150
    assert data["todays_articles"] == 25
    assert data["processed_articles"] == 140
    assert data["per_ring"] == {"1": 80}

    app.dependency_overrides.clear()
