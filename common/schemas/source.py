from pydantic import BaseModel
from typing import Optional

class SourceOut(BaseModel):
    id: int
    name: str
    url: str
    rss_url: Optional[str] = None
    ring: int
    country: Optional[str] = None
    language: Optional[str] = "en"
    is_active: bool
    last_scraped_at: Optional[str] = None

class SourceHealthOut(BaseModel):
    source_id: int
    last_fetched: Optional[str] = None
    last_success: Optional[str] = None
    article_count: int
    status: str  # ok / stale / failed / empty
