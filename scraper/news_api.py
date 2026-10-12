"""
NewsAPI scraper — fetches defence-relevant articles via NewsAPI.
Free tier: 100 req/day. We use ~6/day at 4-hour intervals.
"""
import hashlib
from datetime import datetime

import httpx

from common.config import settings
from common.constants import NEWSAPI_KEYWORDS, USER_AGENT
from common.logger import get_logger

logger = get_logger(__name__)
NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_newsapi(keywords: list[str] | None = None) -> list[dict]:
    """
    Fetch articles from NewsAPI using defence keywords.
    Returns same article dict format as rss_scraper.
    """
    if not settings.NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set — skipping NewsAPI fetch")
        return []

    kw    = keywords or NEWSAPI_KEYWORDS
    query = " OR ".join(f'"{k}"' for k in kw)

    params = {
        "q":        query,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": 100,
        "apiKey":   settings.NEWS_API_KEY,
    }

    try:
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0) as client:
            r = client.get(NEWSAPI_URL, params=params)
            r.raise_for_status()
            data = r.json()

        articles = []
        for item in data.get("articles", []):
            url   = item.get("url", "")
            title = (item.get("title") or "").strip()

            if not url or not title or title == "[Removed]":
                continue

            url_hash    = hashlib.md5(url.encode("utf-8")).hexdigest()
            content     = (item.get("description") or item.get("content") or "").strip()
            published_raw = item.get("publishedAt", "")

            try:
                published_at = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                published_at = datetime.utcnow()

            articles.append({
                "source_name":  item.get("source", {}).get("name", "NewsAPI"),
                "title":        title,
                "content":      content,
                "url":          url,
                "url_hash":     url_hash,
                "language":     "en",
                "published_at": published_at,
            })

        logger.info(f"[NewsAPI] Fetched {len(articles)} articles")
        return articles

    except httpx.HTTPStatusError as e:
        logger.error(f"[NewsAPI] HTTP {e.response.status_code}: {e}")
    except Exception as e:
        logger.error(f"[NewsAPI] Error: {e}")

    return []
