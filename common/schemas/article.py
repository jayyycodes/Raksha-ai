from pydantic import BaseModel
from typing import List, Optional
from .base import ProvenanceFields

class ArticleIn(BaseModel):
    source_id: int
    title: str
    url: str
    language: Optional[str] = "en"
    published_at: Optional[str] = None
    # content is not stored fully; optional summary
    summary: Optional[str] = None

class ArticleDetail(BaseModel):
    id: int
    source_id: int
    title: str
    url: str
    language: str
    published_at: str
    summary: Optional[str] = None
    processed: bool
    analysis: Optional["AnalysisOut"] = None

class ArticleListResponse(BaseModel):
    articles: List[ArticleDetail]
    total: int
    page: int
    size: int
