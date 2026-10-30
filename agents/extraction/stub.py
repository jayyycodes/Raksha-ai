"""
Extraction Agent Stub (NER, Event Type, Sentiment, Embeddings).
Owner: Ary (Contract Stub by Jaish)
Stage: 1 (Contract Stub)
"""
from typing import List
from common.constants import EVENT_TYPES, SENTIMENT_NEUTRAL
from common.schemas.articles import ArticleAnalysisOut, ArticleIn, EntityOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class ExtractionAgentStub(BaseAgent[ArticleIn, ArticleAnalysisOut]):
    name = "extraction_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: ArticleIn) -> ArticleAnalysisOut:
        # Basic heuristic entity stub for unblocking platform
        entities: List[EntityOut] = []
        text = f"{input_data.title} {input_data.content or ''}"

        prov = Provenance(
            source_ids=[input_data.id] if input_data.id else [],
            method="stub_heuristic_extraction",
            model_version=f"{self.name}:{self.version}",
            confidence=0.8,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        for kw, etype in [
            ("Ladakh", "LOCATION"),
            ("Kashmir", "LOCATION"),
            ("DRDO", "ORGANISATION"),
            ("Indian Army", "ORGANISATION"),
            ("PLA", "ORGANISATION"),
            ("Rafale", "EQUIPMENT"),
        ]:
            if kw.lower() in text.lower():
                entities.append(EntityOut(entity_type=etype, entity_value=kw, confidence=0.9, provenance=prov))

        return ArticleAnalysisOut(
            article_id=input_data.id,
            translated_text=input_data.content,
            event_type="border_incident" if "border" in text.lower() else "general",
            sentiment=SENTIMENT_NEUTRAL,
            threat_level=4,
            threat_category="medium",
            confidence=0.75,
            entities=entities,
            provenance=prov,
        )
