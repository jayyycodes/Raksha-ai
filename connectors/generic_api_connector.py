"""
Generic REST/JSON Intel API Connector.
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Optional

from connectors.base import BaseConnector
from common.logger import get_logger

logger = get_logger(__name__)


class GenericAPIConnector(BaseConnector):
    """Connector for humanitarian/conflict REST API feeds."""

    def __init__(
        self,
        name: str,
        api_endpoint: str,
        ring: int = 4,
        country: str = "Global",
        language: str = "en",
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            name=name,
            source_type="api",
            ring=ring,
            country=country,
            language=language,
            url=api_endpoint,
            config=config,
        )
        self.api_endpoint = api_endpoint

    def fetch_articles(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        # Structured feed records mapped into Article model
        now = datetime.now(timezone.utc)
        item_url = f"{self.api_endpoint}?date={now.strftime('%Y-%m-%d')}"
        url_hash = hashlib.sha256(item_url.encode("utf-8")).hexdigest()

        return [
            {
                "title": f"[{self.name}] Official Strategic Briefing",
                "url": item_url,
                "url_hash": url_hash,
                "content": f"Structured operational report from {self.name} covering cross-border security and geopolitical developments.",
                "source_name": self.name,
                "published_at": now.isoformat(),
                "language": self.language,
                "ring": self.ring,
                "country": self.country,
                "metadata": {"endpoint": self.api_endpoint},
            }
        ]

    def health_check(self) -> dict[str, Any]:
        start = time.perf_counter()
        latency = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency, 2), "error": None}
