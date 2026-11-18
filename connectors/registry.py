"""
Central Connector Registry and Plug-in Discovery for Raksha AI.
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Allows registering, discovering, and executing modular connectors.
A new source can be added via 1 small file placed in `connectors/sources/` or registered dynamically.
"""
import importlib
import os
import pkgutil
from datetime import datetime
from typing import Any, Optional, Type

from connectors.base import BaseConnector
from connectors.rss_connector import RSSConnector
from connectors.telegram_connector import TelegramChannelConnector
from connectors.firms_satellite import FirmsSatelliteConnector
from connectors.gdelt_connector import GDELTConnector
from connectors.acled_connector import AcledConnector
from connectors.generic_api_connector import GenericAPIConnector
from common.logger import get_logger

logger = get_logger(__name__)


class ConnectorRegistry:
    """
    Registry for managing all data connectors across Rings 1–4, APIs, and Social/Telegram.
    """

    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}
        self._load_builtins()
        self._discover_plugins()

    def register(self, connector: BaseConnector) -> None:
        """Register a connector instance."""
        self._connectors[connector.name] = connector
        logger.debug(f"Registered connector: {connector.name} ({connector.source_type})")

    def unregister(self, name: str) -> None:
        """Remove a connector by name."""
        self._connectors.pop(name, None)

    def get(self, name: str) -> Optional[BaseConnector]:
        """Retrieve a registered connector by name."""
        return self._connectors.get(name)

    def list_connectors(self) -> list[BaseConnector]:
        """List all active connector instances."""
        return list(self._connectors.values())

    def total_count(self) -> int:
        """Return total number of registered connectors."""
        return len(self._connectors)

    def fetch_all(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Run all registered connectors and aggregate incoming articles."""
        all_articles: list[dict[str, Any]] = []
        for name, conn in self._connectors.items():
            try:
                items = conn.fetch_articles(since=since)
                all_articles.extend(items)
            except Exception as exc:
                logger.error(f"Error fetching from connector '{name}': {exc}")
        return all_articles

    def health_report(self, limit: Optional[int] = None, max_workers: int = 16, timeout: float = 3.5) -> list[dict[str, Any]]:
        """Run health checks across registered connectors concurrently with safe timeout."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        items = list(self._connectors.items())
        if limit and limit > 0:
            items = items[:limit]

        reports = []

        def _probe(item):
            name, conn = item
            try:
                health = conn.health_check()
                return {
                    "name": name,
                    "source_type": conn.source_type,
                    "ring": conn.ring,
                    "country": conn.country,
                    "language": conn.language,
                    **health,
                }
            except Exception as e:
                return {
                    "name": name,
                    "source_type": conn.source_type,
                    "ring": conn.ring,
                    "country": conn.country,
                    "language": conn.language,
                    "status": "failed",
                    "error": str(e),
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {executor.submit(_probe, it): it[0] for it in items}
            for future in as_completed(future_to_name):
                try:
                    res = future.result(timeout=timeout)
                    reports.append(res)
                except Exception as exc:
                    name = future_to_name[future]
                    reports.append({
                        "name": name,
                        "status": "timeout",
                        "error": f"Health check timed out: {exc}",
                    })
        return reports

    def populate_stage3_sources(self) -> int:
        """Register all 96+ Stage 3 sources into the connector registry."""
        from scraper.sources_stage3 import STAGE3_SOURCES_96

        count = 0
        for src in STAGE3_SOURCES_96:
            name = src["name"]
            stype = src.get("source_type", "rss")
            if name in self._connectors:
                continue

            if stype == "rss" and "rss_url" in src:
                conn = RSSConnector(
                    name=name,
                    rss_url=src["rss_url"],
                    ring=src["ring"],
                    country=src["country"],
                    language=src.get("language", "en"),
                    url=src.get("url", ""),
                )
                self.register(conn)
                count += 1
            elif stype == "telegram" and "channel" in src:
                conn = TelegramChannelConnector(
                    name=name,
                    channel_name=src["channel"],
                    ring=src["ring"],
                    country=src["country"],
                    language=src.get("language", "en"),
                )
                self.register(conn)
                count += 1
            elif stype == "api" and "api_endpoint" in src:
                conn = GenericAPIConnector(
                    name=name,
                    api_endpoint=src["api_endpoint"],
                    ring=src["ring"],
                    country=src["country"],
                    language=src.get("language", "en"),
                )
                self.register(conn)
                count += 1

        return count

    def _load_builtins(self) -> None:
        """Initialize built-in API and special connectors."""
        # Built-in structured APIs
        self.register(GDELTConnector())
        self.register(FirmsSatelliteConnector())
        self.register(AcledConnector())

    def _discover_plugins(self) -> None:
        """Scan `connectors/sources/` for dynamic 1-file plug-in connectors."""
        plugins_dir = os.path.join(os.path.dirname(__file__), "sources")
        if not os.path.exists(plugins_dir):
            return

        for _, module_name, _ in pkgutil.iter_modules([plugins_dir]):
            try:
                mod = importlib.import_module(f"connectors.sources.{module_name}")
                # If module exposes a `get_connector()` function or `CONNECTOR` instance
                if hasattr(mod, "get_connector"):
                    conn = mod.get_connector()
                    if isinstance(conn, BaseConnector):
                        self.register(conn)
                elif hasattr(mod, "CONNECTOR") and isinstance(mod.CONNECTOR, BaseConnector):
                    self.register(mod.CONNECTOR)
            except Exception as exc:
                logger.warning(f"Failed to load plug-in connector '{module_name}': {exc}")


# Global default registry instance
registry = ConnectorRegistry()
