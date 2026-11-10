"""
Pydantic schemas for Entity Profile (Object View) Pages.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from common.schemas.provenance import ClaimStatus


class ProfileHeader(BaseModel):
    id: int
    name: str
    entity_type: str
    aliases: List[str] = Field(default_factory=list)
    primary_ring: int = Field(1, ge=1, le=4)
    mention_count: int = 1
    source_count: int = 1
    is_profile: bool = False
    description: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime


class ProfileFactOut(BaseModel):
    id: int
    fact: str
    claim_status: ClaimStatus = ClaimStatus.REPORTED
    article_id: Optional[int] = None
    source_name: Optional[str] = None
    confidence: float = 0.8
    created_at: datetime


class ProfileTimelineEvent(BaseModel):
    date: datetime
    title: str
    event_type: str
    threat_level: int
    article_id: int
    source_name: str


class ProfileDetailOut(BaseModel):
    header: ProfileHeader
    facts: List[ProfileFactOut] = Field(default_factory=list)
    timeline: List[ProfileTimelineEvent] = Field(default_factory=list)
    associates: List[Dict[str, Any]] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)

