"""
Event Classifier — classifies articles into canonical defence event categories.
Owner: Ary
Stage: 1 (Evaluation & Baseline Model) / Stage 2 (Production Pipeline)

Classifies each article into one of the canonical EVENT_TYPES defined in common/constants.py:
    border_incident, cyber_attack, terror_activity, diplomatic,
    disinformation, military_movement, naval, aerial, nuclear, general

Uses a scikit-learn TF-IDF Multinomial Naive Bayes baseline pipeline
for Stage 1 with predicted class probability scoring, lazy model loading, thread-safe caching, and support for HuggingFace
zero-shot classification when transformers dependencies are installed.

Usage:
    from engine.classifier import classify_event
    result = classify_event("Indian Navy conducts exercise in Arabian Sea")
    # {"event_type": "naval", "confidence": 0.87}
"""
from __future__ import annotations

import threading
from typing import Any

from common.constants import EVENT_TYPES
from common.logger import get_logger

logger = get_logger(__name__)

# Canonical event categories (enforced against common/constants.py)
CANONICAL_EVENT_TYPES: list[str] = list(EVENT_TYPES)

# Default model identifier for Stage 1 baseline
DEFAULT_MODEL: str = "tfidf-multinomial-nb"

# Global model cache: {model_name: model_instance}
_MODEL_CACHE: dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()

# =====================================================================
# Canonical Training Exemplars for Stage 1 Baseline (50 examples, 5 per class)
# Distinct from evaluation test data to avoid data leakage.
# =====================================================================
TRAINING_EXEMPLARS: list[tuple[str, str]] = [
    # border_incident
    ("border clash between soldiers along the Line of Actual Control", "border_incident"),
    ("ceasefire violation and exchange of heavy firing across the LoC", "border_incident"),
    ("troops face off during border patrol in disputed mountain territory", "border_incident"),
    ("infiltration attempt thwarted along the international border fence", "border_incident"),
    ("border skirmish leaves personnel injured during standoff at forward post", "border_incident"),

    # cyber_attack
    ("state sponsored hackers launch ransomware attack on defense networks", "cyber_attack"),
    ("critical infrastructure suffers distributed denial of service DDoS attack", "cyber_attack"),
    ("cyber security advisory warns of phishing campaign spreading trojan malware", "cyber_attack"),
    ("data breach exposes sensitive files after network hacking intrusion", "cyber_attack"),
    ("malicious spyware targets government agency servers and databases", "cyber_attack"),

    # terror_activity
    ("security forces eliminate terrorists in fierce gunfight encounter", "terror_activity"),
    ("improvised explosive device IED blast targets security convoy", "terror_activity"),
    ("cordon and search operation leads to capture of militant hideout", "terror_activity"),
    ("terrorist group claims responsibility for ambush on patrol party", "terror_activity"),
    ("counter insurgency operation neutralises active militants in valley", "terror_activity"),

    # diplomatic
    ("foreign ministers hold bilateral talks to resolve regional tensions", "diplomatic"),
    ("diplomatic summit concludes with joint statement on peace and cooperation", "diplomatic"),
    ("ambassador presents credentials during delegation meeting on foreign policy", "diplomatic"),
    ("peace negotiations continue with special envoys drafting ceasefire pact", "diplomatic"),
    ("ministry of external affairs issues diplomatic protest against foreign policy violation", "diplomatic"),

    # disinformation
    ("propaganda campaign spreads fabricated rumors and fake news narratives", "disinformation"),
    ("deepfake video circulates on social media as part of information warfare", "disinformation"),
    ("fact check debunks coordinated social media bot network spreading falsehoods", "disinformation"),
    ("hostile psychological operations use manipulated footage to deceive public", "disinformation"),
    ("coordinated disinformation campaign detected spreading false claims about military", "disinformation"),

    # military_movement
    ("convoy of armored vehicles and troops deployed to forward battle positions", "military_movement"),
    ("mechanized infantry division mobilizes heavy equipment to northern frontier", "military_movement"),
    ("military repositioning of tank regiments and artillery units to border sector", "military_movement"),
    ("rapid deployment exercise moves combat units to frontline defense locations", "military_movement"),
    ("strategic buildup of armed forces and logistical troop convoys observed", "military_movement"),

    # naval
    ("navy warship intercepts hijacked vessel and rescues crew in high seas", "naval"),
    ("aircraft carrier and guided missile destroyers conduct maritime fleet drills", "naval"),
    ("submarine completes deep sea patrol in international maritime corridor", "naval"),
    ("anti-submarine warfare frigate carries out joint naval maneuvers in ocean", "naval"),
    ("maritime security operations patrol territorial waters and prevent piracy", "naval"),

    # aerial
    ("fighter jets scrambled after unidentified aircraft violates national airspace", "aerial"),
    ("combat aircraft conduct high altitude air defense patrol sortie over sector", "aerial"),
    ("surveillance drone intercepted and shot down by air defense radar battery", "aerial"),
    ("air force pilots carry out precision bombing drills at tactical range", "aerial"),
    ("airborne warning and control aircraft monitors suspicious aerial activity", "aerial"),

    # nuclear
    ("test flight of nuclear capable intercontinental ballistic missile conducted", "nuclear"),
    ("strategic forces command carries out deterrence missile launch test", "nuclear"),
    ("atomic energy commission reports on uranium enrichment and nuclear warheads", "nuclear"),
    ("second strike nuclear deterrence capability reinforced with ballistic launch", "nuclear"),
    ("flight test of nuclear delivery system validates strategic weapon range", "nuclear"),

    # general
    ("defense ministry approves annual budget increase for military modernization", "general"),
    ("parliamentary standing committee reviews defense procurement and equipment", "general"),
    ("welfare pensions and recruitment policy reviewed for armed forces veterans", "general"),
    ("indigenous defense manufacturing corridor attracts industrial investments", "general"),
    ("annual armed forces parade showcases defense equipment and public service", "general"),
]


# =====================================================================
# Exception Hierarchy
# =====================================================================
class ClassifierError(Exception):
    """Base exception for event classification errors in Raksha AI."""


class DependencyError(ClassifierError):
    """Raised when required machine learning libraries are missing."""


class ModelLoadError(ClassifierError):
    """Raised when classifier model loading or initialization fails."""


class InferenceError(ClassifierError):
    """Raised when event classification prediction fails."""


# =====================================================================
# Model Loading & Cache Management
# =====================================================================
def _build_baseline_pipeline() -> Any:
    """
    Construct and train the TF-IDF Multinomial Naive Bayes pipeline with probability scoring.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise DependencyError(
            f"Required library 'scikit-learn' is not installed: {exc}"
        ) from exc

    try:
        texts = [item[0] for item in TRAINING_EXEMPLARS]
        labels = [item[1] for item in TRAINING_EXEMPLARS]

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", MultinomialNB(alpha=0.1)),
        ])
        pipeline.fit(texts, labels)
        return pipeline
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to initialize baseline classifier pipeline: {exc}"
        ) from exc


def _load_model(model_name: str) -> Any:
    """
    Load or construct a classifier model by name.
    """
    logger.info("Loading event classifier model '%s'...", model_name)

    if model_name in ("tfidf-multinomial-nb", "default", DEFAULT_MODEL):
        model = _build_baseline_pipeline()
        logger.info("Successfully loaded baseline event classifier model '%s'", model_name)
        return model

    # If a HuggingFace zero-shot model is requested (e.g. facebook/bart-large-mnli)
    try:
        from transformers import pipeline as hf_pipeline
    except ImportError as exc:
        raise DependencyError(
            f"HuggingFace model '{model_name}' requested but 'transformers' is not installed: {exc}"
        ) from exc

    try:
        model = hf_pipeline("zero-shot-classification", model=model_name)
        logger.info("Successfully loaded HuggingFace classifier '%s'", model_name)
        return model
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load HuggingFace model '{model_name}': {exc}"
        ) from exc


def _get_or_load_model(model_name: str = DEFAULT_MODEL) -> Any:
    """
    Retrieve classifier model from cache, or load lazily with thread safety.
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


def clear_classifier_cache() -> None:
    """Clear cached classifier models from memory."""
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()
        logger.info("Classifier model cache cleared.")


def get_cached_models() -> list[str]:
    """Return a list of currently loaded model names in cache."""
    with _CACHE_LOCK:
        return list(_MODEL_CACHE.keys())


# =====================================================================
# Public Event Classification API
# =====================================================================
def classify_event(text: str, model_name: str = DEFAULT_MODEL) -> dict:
    """
    Classify article text into a single canonical defence event type.

    Args:
        text: Article headline or body text (English, pre-translated).
        model_name: Identifier of model to use (default: tfidf-multinomial-nb).

    Returns:
        dict: {"event_type": str, "confidence": float}
        where event_type is one of CANONICAL_EVENT_TYPES, and confidence is in [0.0, 1.0].

    Raises:
        ValueError: If text or model_name is empty, whitespace-only, None, or invalid type.
        DependencyError: If required ML libraries are missing.
        ModelLoadError: If the model cannot be loaded.
        InferenceError: If prediction fails.
    """
    # 1. Validate input text
    if text is None or not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be a non-empty string")

    # 2. Validate model_name
    if model_name is None or not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-empty string")

    clean_text = text.strip()
    clean_model_name = model_name.strip()

    # 3. Lazily load model from cache
    model = _get_or_load_model(clean_model_name)

    # 4. Perform inference
    try:
        # Standard scikit-learn pipeline inference
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba([clean_text])[0]
            classes = model.classes_
            best_idx = int(probs.argmax())
            predicted_class = str(classes[best_idx])
            raw_confidence = float(probs[best_idx])
        # HuggingFace zero-shot classification pipeline inference
        elif callable(model):
            hf_out = model(clean_text, candidate_labels=CANONICAL_EVENT_TYPES)
            predicted_class = str(hf_out["labels"][0])
            raw_confidence = float(hf_out["scores"][0])
        else:
            raise TypeError(f"Unrecognized model object type: {type(model)}")
    except Exception as exc:
        raise InferenceError(
            f"Failed to classify event text using model '{clean_model_name}': {exc}"
        ) from exc

    # 5. Validate category restrictions
    if predicted_class not in CANONICAL_EVENT_TYPES:
        raise ValueError(
            f"Classifier returned non-canonical category '{predicted_class}'. "
            f"Expected one of: {CANONICAL_EVENT_TYPES}"
        )

    # 6. Validate confidence score bounds
    confidence = max(0.0, min(1.0, round(raw_confidence, 4)))

    return {
        "event_type": predicted_class,
        "confidence": confidence,
    }
