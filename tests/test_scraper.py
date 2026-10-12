"""
Stage 1 — Scraper tests
Run: pytest tests/ -v
"""
from scraper.rss_scraper import scrape_source


def test_rss_returns_articles(sample_source):
    """Known working RSS source returns a non-empty article list."""
    articles = scrape_source(sample_source)
    assert isinstance(articles, list)
    assert len(articles) > 0, "Expected articles from BBC Asia RSS"


def test_article_has_required_fields(sample_source, required_keys):
    """Every returned article dict has all required fields."""
    articles = scrape_source(sample_source)
    assert articles, "No articles to validate"
    for article in articles:
        missing = required_keys - set(article.keys())
        assert not missing, f"Article missing fields: {missing}"


def test_broken_source_does_not_crash(broken_source):
    """An unreachable source returns empty list — never raises."""
    result = scrape_source(broken_source)
    assert result == []


def test_url_hash_is_idempotent(sample_source):
    """Same source scraped twice produces identical url_hashes."""
    hashes_1 = {a["url_hash"] for a in scrape_source(sample_source)}
    hashes_2 = {a["url_hash"] for a in scrape_source(sample_source)}
    assert hashes_1 == hashes_2
