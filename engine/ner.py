"""
Named Entity Recognition — extracts locations, organizations, weapons, persons, events.
Owner: Ary
Stage: 1 (Basic Entity Extraction MVP) / Stage 2 (Full NER Pipeline)

Uses spaCy (default: en_core_web_sm) with lazy loading, caching, and lightweight
pattern-based recognition for domain-specific defense terminology.

Entities are stored in the `entities` table:
    entity_type  VARCHAR(30)
    entity_value VARCHAR(200)
    confidence   FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0)

Usage:
    from engine.ner import extract_entities
    entities = extract_entities("Indian Army deployed troops near Ladakh")
    # [{"entity_type": "ORG", "entity_value": "Indian Army", "confidence": 0.85}, ...]
"""
from __future__ import annotations

import re
import threading
from typing import Any

from common.logger import get_logger

logger = get_logger(__name__)

# Default model — lightweight English model for Stage 1 MVP
DEFAULT_MODEL: str = "en_core_web_sm"

# Heuristic / default confidence scores required by the Stage 1 output contract.
# NOTE: Standard spaCy pipelines (such as en_core_web_sm) output categorical entity spans
# without native probability estimates. These values represent contract-fulfilling heuristic
# defaults (range 0.0 to 1.0), not genuine statistical model probabilities.
DEFAULT_PATTERN_CONFIDENCE: float = 0.95
DEFAULT_SPACY_CONFIDENCE: float = 0.85

# Entity types relevant to defence OSINT (preserved from original specification)
ENTITY_TYPES = {
    "LOCATION": "GPE",      # Geopolitical entities (countries, cities, states)
    "ORG": "ORG",           # Organizations (armies, agencies, militant groups)
    "PERSON": "PERSON",     # Named individuals
    "WEAPON": "PRODUCT",    # Weapons systems, missiles, aircraft
    "EVENT": "EVENT",       # Named military operations, exercises
}

# Target entity types accepted in Raksha AI
VALID_ENTITY_TYPES: set[str] = {"LOCATION", "ORG", "PERSON", "WEAPON", "EVENT"}

# Mapping from standard spaCy entity labels to Raksha AI entity types
SPACY_TO_ENTITY_TYPE: dict[str, str] = {
    "GPE": "LOCATION",      # Countries, cities, states
    "LOC": "LOCATION",      # Non-GPE locations, mountain ranges, bodies of water
    "FAC": "LOCATION",      # Buildings, airports, military installations
    "ORG": "ORG",           # Companies, military agencies, institutions
    "PERSON": "PERSON",     # People, commanders, officials
    "EVENT": "EVENT",       # Named military operations, exercises, battles
}

# Generic weapon / defense equipment indicators used to conservatively gate PRODUCT entities
WEAPON_INDICATORS: set[str] = {
    "missile", "missiles", "rocket", "rockets", "torpedo", "torpedoes",
    "bomb", "bombs", "warhead", "warheads", "icbm", "cruise",
    "tank", "tanks", "howitzer", "howitzers", "artillery", "cannon",
    "gun", "guns", "rifle", "rifles", "carbine", "carbines",
    "fighter", "fighters", "bomber", "bombers", "interceptor", "interceptors",
    "jet", "jets", "aircraft", "helicopter", "helicopters",
    "uav", "uavs", "drone", "drones", "submarine", "submarines",
    "frigate", "frigates", "destroyer", "destroyers", "corvette", "corvettes",
    "carrier", "carriers", "warship", "warships", "cruiser", "cruisers",
    "radar", "radars", "sonar", "launcher", "launchers", "interceptor",
}

# Known weapon designations and defense platforms for conservative PRODUCT matching
WEAPON_DESIGNATION_PATTERN = re.compile(
    r"\b(Rafale|Tejas|Sukhoi|Su-\d+|MiG-\d+|Mirage|Apache|Chinook|Kamov|"
    r"Agni|Prithvi|BrahMos|Akash|Nag|Helina|Pinaka|S-400|Barak|"
    r"INS\s+[A-Z][a-z]+|Arjun|T-90|T-72|K9\s+Vajra|Vikrant|Vikramaditya|"
    r"MQ-9|Predator|Reaper|Bayraktar|Heron|Searcher|Rudra|LCH|ALH)\b",
    re.IGNORECASE,
)

# Domain-specific defense patterns for terms spaCy might miss or misclassify.
# LoC/LOC and LAC require explicit acronym casing or the full phrase to avoid matching lowercase words.
DEFENSE_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r"\b(?:(?i:Line of Actual Control)|LAC)\b"), "LOCATION", DEFAULT_PATTERN_CONFIDENCE),
    (re.compile(r"\b(?:(?i:Line of Control)|LoC|LOC)\b"), "LOCATION", DEFAULT_PATTERN_CONFIDENCE),
    (re.compile(r"\b(?:Siachen(?:\s+Glacier)?)\b", re.IGNORECASE), "LOCATION", DEFAULT_PATTERN_CONFIDENCE),
    (re.compile(r"\b(?:BrahMos|Brahmos)\b", re.IGNORECASE), "WEAPON", DEFAULT_PATTERN_CONFIDENCE),
    (
        re.compile(
            r"\b(?:(?i:Defence Research and Development Organisation|Defense Research and Development Organisation)|DRDO)\b"
        ),
        "ORG",
        DEFAULT_PATTERN_CONFIDENCE,
    ),
    (re.compile(r"\b(?:Agni(?:-[IVX]+|-P)?)\b"), "WEAPON", DEFAULT_PATTERN_CONFIDENCE),
]

# Global model cache: {model_name: spacy_Language_instance}
_MODEL_CACHE: dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()


# =====================================================================
# Exception Hierarchy
# =====================================================================
class NERError(Exception):
    """Base exception for NER errors in Raksha AI."""


class DependencyError(NERError):
    """Raised when required NLP libraries (spacy) are missing."""


class ModelLoadError(NERError):
    """Raised when spaCy model loading fails."""


# =====================================================================
# Helper Utilities
# =====================================================================
def _is_weapon_product(text: str) -> bool:
    """
    Conservatively evaluate whether a spaCy PRODUCT entity represents defense weaponry.

    Unrelated consumer or commercial products (e.g. iPhone, PlayStation, Windows)
    are excluded from the defense-specific WEAPON category.
    """
    if WEAPON_DESIGNATION_PATTERN.search(text):
        return True

    words = {w.lower() for w in re.findall(r"\b[A-Za-z-]+\b", text)}
    return bool(words & WEAPON_INDICATORS)


# =====================================================================
# Model Loading & Cache Management
# =====================================================================
def _load_model(model_name: str) -> Any:
    """
    Load a spaCy model by name.

    Imports spacy lazily so importing this module does not fail
    in environments where spacy has not yet been installed.
    """
    try:
        import spacy
    except ImportError as exc:
        raise DependencyError(
            f"Required library 'spacy' is not installed: {exc}"
        ) from exc

    try:
        logger.info("Loading spaCy model '%s'...", model_name)
        model = spacy.load(model_name)
        logger.info("Successfully loaded spaCy model '%s'", model_name)
        return model
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load spaCy model '{model_name}': {exc}"
        ) from exc


def _get_or_load_model(model_name: str = DEFAULT_MODEL) -> Any:
    """
    Retrieve spaCy model from cache, or load lazily with thread safety.
    """
    if model_name is None or not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-empty string")

    clean_model_name = model_name.strip()

    if clean_model_name in _MODEL_CACHE:
        return _MODEL_CACHE[clean_model_name]

    with _CACHE_LOCK:
        if clean_model_name in _MODEL_CACHE:
            return _MODEL_CACHE[clean_model_name]

        model = _load_model(clean_model_name)
        _MODEL_CACHE[clean_model_name] = model
        return model


def clear_ner_cache() -> None:
    """Clear cached spaCy models from memory."""
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()
        logger.info("NER model cache cleared.")


def get_cached_models() -> list[str]:
    """Return a list of currently loaded model names in cache."""
    with _CACHE_LOCK:
        return list(_MODEL_CACHE.keys())


# =====================================================================
# Public Entity Extraction API
# =====================================================================
def extract_entities(text: str, model_name: str = DEFAULT_MODEL) -> list[dict]:
    """
    Extract named entities from article text.

    Args:
        text: Article text (English, pre-translated if needed).
        model_name: spaCy model identifier (default: en_core_web_sm).

    Returns:
        List of dicts: [{"entity_type": str, "entity_value": str, "confidence": float}]
        where entity_type is one of: LOCATION, ORG, PERSON, WEAPON, EVENT.

    Raises:
        ValueError: If input text or model_name is invalid.
        DependencyError: If spacy is not installed.
        ModelLoadError: If the spaCy model cannot be loaded.
        NERError: If text processing fails.
    """
    # 1. Validate input text
    if text is None or not isinstance(text, str):
        raise ValueError("Input text must be a string")

    # Clean whitespace; empty/whitespace-only text yields no entities
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    # 2. Validate model_name
    if model_name is None or not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-empty string")

    clean_model_name = model_name.strip()

    # 3. Lazily load spaCy model
    nlp = _get_or_load_model(clean_model_name)

    # 4. Process text with spaCy
    try:
        doc = nlp(cleaned_text)
    except Exception as exc:
        raise NERError(
            f"Failed to process text with spaCy model '{clean_model_name}': {exc}"
        ) from exc

    entities: list[dict] = []
    # Deduplication set tracks (entity_type, normalized_value) so that entities in
    # different categories (e.g. identical text in both WEAPON and PERSON) are not merged.
    seen_entities: set[tuple[str, str]] = set()

    # 5. Extract domain-specific defense terminology (curated patterns)
    for pattern, entity_type, confidence in DEFENSE_PATTERNS:
        for match in pattern.finditer(cleaned_text):
            matched_value = match.group(0).strip()
            norm_value = matched_value.lower()
            key = (entity_type, norm_value)

            if key not in seen_entities:
                seen_entities.add(key)
                if "siachen" in norm_value:
                    seen_entities.add((entity_type, "siachen"))
                entities.append({
                    "entity_type": entity_type,
                    "entity_value": matched_value,
                    "confidence": confidence,
                })

    # 6. Extract general entities via spaCy model
    for ent in doc.ents:
        ent_value = ent.text.strip()
        norm_value = ent_value.lower()

        if not ent_value:
            continue

        # Determine target entity type
        if ent.label_ == "PRODUCT":
            # Conservatively classify PRODUCT as WEAPON only if it matches defense/military terms
            if _is_weapon_product(ent_value):
                mapped_type = "WEAPON"
            else:
                continue
        else:
            mapped_type = SPACY_TO_ENTITY_TYPE.get(ent.label_)
            if mapped_type is None:
                continue

        # Category-aware deduplication: if the exact (entity_type, norm_value) was
        # already captured (e.g. by a higher-priority defense pattern), skip it.
        key = (mapped_type, norm_value)
        if key in seen_entities:
            continue

        # Assign heuristic default confidence required by Stage 1 contract.
        # If custom model/scorer explicitly provides a numeric confidence, use it.
        confidence = DEFAULT_SPACY_CONFIDENCE
        if hasattr(ent, "confidence"):
            try:
                conf_val = float(ent.confidence)
                if 0.0 <= conf_val <= 1.0:
                    confidence = conf_val
            except (TypeError, ValueError):
                pass

        seen_entities.add(key)
        entities.append({
            "entity_type": mapped_type,
            "entity_value": ent_value,
            "confidence": confidence,
        })

    return entities
