"""
Event and threading schemas for Raksha AI ontology.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from common.schemas.provenance import Provenance


class EventIn(BaseModel):
    title: str
    region: Optional[str] = None
    event_type: str = "general"
    status: str = "ongoing"
    summary: Optional[str] = None


class EventOut(BaseModel):
    id: Optional[int] = None
    title: str
    region: Optional[str] = None
    event_type: str
    status: str = "ongoing"
    threat_level: float = 0.0
    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    article_count: int = 1
    summary: Optional[str] = None
    provenance: Provenance


class EventLinkOut(BaseModel):
    event_id: int
    article_id: int
    link_method: str = Field(..., description="Method used: entity_overlap, semantic_cosine, keyword_match.")
    confidence: float = Field(ge=0.0, le=1.0)
    is_seed: bool = False
    explanation: Optional[str] = Field(
        default=None,
        description="Explainable link rationale: shared entities and similarity metrics."
    )
    provenance: Provenance


class EventThreadingIn(BaseModel):
    article_id: int
    title: str
    content: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    event_type: str = "general"
    region: Optional[str] = None
    window_days: int = Field(default=180, description="6-month threading lookback window.")


class EventThreadingOut(BaseModel):
    article_id: int
    matched_event_id: Optional[int] = None
    candidate_links: List[EventLinkOut] = Field(default_factory=list)
    created_new_event: bool = False
    new_event_title: Optional[str] = None
    provenance: Provenance
