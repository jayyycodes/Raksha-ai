"""
GDELT 2.0 Global Events API Connector.
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
import time
from datetime import datetime
from typing import Any, Optional

from connectors.base import BaseConnector
from scraper.gdelt import fetch_gdelt_articles
from common.logger import get_logger

logger = get_logger(__name__)


class GDELTConnector(BaseConnector):
    """Connector for the GDELT 2.0 Doc API."""

    def __init__(
        self,
        name: str = "GDELT Global Events",
        query: str = "India (defence OR military OR border OR army OR navy OR missile)",
        ring: int = 4,
        country: str = "Global",
        max_records: int = 30,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            name=name,
            source_type="api",
            ring=ring,
            country=country,
            language="en",
            url="https://api.gdeltproject.org/api/v2/doc/doc",
            config=config,
        )
        self.query = query
        self.max_records = max_records

    def fetch_articles(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        return fetch_gdelt_articles(query=self.query, max_records=self.max_records)

    def health_check(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            sample = fetch_gdelt_articles(query="India", max_records=1)
            latency = (time.perf_counter() - start) * 1000
            if sample:
                return {"status": "ok", "latency_ms": round(latency, 2), "error": None}
            return {"status": "stale", "latency_ms": round(latency, 2), "error": "No records returned"}
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {"status": "failed", "latency_ms": round(latency, 2), "error": str(e)}
