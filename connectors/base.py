"""
Base Connector Interface for Raksha AI (Stage 3 Solid - Milestone M7).
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Defines the plug-in connector interface allowing any new source (RSS, public Telegram,
satellite thermal anomaly, conflict event API) to be added with a single lightweight class.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class ConnectorArticle(BaseModel):
    """Standardized article dictionary returned by any connector."""
    title: str
    url: str
    url_hash: Optional[str] = None
    content: str
    source_name: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    ring: int = 1
    country: str = "India"
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base class for all data connectors.
    To add a new source, subclass this class and implement `fetch_articles` and `health_check`.
    """

    def __init__(
        self,
        name: str,
        source_type: str,
        ring: int,
        country: str,
        language: str = "en",
        url: str = "",
        config: Optional[dict[str, Any]] = None,
    ):
        self.name = name
        self.source_type = source_type
        self.ring = ring
        self.country = country
        self.language = language
        self.url = url
        self.config = config or {}

    @abstractmethod
    def fetch_articles(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        """
        Fetch new items from the data source published after `since`.
        Returns a list of standardized article dictionaries.
        """
        pass

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """
        Probe source reachability and return status dictionary.
        Returns:
            {"status": "ok" | "stale" | "failed", "latency_ms": float, "error": str | None}
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize connector metadata for source directory and UI."""
        return {
            "name": self.name,
            "source_type": self.source_type,
            "ring": self.ring,
            "country": self.country,
            "language": self.language,
            "url": self.url,
            "config": self.config,
        }
