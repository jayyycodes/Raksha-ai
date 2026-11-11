"""
Extraction Agent for Raksha AI.
Floor 2 — Language & Knowledge Agents
Owner: Ary
Stage: 2 Production Implementation

Bridges engine.ner and engine.classifier into the BaseAgent protocol,
producing typed ArticleAnalysisOut with structured entities and provenance.
"""
from typing import Any, Dict, List, Optional, Union

from agents.base import BaseAgent
from common.constants import (
    EVENT_TYPES,
    SENTIMENT_NEUTRAL,
)
from common.logger import get_logger
from common.schemas.articles import ArticleAnalysisOut, ArticleIn, EntityOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from engine.classifier import classify_event
from engine.ner import DEFENSE_PATTERNS, extract_entities

logger = get_logger(__name__)

# Canonical type mapping from NER engine to Platform Schema
ENTITY_TYPE_NORMALIZATION: Dict[str, str] = {
    "ORG": "ORGANISATION",
    "ORGANISATION": "ORGANISATION",
    "ORGANIZATION": "ORGANISATION",
    "WEAPON": "EQUIPMENT",
    "EQUIPMENT": "EQUIPMENT",
    "PRODUCT": "EQUIPMENT",
    "LOC": "LOCATION",
    "LOCATION": "LOCATION",
    "GPE": "LOCATION",
    "PERSON": "PERSON",
    "EVENT": "EVENT",
}

# Threat heuristics based on canonical event types
HIGH_THREAT_EVENTS = {"border_incident", "terror_activity", "nuclear", "cyber_attack"}
MEDIUM_THREAT_EVENTS = {"military_movement", "naval", "aerial", "disinformation"}


class ExtractionAgent(BaseAgent[Union[ArticleIn, Dict[str, Any]], ArticleAnalysisOut]):
    """
    Executes Named Entity Recognition and Event Classification on articles,
    emitting a fully structured ArticleAnalysisOut with entity provenance.
    """
    name: str = "extraction_agent"
    version: str = "0.2.0"

    def run(self, input_data: Union[ArticleIn, Dict[str, Any]]) -> ArticleAnalysisOut:
        """
        Execute extraction inference on a single article.
        """
        if isinstance(input_data, ArticleIn):
            article_id = input_data.id
            title = input_data.title or ""
            content = input_data.content or ""
            translated_text = content
        elif isinstance(input_data, dict):
            article_id = input_data.get("id") or input_data.get("article_id")
            title = input_data.get("title") or ""
            content = input_data.get("content") or ""
            translated_text = input_data.get("translated_text") or content
        else:
            raise TypeError(f"Unsupported input type for ExtractionAgent: {type(input_data).__name__}")

        source_ids = [article_id] if article_id is not None else []
        analysis_text = f"{title}. {content}".strip()
        if not analysis_text:
            analysis_text = title or content or ""

        # 1. Named Entity Extraction
        entities_out: List[EntityOut] = []
        if analysis_text:
            raw_entities = []
            try:
                raw_entities = extract_entities(analysis_text)
            except Exception as exc:
                logger.warning(
                    "Full spaCy NER unavailable, falling back to defense patterns for article %s: %s",
                    article_id,
                    exc,
                )
                seen_keys = set()
                for pattern, etype, conf in DEFENSE_PATTERNS:
                    for match in pattern.finditer(analysis_text):
                        val = match.group(0).strip()
                        key = (etype, val.lower())
                        if key not in seen_keys:
                            seen_keys.add(key)
                            raw_entities.append(
                                {
                                    "entity_type": etype,
                                    "entity_value": val,
                                    "confidence": conf,
                                }
                            )

            for ent in raw_entities:
                raw_type = ent.get("entity_type", "LOCATION")
                norm_type = ENTITY_TYPE_NORMALIZATION.get(raw_type, raw_type)
                val = ent.get("entity_value", "").strip()
                conf = float(ent.get("confidence", 0.85))

                ent_prov = Provenance(
                    source_ids=source_ids,
                    method="spacy_ner_defense_patterns",
                    model_version="ner-v0.1.0",
                    confidence=conf,
                    claim_status=ClaimStatus.REPORTED,
                    source_type=SourceType.PUBLIC,
                )
                entities_out.append(
                    EntityOut(
                        entity_type=norm_type,
                        entity_value=val,
                        confidence=conf,
                        provenance=ent_prov,
                    )
                )

        # 2. Event Classification
        event_type = "general"
        event_confidence = 0.50
        if analysis_text:
            try:
                clf_res = classify_event(analysis_text)
                event_type = clf_res.get("event_type", "general")
                event_confidence = float(clf_res.get("confidence", 0.50))
            except Exception as exc:
                logger.error("Event classification failed for article %s: %s", article_id, exc)

        # 3. Threat and Sentiment Heuristics
        if event_type in HIGH_THREAT_EVENTS:
            threat_level = 8
            threat_category = "high"
        elif event_type in MEDIUM_THREAT_EVENTS:
            threat_level = 5
            threat_category = "medium"
        else:
            threat_level = 2
            threat_category = "low"

        sentiment = SENTIMENT_NEUTRAL
        lower_text = analysis_text.lower()
        if any(w in lower_text for w in ["attack", "strike", "clash", "killed", "hostile", "retaliation"]):
            sentiment = "alarming"

        overall_prov = Provenance(
            source_ids=source_ids,
            method="ner_and_event_classifier",
            model_version=f"{self.name}:{self.version}",
            confidence=event_confidence,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return ArticleAnalysisOut(
            article_id=article_id,
            translated_text=translated_text or title,
            event_type=event_type,
            sentiment=sentiment,
            threat_level=threat_level,
            threat_category=threat_category,
            confidence=event_confidence,
            entities=entities_out,
            provenance=overall_prov,
        )
