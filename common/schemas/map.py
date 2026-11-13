"""
Pydantic schemas for Geospatial Incidents & Tactical Border Mapping (Leaflet.js support).
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class MapIncident(BaseModel):
    id: int = Field(..., description="Unique event / incident ID")
    title: str = Field(..., description="Headline / incident title")
    event_type: str = Field("border_incident", description="Canonical event category")
    threat_level: int = Field(5, ge=1, le=10, description="Numerical threat severity 1-10")
    threat_category: str = Field("medium", description="low, medium, high")
    ring: int = Field(1, ge=1, le=4, description="Security ring (1 to 4)")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    location_name: str = Field(..., description="Geographical name (e.g. Galwan Valley, Hyderabad, Gwadar)")
    region: Optional[str] = Field("Ladakh", description="Broader geopolitical theatre")
    article_id: Optional[int] = Field(None, description="Primary source article ID")
    source_name: Optional[str] = Field(None, description="Reporting news outlet")
    url: Optional[str] = Field(None, description="Canonical source URL")
    summary: Optional[str] = Field(None, description="Intelligence summary excerpt")
    event_id: Optional[int] = Field(None, description="Linked event thread ID")
    event_title: Optional[str] = Field(None, description="Linked event title")
    related_entities: List[dict] = Field(default_factory=list, description="Key entities [{id, name, type}]")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the incident")


class MapResponse(BaseModel):
    incidents: List[MapIncident] = Field(default_factory=list)
    total: int = 0
