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
    GROQ_MODEL: str
    LLM_FALLBACK_API_KEY: str | None = None
    LLM_FALLBACK_ENDPOINT: str = "https://api.openai.com/v1/chat/completions"
    LLM_FALLBACK_MODEL: str = "gpt-4o-mini"
    OLLAMA_HOST: str | None = None
    OLLAMA_MODEL: str = "llama3"


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
        GROQ_MODEL=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        LLM_FALLBACK_API_KEY=os.getenv("LLM_FALLBACK_API_KEY", os.getenv("OPENAI_API_KEY", None)),
        LLM_FALLBACK_ENDPOINT=os.getenv("LLM_FALLBACK_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
        LLM_FALLBACK_MODEL=os.getenv("LLM_FALLBACK_MODEL", "gpt-4o-mini"),
        OLLAMA_HOST=os.getenv("OLLAMA_HOST", None),
        OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "llama3"),
    )


settings = _load()
