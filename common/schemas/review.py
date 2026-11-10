"""
Pydantic schemas for the Human-in-the-Loop Disambiguation Review Queue.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MergeSuggestionOut(BaseModel):
    id: int
    source_node_id: int
    source_name: str
    target_node_id: int
    target_name: str
    entity_type: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    status: str = Field("pending", description="pending, accepted, rejected")
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ReviewActionIn(BaseModel):
    action: str = Field(..., description="'accept' (merge), 'reject' (keep separate), 'split'")
    analyst_name: Optional[str] = Field("analyst_1", description="Analyst handling the review")
    notes: Optional[str] = Field(None, description="Optional reasoning notes for the audit trail")


class ReviewQueueResponse(BaseModel):
    suggestions: List[MergeSuggestionOut] = Field(default_factory=list)
    total_pending: int = 0
