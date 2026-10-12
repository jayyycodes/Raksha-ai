"""Shared pytest fixtures for all stages."""
import pytest

SAMPLE_SOURCE = {
    "name":     "BBC Asia",
    "url":      "https://www.bbc.com",
    "rss_url":  "http://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "ring":     4,
    "country":  "Global",
    "language": "en",
}

BROKEN_SOURCE = {
    "name":     "Broken Source",
    "url":      "https://this-domain-does-not-exist-raksha.ai",
    "rss_url":  "https://this-domain-does-not-exist-raksha.ai/rss",
    "ring":     4,
    "country":  "Global",
    "language": "en",
}

REQUIRED_ARTICLE_KEYS = {
    "source_name", "title", "url", "url_hash",
    "content", "language", "published_at",
}


@pytest.fixture
def sample_source():
    return SAMPLE_SOURCE


@pytest.fixture
def broken_source():
    return BROKEN_SOURCE


@pytest.fixture
def required_keys():
    return REQUIRED_ARTICLE_KEYS
