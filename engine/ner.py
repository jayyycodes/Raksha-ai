"""
Named Entity Recognition — extracts locations, organizations, weapons, persons.
Owner: Ary
Stage: 2

Uses spaCy with en_core_web_lg model.
Entities are stored in the `entities` table.

Usage:
    from engine.ner import extract_entities
    entities = extract_entities("Indian Army deployed troops near Ladakh")
    # [{"entity_type": "ORG", "entity_value": "Indian Army", "confidence": 0.95}, ...]
"""
from common.logger import get_logger

logger = get_logger(__name__)

# Entity types relevant to defence OSINT
ENTITY_TYPES = {
    "LOCATION": "GPE",      # Geopolitical entities (countries, cities, states)
    "ORG": "ORG",           # Organizations (armies, agencies, militant groups)
    "PERSON": "PERSON",     # Named individuals
    "WEAPON": "PRODUCT",    # Weapons systems, missiles, aircraft
    "EVENT": "EVENT",       # Named military operations, exercises
}


def extract_entities(text: str) -> list[dict]:
    """
    Extract named entities from article text.

    Args:
        text: Article text (English, pre-translated if needed)

    Returns:
        List of dicts: [{"entity_type": str, "entity_value": str, "confidence": float}]

    TODO (Ary):
        1. Load spaCy model (en_core_web_lg)
        2. Process text and extract entities
        3. Filter to defence-relevant entity types
        4. Add custom entity patterns for Indian defence terms
           (e.g., "LAC", "LoC", "Siachen", "BrahMos", "Agni-V")
        5. Return confidence scores from spaCy's scorer
    """
    raise NotImplementedError("NER pipeline not yet implemented — Stage 2")
