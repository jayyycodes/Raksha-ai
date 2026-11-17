"""
Public Telegram Defence Channel Connector.
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Scrapes public defense and intelligence channels via their open Telegram web preview
(https://t.me/s/<channel>) without requiring bot tokens or Telegram API credentials.
Strictly adheres to copyright safety (headline + summary <=500 chars).
"""
import hashlib
import re
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from connectors.base import BaseConnector
from common.logger import get_logger

logger = get_logger(__name__)


class TelegramChannelConnector(BaseConnector):
    """
    Public Telegram Channel OSINT Connector.
    Extracts posts from https://t.me/s/<channel_name>
    """

    def __init__(
        self,
        name: str,
        channel_name: str,
        ring: int = 1,
        country: str = "India",
        language: str = "en",
        config: Optional[dict[str, Any]] = None,
    ):
        self.channel_name = channel_name.lstrip("@")
        preview_url = f"https://t.me/s/{self.channel_name}"
        super().__init__(
            name=name,
            source_type="telegram",
            ring=ring,
            country=country,
            language=language,
            url=preview_url,
            config=config,
        )

    def fetch_articles(self, since: Optional[datetime] = None) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        try:
            req = urllib.request.Request(
                self.url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 RakshaAI/3.0",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8", errors="replace")

            if not BeautifulSoup:
                logger.warning("BeautifulSoup not installed; Telegram connector returning empty list.")
                return []

            soup = BeautifulSoup(html, "html.parser")
            message_nodes = soup.find_all("div", class_=re.compile(r"tgme_widget_message_wrap"))

            for msg in message_nodes:
                text_node = msg.find("div", class_=re.compile(r"tgme_widget_message_text"))
                if not text_node:
                    continue

                raw_text = text_node.get_text(separator=" ", strip=True)
                if not raw_text or len(raw_text) < 15:
                    continue

                # Parse post link
                link_node = msg.find("a", class_=re.compile(r"tgme_widget_message_date"))
                post_url = link_node["href"] if link_node and link_node.has_attr("href") else f"{self.url}/{hashlib.md5(raw_text[:30].encode()).hexdigest()[:8]}"

                # Parse time
                pub_dt = datetime.now(timezone.utc)
                time_node = msg.find("time")
                if time_node and time_node.has_attr("datetime"):
                    try:
                        pub_dt = datetime.fromisoformat(time_node["datetime"].replace("Z", "+00:00"))
                    except Exception:
                        pass

                if since and pub_dt < since:
                    continue

                # Headline from first line or first 100 chars
                first_line = raw_text.split("\n")[0].strip()
                title = first_line[:120] if len(first_line) > 10 else raw_text[:100]
                summary = raw_text[:480]

                url_hash = hashlib.sha256(post_url.encode("utf-8")).hexdigest()
                articles.append({
                    "title": f"[{self.name}] {title}",
                    "url": post_url,
                    "url_hash": url_hash,
                    "content": summary,
                    "source_name": self.name,
                    "published_at": pub_dt.isoformat(),
                    "language": self.language,
                    "ring": self.ring,
                    "country": self.country,
                    "metadata": {
                        "channel": self.channel_name,
                        "platform": "telegram",
                    },
                })
        except Exception as exc:
            logger.warning(f"[{self.name}] Failed to fetch public Telegram preview for @{self.channel_name}: {exc}")
        return articles

    def health_check(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "Mozilla/5.0 RakshaAI-HealthCheck/3.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
            latency = (time.perf_counter() - start) * 1000
            if status_code == 200:
                return {"status": "ok", "latency_ms": round(latency, 2), "error": None}
            return {"status": "degraded", "latency_ms": round(latency, 2), "error": f"HTTP {status_code}"}
        except Exception as err:
            latency = (time.perf_counter() - start) * 1000
            return {"status": "failed", "latency_ms": round(latency, 2), "error": str(err)}
