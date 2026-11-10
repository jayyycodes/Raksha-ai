"""
GDELT 2.0 Connector — fetches global and regional defence events via GDELT Doc API.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
import hashlib
from datetime import datetime, timezone
import httpx
from common.constants import USER_AGENT, MAX_CONTENT_LENGTH
from common.logger import get_logger

logger = get_logger(__name__)

GDELT_DOC_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# South Asian and Himalayan theatre defence query
DEFAULT_GDELT_QUERY = (
    '(India OR Pakistan OR China OR "Line of Actual Control" OR "Line of Control" '
    'OR Kashmir OR DRDO OR Ladakh OR Arunachal) '
    '(military OR defense OR defence OR missile OR border OR army OR navy OR "air force")'
)


def _parse_gdelt_date(date_str: str) -> datetime:
    """Parse GDELT seendate format: YYYYMMDDTHHMMSSZ."""
    try:
        return datetime.strptime(date_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.strptime(date_str[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)


def fetch_gdelt_articles(
    query: str | None = None,
    max_records: int = 50,
    timeout_seconds: float = 15.0,
) -> list[dict]:
    """
    Fetch recent articles matching defence intelligence criteria from GDELT 2.0 Doc API.
    Returns standard Raksha AI article dictionaries ready for deduplication and DB storage.
    """
    active_query = query or DEFAULT_GDELT_QUERY
    params = {
        "query": active_query,
        "mode": "ArtList",
        "maxrecords": str(max_records),
        "format": "json",
        "sort": "DateDesc",
    }

    try:
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=timeout_seconds) as client:
            resp = client.get(GDELT_DOC_API_URL, params=params)
            if resp.status_code != 200:
                logger.warning(f"[GDELT] HTTP {resp.status_code} from GDELT API")
                return []

            try:
                data = resp.json()
            except Exception:
                logger.warning("[GDELT] Could not parse JSON response from GDELT")
                return []

        raw_articles = data.get("articles", [])
        articles = []

        for item in raw_articles:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            if not url or not title:
                continue

            domain = (item.get("domain") or "news").strip()
            url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
            published_at = _parse_gdelt_date(item.get("seendate", ""))

            # GDELT snippet is concise; ensure copyright-safe length <= 500 chars
            content = title[:MAX_CONTENT_LENGTH]

            lang_raw = (item.get("language") or "en").lower()
            lang = "en" if "eng" in lang_raw else lang_raw[:5]

            articles.append({
                "source_name": f"GDELT ({domain})",
                "title": title,
                "content": content,
                "url": url,
                "url_hash": url_hash,
                "language": lang,
                "published_at": published_at,
            })

        logger.info(f"[GDELT] Fetched {len(articles)} defence articles")
        return articles

    except httpx.TimeoutException:
        logger.warning("[GDELT] Request timed out")
    except Exception as e:
        logger.error(f"[GDELT] Scrape failed: {e}")

    return []
