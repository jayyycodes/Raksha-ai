"""
Article input/output contracts for pipeline and agent execution.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from common.schemas.provenance import Provenance


class ArticleIn(BaseModel):
    """
    Standard article input model fed into agents and pipeline.
    """
    id: Optional[int] = Field(default=None, description="Article database ID if saved.")
    source_id: Optional[int] = Field(default=None, description="Monitored source ID.")
    title: str = Field(..., min_length=1, description="Article headline.")
    content: Optional[str] = Field(default="", description="Article body or summary.")
    url: str = Field(..., description="Canonical source URL.")
    url_hash: Optional[str] = Field(default=None, description="SHA256 hash of canonical URL.")
    language: str = Field(default="en", description="Detected language code (e.g. 'en', 'ur', 'zh').")
    ring: Optional[int] = Field(default=None, ge=1, le=4, description="Geopolitical source ring (1-4).")
    published_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntityOut(BaseModel):
    """
    Named entity extracted from text with attribution.
    """
    entity_type: str = Field(..., description="Entity category: LOCATION, ORGANISATION, EQUIPMENT, PERSON.")
    entity_value: str = Field(..., min_length=1, description="Resolved entity text name.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: Provenance


class ArticleAnalysisOut(BaseModel):
    """
    Output of Floor 2 (Language & Knowledge) and Floor 3 (Analysis) per article.
    """
    article_id: Optional[int] = None
    translated_text: Optional[str] = None
    event_type: str = Field(default="general", description="Classified event type from constants.py.")
    sentiment: str = Field(default="neutral", description="neutral, aggressive, or alarming.")
    threat_level: int = Field(default=1, ge=1, le=10, description="1 to 10 scale.")
    threat_category: str = Field(default="low", description="low, medium, high.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    entities: List[EntityOut] = Field(default_factory=list)
    provenance: Provenance


class ArticleAnalysisBatchIn(BaseModel):
    articles: List[ArticleIn]


class ArticleAnalysisBatchOut(BaseModel):
    results: List[ArticleAnalysisOut]
