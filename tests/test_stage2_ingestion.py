"""
Tests for Stage 2 Ingestion Expansion (40 sources, GDELT 2.0 connector, and proxy handler).
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock
from scraper.sources import RSS_SOURCES
from scraper.gdelt import fetch_gdelt_articles, _parse_gdelt_date
from scraper.rss_scraper import scrape_source
from common.constants import (
    RING_INDIA, RING_ADVERSARY, RING_REGIONAL, RING_GLOBAL
)


def test_sources_count_and_fields():
    assert len(RSS_SOURCES) == 40
    required_keys = {"name", "url", "rss_url", "ring", "country", "language"}

    names = set()
    for s in RSS_SOURCES:
        assert required_keys.issubset(s.keys()), f"Source missing required keys: {s}"
        assert s["ring"] in (1, 2, 3, 4), f"Invalid ring for source: {s}"
        assert s["name"] not in names, f"Duplicate source name: {s['name']}"
        names.add(s["name"])


def test_sources_ring_distribution():
    rings = {1: 0, 2: 0, 3: 0, 4: 0}
    for s in RSS_SOURCES:
        rings[s["ring"]] += 1

    assert rings[RING_INDIA] >= 10, f"Ring 1 underrepresented: {rings[RING_INDIA]}"
    assert rings[RING_ADVERSARY] >= 8, f"Ring 2 underrepresented: {rings[RING_ADVERSARY]}"
    assert rings[RING_REGIONAL] >= 8, f"Ring 3 underrepresented: {rings[RING_REGIONAL]}"
    assert rings[RING_GLOBAL] >= 8, f"Ring 4 underrepresented: {rings[RING_GLOBAL]}"


def test_gdelt_date_parsing():
    parsed = _parse_gdelt_date("20261110T143000Z")
    assert parsed.year == 2026
    assert parsed.month == 11
    assert parsed.day == 10
    assert parsed.hour == 14
    assert parsed.minute == 30

    # Fallback to current time on garbage string
    fallback = _parse_gdelt_date("invalid-date")
    assert isinstance(fallback, datetime)


@patch("httpx.Client")
def test_gdelt_successful_fetch(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "articles": [
            {
                "url": "https://example.com/ladakh-patrol-agreement",
                "title": "India-China complete disengagement in Demchok and Depsang",
                "domain": "thehindu.com",
                "language": "English",
                "seendate": "20261110T120000Z",
            }
        ]
    }
    mock_client.get.return_value = mock_resp

    articles = fetch_gdelt_articles(query="Ladakh disengagement", max_records=5)
    assert len(articles) == 1
    a = articles[0]
    assert a["title"] == "India-China complete disengagement in Demchok and Depsang"
    assert a["source_name"] == "GDELT (thehindu.com)"
    assert a["language"] == "en"
    assert a["url"] == "https://example.com/ladakh-patrol-agreement"
    assert len(a["url_hash"]) == 32


@patch("httpx.Client")
def test_gdelt_handles_errors_gracefully(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    # 429 Rate limited response
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_client.get.return_value = mock_resp

    articles = fetch_gdelt_articles()
    assert articles == []


def test_adversary_proxy_wiring(monkeypatch):
    monkeypatch.setattr("common.config.settings.PROXY_URL", "http://127.0.0.1:8080")
    with patch("feedparser.parse") as mock_parse:
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        adversary_source = {
            "name": "Dawn Pakistan",
            "url": "https://www.dawn.com",
            "rss_url": "https://www.dawn.com/feed",
            "ring": RING_ADVERSARY,
            "country": "Pakistan",
            "language": "en",
        }
        scrape_source(adversary_source)

        assert mock_parse.called
        kwargs = mock_parse.call_args[1]
        handlers = kwargs.get("handlers", [])
        assert len(handlers) == 1
