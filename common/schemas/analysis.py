from pydantic import BaseModel
from typing import Optional, List
from .base import ProvenanceFields

class AnalysisOut(BaseModel, ProvenanceFields):
    """Result of the NLP pipeline for a single article."""
    article_id: int
    translated_text: Optional[str] = None
    event_type: Optional[str] = None
    sentiment: Optional[str] = None
    threat_level: Optional[int] = None
    confidence: Optional[float] = None
