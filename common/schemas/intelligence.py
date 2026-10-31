"""
Intelligence and Generation Schemas (Floor 3 - Jaish).
Contracts for Threat Scoring, Anomaly Detection, SitRep, Profile Summaries, and Corroboration.
"""
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from common.schemas.provenance import ClaimStatus, Provenance


class ThreatCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThreatClassifyIn(BaseModel):
    title: str
    content: Optional[str] = ""
    event_type: str = "general"
    ring: Optional[int] = Field(default=1, ge=1, le=4)
    entities: List[str] = Field(default_factory=list)


class ThreatClassifyOut(BaseModel):
    category: ThreatCategory
    threat_level: int = Field(ge=1, le=10, description="1 to 10 scale for DB compatibility.")
    score: float = Field(ge=0.0, le=10.0)
    matched_keywords: List[str] = Field(default_factory=list)
    reasoning: str
    provenance: Provenance


class RegionalThreatScoreIn(BaseModel):
    region: str
    window_hours: int = 24


class RegionalThreatScoreOut(BaseModel):
    region: str
    score: float = Field(ge=0.0, le=10.0)
    trend: str = Field(default="stable", description="'rising', 'stable', or 'falling'")
    article_count: int = 0
    top_events: List[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: Provenance


class AnomalyCheckIn(BaseModel):
    region: str
    window_hours: int = 24
    baseline_days: int = 30


class AnomalyCheckOut(BaseModel):
    region: str
    is_anomaly: bool
    current_count: int
    baseline_average: float
    deviation_factor: float
    alert_severity: Optional[str] = None
    description: Optional[str] = None
    provenance: Provenance


class SitRepSentence(BaseModel):
    text: str = Field(..., description="Every statement in the SitRep.")
    citations: List[int] = Field(
        default_factory=list,
        description="List of article IDs that support this specific sentence."
    )
    is_supported: bool = Field(
        default=True,
        description="Whether this sentence was verified by grounded citations. Unsupported sentences are flagged."
    )


class SitRepIn(BaseModel):
    report_date: date = Field(default_factory=date.today)
    article_ids: List[int] = Field(default_factory=list)
    region_focus: Optional[str] = None


class SitRepOut(BaseModel):
    report_date: date
    title: str = "Raksha AI Daily Intelligence Situation Report"
    executive_summary: str
    sentences: List[SitRepSentence] = Field(
        default_factory=list,
        description="Full text decomposed into verifiable, cited sentences."
    )
    top_threats: List[Dict[str, Any]] = Field(default_factory=list)
    article_count: int = 0
    grounding_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Share of sentences strictly backed by source citations."
    )
    provenance: Provenance


class ProfileFactOut(BaseModel):
    fact: str
    claim_status: ClaimStatus = ClaimStatus.REPORTED
    source_ids: List[int] = Field(default_factory=list)
    first_seen_at: Optional[datetime] = None
    last_confirmed_at: Optional[datetime] = None


class ProfileSummaryIn(BaseModel):
    entity_id: int
    entity_name: str
    entity_type: str = "PERSON"
    associated_articles: List[Dict[str, Any]] = Field(default_factory=list)


class ProfileSummaryOut(BaseModel):
    entity_id: int
    entity_name: str
    entity_type: str
    summary: str
    facts: List[ProfileFactOut] = Field(default_factory=list)
    claim_status: ClaimStatus = ClaimStatus.REPORTED
    associated_entities: List[str] = Field(default_factory=list)
    provenance: Provenance


class CorroborationIn(BaseModel):
    source_article_id: int
    source_text: str
    source_ring: int
    compare_article_id: int
    compare_text: str
    compare_ring: int


class CorroborationLinkOut(BaseModel):
    source_article_id: int
    compare_article_id: int
    relation: str = Field(..., description="'CORROBORATED_BY' or 'CONTRADICTS'")
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    provenance: Provenance


class CorroborationOut(BaseModel):
    links: List[CorroborationLinkOut] = Field(default_factory=list)
    disinformation_indicator: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated disinformation score based on adversarial cross-contradictions."
    )
    provenance: Provenance
