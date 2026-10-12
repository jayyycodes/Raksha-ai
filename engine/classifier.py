"""
Event Classifier — classifies articles into defence event types.
Owner: Ary
Stage: 2

Classifies each article into one of the EVENT_TYPES defined in common/constants.py:
    border_incident, cyber_attack, terror_activity, diplomatic,
    disinformation, military_movement, naval, aerial, nuclear, general

Usage:
    from engine.classifier import classify_event
    result = classify_event("Indian Navy conducts exercise in Arabian Sea")
    # {"event_type": "naval", "confidence": 0.87}
"""
from common.constants import EVENT_TYPES
from common.logger import get_logger

logger = get_logger(__name__)


def classify_event(text: str) -> dict:
    """
    Classify article text into a defence event type.

    Args:
        text: Article text (English)

    Returns:
        {"event_type": str, "confidence": float}

    TODO (Ary):
        1. Use zero-shot classification (facebook/bart-large-mnli) OR
           fine-tune a lightweight classifier on labelled defence articles
        2. Map model output to EVENT_TYPES constants
        3. Return confidence score
        4. Handle edge cases: articles that span multiple event types
           → return the primary type with highest confidence
    """
    raise NotImplementedError("Event classifier not yet implemented — Stage 2")
