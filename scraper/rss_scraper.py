"""
RSS feed scraper — fetches and parses articles from all RSS sources.
"""
import hashlib
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from langdetect import detect, LangDetectException

from common.constants import (
    LANG_DETECT_MIN_CHARS, MIN_TITLE_LENGTH,
    MAX_CONTENT_LENGTH, REQUEST_DELAY_SECONDS,
    RING_ADVERSARY, USER_AGENT,
)
from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)


def _parse_date(entry) -> datetime:
    """Extract published_at from RSS entry; fall back to NOW."""
    for field in ("published", "updated"):
        val = getattr(entry, field, None)
        if val:
            try:
                return parsedate_to_datetime(val).astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.utcnow()


def _detect_language(text: str, default_lang: str) -> str:
    """Detect language with safe fallback."""
    if not text or len(text) < LANG_DETECT_MIN_CHARS:
        return default_lang
    try:
        return detect(text)
    except LangDetectException:
        return default_lang


def scrape_source(source: dict) -> list[dict]:
    """
    Scrape a single RSS source.
    Returns a list of clean article dicts ready for DB insert.
    Never raises — returns empty list on any failure.
    """
    name         = source.get("name", "unknown")
    rss_url      = source.get("rss_url", "")
    default_lang = source.get("language", "en")
    ring         = source.get("ring", 4)

    # Optional proxy for Ring 2 adversary sources
    proxies = None
    if ring == RING_ADVERSARY and settings.PROXY_URL:
        proxies = {"http": settings.PROXY_URL, "https": settings.PROXY_URL}

    try:
        feed = feedparser.parse(rss_url, agent=USER_AGENT)

        if feed.bozo and not feed.entries:
            logger.warning(f"[{name}] Malformed or unreachable feed: {rss_url}")
            return []

        articles = []
        for entry in feed.entries:
            title = (getattr(entry, "title", "") or "").strip()
            if len(title) < MIN_TITLE_LENGTH:
                continue

            url = getattr(entry, "link", "") or ""
            if not url:
                continue

            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
            content  = (
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
                or ""
            ).strip()[:MAX_CONTENT_LENGTH]

            published_at = _parse_date(entry)
            language     = _detect_language(content or title, default_lang)

            articles.append({
                "source_name":  name,
                "title":        title,
                "content":      content,
                "url":          url,
                "url_hash":     url_hash,
                "language":     language,
                "published_at": published_at,
            })

        logger.info(f"[{name}] Fetched {len(articles)} articles")
        return articles

    except Exception as e:
        logger.error(f"[{name}] Scrape failed: {e}")
        return []


def scrape_all_sources(sources: list[dict]) -> list[dict]:
    """Scrape all sources with a polite delay. Returns combined article list."""
    all_articles = []
    for i, source in enumerate(sources):
        all_articles.extend(scrape_source(source))
        if i < len(sources) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)
    logger.info(f"Total fetched across all sources: {len(all_articles)}")
    return all_articles
