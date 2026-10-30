"""
Embedding Generator — creates 768-dim vectors for semantic similarity.
Owner: Ary
Stage: 1 (Model Selection & Vector Generation) / 2.5 (Similarity Search)

Uses sentence-transformers/all-mpnet-base-v2 to generate 768-dimensional
embeddings stored in the `article_embeddings` table via pgvector.

Usage:
    from engine.embeddings import generate_embedding
    vector = generate_embedding("Indian Army deploys troops near LAC")
    # Returns list[float] of length 768
"""
from __future__ import annotations

import math
import threading
from typing import Any

from common.logger import get_logger

logger = get_logger(__name__)

# Default model — produces 768-dim vectors matching article_embeddings.embedding VECTOR(768)
DEFAULT_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM: int = 768

# Global model cache: {model_name: SentenceTransformer_instance}
_MODEL_CACHE: dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()


# =====================================================================
# Exception Hierarchy
# =====================================================================
class EmbeddingError(Exception):
    """Base exception for embedding generator errors in Raksha AI."""


class DependencyError(EmbeddingError):
    """Raised when required NLP libraries (sentence-transformers, torch) are missing."""


class ModelLoadError(EmbeddingError):
    """Raised when embedding model loading fails."""


class InferenceError(EmbeddingError):
    """Raised when vector encoding or output conversion fails."""


# =====================================================================
# Model Loading & Cache Management
# =====================================================================
def _load_model(model_name: str) -> Any:
    """
    Load a SentenceTransformer model by name.

    Imports sentence_transformers lazily so importing this module does not fail
    in environments where NLP dependencies have not yet been installed.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise DependencyError(
            f"Required library 'sentence-transformers' is not installed: {exc}"
        ) from exc

    try:
        logger.info("Loading embedding model '%s'...", model_name)
        model = SentenceTransformer(model_name)
        logger.info("Successfully loaded embedding model '%s'", model_name)
        return model
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load or initialize embedding model '{model_name}': {exc}"
        ) from exc


def _get_or_load_model(model_name: str = DEFAULT_MODEL) -> Any:
    """
    Retrieve model from cache, or load lazily with thread safety.
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


def clear_embedding_cache() -> None:
    """Clear cached embedding models from memory."""
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()
        logger.info("Embedding model cache cleared.")


def get_cached_models() -> list[str]:
    """Return a list of currently loaded model names in cache."""
    with _CACHE_LOCK:
        return list(_MODEL_CACHE.keys())


# =====================================================================
# Public Embedding API
# =====================================================================
def generate_embedding(text: str, model_name: str = DEFAULT_MODEL) -> list[float]:
    """
    Generate a 768-dimensional vector embedding for the given text.

    Args:
        text: Input text (English, pre-translated).
        model_name: HuggingFace model identifier (default: all-mpnet-base-v2).

    Returns:
        List of 768 finite Python floats.

    Raises:
        ValueError: If input text or model_name is invalid, if vector dimension != 768,
            or if the vector contains non-finite values (NaN, positive/negative infinity).
        DependencyError: If sentence-transformers is not installed.
        ModelLoadError: If the model cannot be loaded.
        InferenceError: If encoding fails or model output cannot be converted to floats.
    """
    # 1. Validate input text safely
    if text is None or not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be a non-empty string")

    # 2. Validate model_name safely
    if model_name is None or not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("model_name must be a non-empty string")

    clean_model_name = model_name.strip()

    # 3. Lazily load model from cache
    model = _get_or_load_model(clean_model_name)

    # 4. Generate raw embedding
    try:
        raw_output = model.encode(text.strip())
    except Exception as exc:
        raise InferenceError(
            f"Failed to encode text with model '{clean_model_name}': {exc}"
        ) from exc

    # 5. Convert raw model output structure to a list
    try:
        if hasattr(raw_output, "tolist") and callable(raw_output.tolist):
            raw_list = raw_output.tolist()
        elif isinstance(raw_output, (list, tuple)):
            raw_list = list(raw_output)
        else:
            raw_list = list(raw_output)
    except Exception as exc:
        raise InferenceError(
            f"Failed to convert embedding output structure from model '{clean_model_name}': {exc}"
        ) from exc

    # 6. Convert all elements to native Python floats
    try:
        vector = [float(val) for val in raw_list]
    except (TypeError, ValueError) as exc:
        raise InferenceError(
            f"Failed to convert embedding output values to float from model '{clean_model_name}': {exc}"
        ) from exc

    # 7. Validate exact dimension (768 for schema compatibility)
    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, got {len(vector)} "
            f"from model '{clean_model_name}'"
        )

    # 8. Reject vectors containing NaN, +Inf, or -Inf
    for idx, val in enumerate(vector):
        if not math.isfinite(val):
            raise ValueError(
                f"Embedding vector contains non-finite value ({val}) at index {idx} "
                f"from model '{clean_model_name}'"
            )

    return vector


def find_similar_articles(embedding: list[float], threshold: float = 0.75, limit: int = 10) -> list[dict]:
    """
    Find similar articles using pgvector cosine similarity.

    Args:
        embedding: Query vector
        threshold: Minimum cosine similarity (default 0.75)
        limit: Max results to return

    Returns:
        List of {"article_id": int, "similarity": float}
    """
    raise NotImplementedError("Similarity search not yet implemented — Stage 2.5")
