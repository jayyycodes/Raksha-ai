from pydantic import BaseModel
from typing import Optional

class StatsOut(BaseModel):
    total_articles: int
    todays_articles: int
    per_ring: dict[int, int]
    per_source: dict[int, int]
    last_scrape_at: Optional[str] = None
