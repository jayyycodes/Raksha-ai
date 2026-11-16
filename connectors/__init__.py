"""
Raksha AI Plug-in Connector Framework (Stage 3 Solid - Milestone M7).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from connectors.base import BaseConnector, ConnectorArticle
from connectors.rss_connector import RSSConnector
from connectors.telegram_connector import TelegramChannelConnector
from connectors.firms_satellite import FirmsSatelliteConnector
from connectors.gdelt_connector import GDELTConnector
from connectors.acled_connector import AcledConnector
from connectors.registry import ConnectorRegistry, registry

__all__ = [
    "BaseConnector",
    "ConnectorArticle",
    "RSSConnector",
    "TelegramChannelConnector",
    "FirmsSatelliteConnector",
    "GDELTConnector",
    "AcledConnector",
    "ConnectorRegistry",
    "registry",
]
