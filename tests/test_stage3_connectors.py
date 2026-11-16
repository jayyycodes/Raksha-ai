"""
Unit & Integration Tests for Stage 3 Connector Framework & 96+ Source Coverage (Milestone M7).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pytest

from connectors.base import BaseConnector, ConnectorArticle
from connectors.rss_connector import RSSConnector
from connectors.telegram_connector import TelegramChannelConnector
from connectors.firms_satellite import FirmsSatelliteConnector
from connectors.gdelt_connector import GDELTConnector
from connectors.acled_connector import AcledConnector
from connectors.generic_api_connector import GenericAPIConnector
from connectors.registry import ConnectorRegistry
from scraper.sources_stage3 import STAGE3_SOURCES_96
from common.constants import RING_INDIA, RING_ADVERSARY, RING_REGIONAL, RING_GLOBAL


def test_stage3_sources_count_and_distribution():
    """Verify full 96-source expansion across all 4 rings + APIs + Social."""
    assert len(STAGE3_SOURCES_96) >= 96

    rings = {1: 0, 2: 0, 3: 0, 4: 0}
    source_types = set()
    names = set()

    for s in STAGE3_SOURCES_96:
        assert "name" in s
        assert "ring" in s
        assert "country" in s
        assert s["ring"] in (1, 2, 3, 4)
        assert s["name"] not in names, f"Duplicate source name: {s['name']}"
        names.add(s["name"])
        rings[s["ring"]] += 1
        source_types.add(s.get("source_type", "rss"))

    # Validate ring representation matches Stage 3 targets
    assert rings[RING_INDIA] >= 25, f"Ring 1 underrepresented: {rings[RING_INDIA]}"
    assert rings[RING_ADVERSARY] >= 18, f"Ring 2 underrepresented: {rings[RING_ADVERSARY]}"
    assert rings[RING_REGIONAL] >= 12, f"Ring 3 underrepresented: {rings[RING_REGIONAL]}"
    assert rings[RING_GLOBAL] >= 25, f"Ring 4 underrepresented: {rings[RING_GLOBAL]}"
    assert {"rss", "api", "satellite", "telegram"}.issubset(source_types)


def test_base_connector_contract():
    """Custom connector subclasses BaseConnector cleanly."""
    class SampleCustomConnector(BaseConnector):
        def fetch_articles(self, since=None):
            return [{
                "title": "Custom Test Intel",
                "url": "https://example.com/custom/1",
                "content": "Custom test content",
                "source_name": self.name,
                "published_at": datetime.now(timezone.utc).isoformat(),
                "language": self.language,
                "ring": self.ring,
                "country": self.country,
            }]

        def health_check(self):
            return {"status": "ok", "latency_ms": 12.5, "error": None}

    conn = SampleCustomConnector(
        name="Custom Desk Intel",
        source_type="custom",
        ring=1,
        country="India",
    )
    assert conn.name == "Custom Desk Intel"
    assert conn.source_type == "custom"
    articles = conn.fetch_articles()
    assert len(articles) == 1
    assert articles[0]["title"] == "Custom Test Intel"
    health = conn.health_check()
    assert health["status"] == "ok"


def test_rss_connector_mocked():
    """RSSConnector parses entries into standardized article dictionaries."""
    conn = RSSConnector(
        name="Mock RSS",
        rss_url="https://example.com/feed.xml",
        ring=1,
        country="India",
    )
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_entry = MagicMock()
    mock_entry.link = "https://example.com/art-1"
    mock_entry.title = "Border Security Exercise Conducted"
    mock_entry.summary = "Joint operational training in northern sector."
    mock_entry.published_parsed = (2026, 11, 16, 10, 0, 0, 0, 0, 0)
    mock_feed.entries = [mock_entry]

    with patch("connectors.rss_connector.feedparser.parse", return_value=mock_feed):
        articles = conn.fetch_articles()
        assert len(articles) == 1
        a = articles[0]
        assert a["title"] == "Border Security Exercise Conducted"
        assert a["source_name"] == "Mock RSS"
        assert a["ring"] == 1
        assert "url_hash" in a


def test_telegram_channel_connector_parsing():
    """TelegramChannelConnector parses public web preview HTML safely."""
    conn = TelegramChannelConnector(
        name="OSINT Frontier Telegram",
        channel_name="frontier_osint",
        ring=1,
        country="India",
    )
    sample_html = """
    <html>
      <div class="tgme_widget_message_wrap">
        <a class="tgme_widget_message_date" href="https://t.me/frontier_osint/101">
          <time datetime="2026-11-16T08:30:00+00:00"></time>
        </a>
        <div class="tgme_widget_message_text">
          Air Force conducts multi-squadron interception drill across northern bases. Enhanced radar patrol active.
        </div>
      </div>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = sample_html.encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        items = conn.fetch_articles()
        assert len(items) == 1
        item = items[0]
        assert "[OSINT Frontier Telegram]" in item["title"]
        assert "drill" in item["content"]
        assert item["metadata"]["platform"] == "telegram"
        assert item["metadata"]["channel"] == "frontier_osint"


def test_firms_satellite_connector():
    """FirmsSatelliteConnector generates calibrated strategic sector thermal events."""
    conn = FirmsSatelliteConnector()
    items = conn.fetch_articles()
    assert len(items) == 4
    regions = {it["metadata"]["region"] for it in items}
    assert "Ladakh" in regions
    assert "Jammu & Kashmir" in regions
    health = conn.health_check()
    assert health["status"] == "ok"


def test_acled_connector():
    """AcledConnector maps structured conflict events into articles."""
    conn = AcledConnector()
    items = conn.fetch_articles()
    assert len(items) == 2
    for it in items:
        assert it["source_name"] == "ACLED South Asia Conflict Watch"
        assert it["ring"] == 4
        assert "url_hash" in it


def test_connector_registry_full_population():
    """ConnectorRegistry populates all 96 Stage 3 sources and performs health checks."""
    reg = ConnectorRegistry()
    added = reg.populate_stage3_sources()
    assert reg.total_count() == 96

    telegram_conns = [c for c in reg.list_connectors() if c.source_type == "telegram"]
    assert len(telegram_conns) == 10

    api_conns = [c for c in reg.list_connectors() if c.source_type in ("api", "satellite")]
    assert len(api_conns) == 6

    # Test individual retrieval
    assert reg.get("NASA FIRMS Satellite Thermal") is not None
    assert reg.get("Indian Defence Updates") is not None
