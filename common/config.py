"""
Centralized configuration — reads from .env and exposes a typed settings object.
Usage: from common.config import settings
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    DATABASE_URL: str
    NEWS_API_KEY: str
    SCRAPE_INTERVAL_HOURS: int
    LOG_LEVEL: str
    PROXY_URL: str | None
    GROQ_API_KEY: str | None


def _load() -> Settings:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise EnvironmentError("DATABASE_URL is required but not set in .env")
    return Settings(
        DATABASE_URL=db_url,
        NEWS_API_KEY=os.getenv("NEWS_API_KEY", ""),
        SCRAPE_INTERVAL_HOURS=int(os.getenv("SCRAPE_INTERVAL_HOURS", "4")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        PROXY_URL=os.getenv("PROXY_URL", None),
        GROQ_API_KEY=os.getenv("GROQ_API_KEY", None),
    )


settings = _load()
