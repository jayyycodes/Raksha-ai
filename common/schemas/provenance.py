"""
Provenance schema for Raksha AI.
Every derived record, analysis result, and report assertion must carry provenance.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    REPORTED = "reported"
    OFFICIAL_DESIGNATION = "official_designation"
    ANALYST_VERIFIED = "analyst_verified"
    DISPUTED = "disputed"


class SourceType(str, Enum):
    PUBLIC = "public"
    USER_UPLOAD = "user_upload"


class Provenance(BaseModel):
    """
    Immutable audit trail and provenance record for derived data.
    """
    source_ids: List[int] = Field(
        default_factory=list,
        description="IDs of raw articles or uploads that generated/supported this record."
    )
    method: str = Field(
        ...,
        description="Method or algorithm used (e.g. 'rule_v0', 'spacy_ner', 'groq_llama3', 'cosine_similarity')."
    )
    model_version: str = Field(
        ...,
        description="Version string of the agent or model (e.g. 'threat-v0.1.0', 'llama-3-8b-8192')."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0."
    )
    claim_status: Optional[ClaimStatus] = Field(
        default=ClaimStatus.REPORTED,
        description="Attribution status of the claim."
    )
    source_type: SourceType = Field(
        default=SourceType.PUBLIC,
        description="Origin of the source data: public OSINT or user-uploaded private document."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when this derivation was computed."
    )
