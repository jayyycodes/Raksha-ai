"""
Pydantic schemas for the Entity Knowledge Graph (Cytoscape.js support).
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier (e.g., node_12)")
    label: str = Field(..., description="Entity name / display label")
    entity_type: str = Field(..., description="PERSON, ORGANISATION, LOCATION, EQUIPMENT, EVENT")
    primary_ring: int = Field(1, ge=1, le=4, description="Security ring (1=India, 2=Adversary, 3=Regional, 4=Global)")
    mention_count: int = Field(1, description="Number of times mentioned across articles")
    source_count: int = Field(1, description="Number of unique sources reporting this entity")
    is_profile: bool = Field(False, description="Whether this entity qualifies as an established profile")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata (aliases, role, etc.)")


class GraphEdge(BaseModel):
    id: str = Field(..., description="Unique edge identifier (e.g., edge_1_2)")
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    link_type: str = Field(..., description="INVOLVES, LOCATED_IN, ASSOCIATED_WITH, EQUIPPED_WITH, etc.")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Link certainty score")
    article_id: Optional[int] = Field(None, description="Article where this co-occurrence or link was extracted")
    method: str = Field("ner_co_occurrence", description="Method used to establish the link")


class GraphResponse(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0

