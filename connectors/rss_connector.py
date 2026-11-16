"""
Plug-in RSS/Atom feed connector.
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Optional
import feedparser

from connectors.base import BaseConnector
from common.logger import get_logger

logger = get_logger(__name__)


class RSSConnector(BaseConnector):
    """Connector for standard RSS and Atom feeds."""

    def __init__(
        self,
        name: str,
        rss_url: str,
        ring: int,
        country: str,
        language: str = "en",
        url: str = "",
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            name=name,
            source_type="rss",
            ring=ring,
            country=country,
            language=language,
            url=url or rss_url,
            config=config,
        )
        self.rss_url = rss_url

    def fetch_articles(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        try:
            feed = feedparser.parse(
                self.rss_url,
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) RakshaAI-OSINT/3.0",
            )
            if feed.bozo and not feed.entries:
                logger.warning(f"[{self.name}] Malformed or unreachable RSS feed: {self.rss_url}")
                return []

            for entry in feed.entries:
                link = getattr(entry, "link", None)
                title = getattr(entry, "title", None)
                if not link or not title:
                    continue

                raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                content = raw_summary[:500] if raw_summary else title

                # Parse publish time
                pub_dt = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                if since and pub_dt < since:
                    continue

                url_hash = hashlib.sha256(link.encode("utf-8")).hexdigest()
                articles.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "url_hash": url_hash,
                    "content": content.strip(),
                    "source_name": self.name,
                    "published_at": pub_dt.isoformat(),
                    "language": self.language,
                    "ring": self.ring,
                    "country": self.country,
                    "metadata": {"rss_url": self.rss_url},
                })
        except Exception as exc:
            logger.error(f"[{self.name}] Error in RSS fetch: {exc}")
        return articles

    def health_check(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            feed = feedparser.parse(self.rss_url)
            latency = (time.perf_counter() - start) * 1000
            if feed.entries or len(getattr(feed, "feed", {})) > 0:
                return {"status": "ok", "latency_ms": round(latency, 2), "error": None}
            return {"status": "stale", "latency_ms": round(latency, 2), "error": "Empty feed entries"}
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {"status": "failed", "latency_ms": round(latency, 2), "error": str(e)}
