"""
Translator module — translates non-English articles to English.
Owner: Ary
Stage: 2

Uses Helsinki-NLP/opus-mt models for:
  - Urdu → English  (Helsinki-NLP/opus-mt-ur-en)
  - Chinese → English (Helsinki-NLP/opus-mt-zh-en)
  - Hindi → English (Helsinki-NLP/opus-mt-hi-en)

Usage:
    from engine.translator import translate

    result = translate(text=article_text, source_lang=source_lang)
    if result.is_success:
        # Translation succeeded (Urdu/Chinese/Hindi -> English)
        english_text = str(result)
    elif result.is_skipped:
        # Already in English or empty; retain original text for downstream NLP
        english_text = str(result)  # (or result.original_text)
    else:
        # Translation failed: do NOT treat foreign text as English!
        logger.error("Translation failed: %s", result.error)
        english_text = None  # Quarantine or flag translation failure

Operational Handling Guidelines:
    - English source articles (or empty text) result in result.is_skipped == True.
      The calling pipeline must retain the original English text for downstream
      analysis (summarization, entity extraction, threat classification).
      A skipped English translation must NEVER be interpreted as an instruction
      to discard the article.
    - Failed non-English translations result in result.is_failed == True.
      The original foreign-language text must NEVER be treated as English or passed
      to English-only downstream NLP models.
"""
from __future__ import annotations

import re
import threading
from typing import Any, Optional

from common.logger import get_logger

logger = get_logger(__name__)

# Translation Status Constants
STATUS_SUCCESS = "success"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"

# Supported MarianMT models mapping source language (ISO 639-1) -> HuggingFace model identifier
SUPPORTED_MODELS: dict[str, str] = {
    "ur": "Helsinki-NLP/opus-mt-ur-en",
    "zh": "Helsinki-NLP/opus-mt-zh-en",
    "hi": "Helsinki-NLP/opus-mt-hi-en",
}

# Maximum token chunk size for MarianMT (model max position embedding is 512)
MAX_CHUNK_TOKENS: int = 450
MAX_SEQUENCE_LENGTH: int = 512

# Sentence boundary delimiter regex (handles Hindi, Urdu, Chinese, and standard punctuation)
SENTENCE_SPLIT_PATTERN: re.Pattern = re.compile(
    r"(?<=[。！？；।॥۔؟!?])\s*|(?<=\.)\s+|\n+"
)

# Global model and tokenizer cache: {source_lang: (tokenizer, model)}
_MODEL_CACHE: dict[str, tuple[Any, Any]] = {}
_CACHE_LOCK = threading.Lock()


# =====================================================================
# Exception Hierarchy
# =====================================================================
class TranslationError(Exception):
    """Base exception for translation errors in Raksha AI."""


class DependencyError(TranslationError):
    """Raised when required NLP libraries (transformers, torch, sentencepiece) are missing."""


class UnsupportedLanguageError(TranslationError):
    """Raised when an unsupported source or target language code is provided."""


class ModelLoadError(TranslationError):
    """Raised when model or tokenizer loading fails."""


class InferenceError(TranslationError):
    """Raised when model translation generation or decoding fails."""


# =====================================================================
# Structured String Output
# =====================================================================
class TranslationResult(str):
    """
    Subclass of `str` containing translation output and operational metadata.

    Inherits from `str` to support ordinary string operations:
        result = translate(...)
        print(len(result), result.upper(), f"text: {result}")

    Callers should note that the public return type and behavior include
    status metadata rather than returning a plain str primitive. The calling
    pipeline must inspect these fields to distinguish operational states:
        - Successful translation: result.is_success == True
        - Skipped translation:    result.is_skipped == True (e.g. English source or empty text;
                                  caller must retain original text for downstream NLP)
        - Failed translation:     result.is_failed == True  (with result.error populated;
                                  caller must NOT treat foreign text as English)
    """

    status: str
    source_lang: str
    target_lang: str
    error: Optional[str]
    original_text: str

    def __new__(
        cls,
        text: str,
        status: str,
        source_lang: str,
        target_lang: str = "en",
        error: Optional[str] = None,
        original_text: Optional[str] = None,
    ):
        instance = super().__new__(cls, text)
        instance.status = status
        instance.source_lang = source_lang
        instance.target_lang = target_lang
        instance.error = error
        instance.original_text = original_text if original_text is not None else text
        return instance

    @property
    def is_success(self) -> bool:
        """True if the text was actively and successfully translated."""
        return self.status == STATUS_SUCCESS

    @property
    def is_skipped(self) -> bool:
        """True if translation was skipped (source already English, matching target, or empty)."""
        return self.status == STATUS_SKIPPED

    @property
    def is_failed(self) -> bool:
        """True if translation failed due to an error, missing dependency, or unsupported language."""
        return self.status == STATUS_FAILED


# =====================================================================
# Model Loading & Cache Management
# =====================================================================
def _load_model_and_tokenizer(model_name: str) -> tuple[Any, Any]:
    """
    Load MarianMT tokenizer and model for the specified HuggingFace model name.

    Imports transformers and torch lazily so importing this module does not fail
    in environments where NLP dependencies have not yet been installed.
    """
    try:
        import torch
        from transformers import MarianMTModel, MarianTokenizer
    except ImportError as exc:
        raise DependencyError(
            f"Required NLP libraries ('transformers', 'torch') are not installed: {exc}"
        ) from exc

    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading translation model '%s' on device '%s'...", model_name, device)

        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name).to(device)
        model.eval()

        logger.info("Successfully loaded and initialized translation model '%s'", model_name)
        return tokenizer, model
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load or initialize translation model '{model_name}': {exc}"
        ) from exc


def _get_or_load_model(source_lang: str) -> tuple[Any, Any]:
    """
    Retrieve model and tokenizer from cache, or load lazily with thread safety.
    """
    if source_lang in _MODEL_CACHE:
        return _MODEL_CACHE[source_lang]

    with _CACHE_LOCK:
        # Double-check pattern after acquiring lock
        if source_lang in _MODEL_CACHE:
            return _MODEL_CACHE[source_lang]

        model_name = SUPPORTED_MODELS[source_lang]
        tokenizer, model = _load_model_and_tokenizer(model_name)
        _MODEL_CACHE[source_lang] = (tokenizer, model)
        return tokenizer, model


def clear_model_cache() -> None:
    """Clear cached models and tokenizers from memory."""
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()
        logger.info("Translation model cache cleared.")


def get_cached_languages() -> list[str]:
    """Return a list of currently loaded language codes in cache."""
    with _CACHE_LOCK:
        return list(_MODEL_CACHE.keys())


# =====================================================================
# Token-Aware Chunking
# =====================================================================
def _count_tokens(text: str, tokenizer: Any) -> int:
    """
    Return the total token count of text for the given tokenizer.
    Includes special tokens if the tokenizer supports add_special_tokens.
    """
    try:
        return len(tokenizer.encode(text, add_special_tokens=True))
    except TypeError:
        return len(tokenizer.encode(text))


def _split_long_sentence(sentence: str, tokenizer: Any, max_tokens: int) -> list[str]:
    """
    Split a single sentence exceeding max_tokens into subchunks.

    Verifies the actual token count after decoding each candidate slice to
    ensure the prepared subchunk strictly stays within the safe token budget
    when passed to model inference (including special tokens).
    Partitions the content token sequence into contiguous slices without omissions;
    reassembled text retains words verified by the tokenizer model.
    """
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError(f"max_tokens must be a positive integer, got {max_tokens!r}")

    try:
        token_ids = tokenizer.encode(sentence, add_special_tokens=False)
    except TypeError:
        token_ids = tokenizer.encode(sentence)

    num_tokens = len(token_ids)
    if _count_tokens(sentence, tokenizer) <= max_tokens:
        return [sentence.strip()] if sentence.strip() else []

    if num_tokens == 0:
        if not sentence.strip():
            return []
        raise ValueError(
            f"Sentence produced zero content token IDs but exceeds token budget "
            f"(max_tokens={max_tokens}): '{sentence.strip()}'"
        )

    subchunks: list[str] = []
    start = 0
    while start < num_tokens:
        end = min(start + max_tokens, num_tokens)
        sub_ids = token_ids[start:end]
        try:
            sub_text = tokenizer.decode(sub_ids, skip_special_tokens=True).strip()
        except TypeError:
            sub_text = tokenizer.decode(sub_ids).strip()

        # If re-tokenizing decoded text exceeds max_tokens (due to special tokens
        # or decoding boundaries), iteratively shrink end until it fits within budget
        while end > start + 1 and _count_tokens(sub_text, tokenizer) > max_tokens:
            end -= 1
            sub_ids = token_ids[start:end]
            try:
                sub_text = tokenizer.decode(sub_ids, skip_special_tokens=True).strip()
            except TypeError:
                sub_text = tokenizer.decode(sub_ids).strip()

        # Explicitly verify that decoded sub_text strictly fits the token budget
        actual_tokens = _count_tokens(sub_text, tokenizer)
        if actual_tokens > max_tokens:
            raise ValueError(
                f"Decoded token slice ({actual_tokens} tokens) exceeds token budget "
                f"(max_tokens={max_tokens}) even at minimum slice size: '{sub_text}'"
            )

        if sub_text:
            subchunks.append(sub_text)
        start = end

    return subchunks


def _chunk_text(text: str, tokenizer: Any, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
    """
    Split text into token-aware chunks that fit within max_tokens for MarianMT.

    Preserves sentence boundaries across Hindi, Urdu, Chinese, and Latin scripts
    where possible. Re-tokenizes the complete candidate chunk after joining sentences
    to ensure the combined input passed to model inference stays strictly within the
    configured safe token budget (including special tokens).
    Falls back to verified token slicing for individual sentences exceeding max_tokens.
    """
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError(f"max_tokens must be a positive integer, got {max_tokens!r}")
    raw_sentences = SENTENCE_SPLIT_PATTERN.split(text)
    sentences = [s.strip() for s in raw_sentences if s and s.strip()]

    if not sentences:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current_sentences: list[str] = []

    for sentence in sentences:
        sentence_tokens = _count_tokens(sentence, tokenizer)

        # Handle edge case: single sentence longer than max_tokens
        if sentence_tokens > max_tokens:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []

            # Sub-chunk the long sentence by verified token slices
            sentence_subchunks = _split_long_sentence(sentence, tokenizer, max_tokens)
            chunks.extend(sentence_subchunks)
            continue

        # Check candidate chunk: re-tokenize complete candidate chunk after joining
        candidate_sentences = current_sentences + [sentence]
        candidate_text = " ".join(candidate_sentences)
        candidate_tokens = _count_tokens(candidate_text, tokenizer)

        if candidate_tokens <= max_tokens:
            current_sentences = candidate_sentences
        else:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
            current_sentences = [sentence]

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


# =====================================================================
# Public Translation API
# =====================================================================
def _translate_chunk(chunk: str, tokenizer: Any, model: Any) -> str:
    """
    Translate a single token-bounded chunk using the loaded model and tokenizer.
    """
    import torch

    inputs = tokenizer(
        chunk,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=MAX_SEQUENCE_LENGTH,
    )

    if hasattr(model, "device") and model.device is not None:
        inputs = {
            k: (v.to(model.device) if hasattr(v, "to") else v)
            for k, v in inputs.items()
        }

    with torch.no_grad():
        translated_ids = model.generate(
            **inputs,
            max_length=MAX_SEQUENCE_LENGTH,
        )

    return tokenizer.decode(
        translated_ids[0],
        skip_special_tokens=True,
    ).strip()


def translate(
    text: str,
    source_lang: str,
    target_lang: str = "en",
) -> TranslationResult:
    """
    Translate text from source_lang to target_lang.

    Args:
        text: Input text to translate.
        source_lang: ISO 639-1 language code (e.g., 'ur', 'zh', 'hi').
        target_lang: Target language, default 'en'.

    Returns:
        TranslationResult (str subclass) with:
          - .status: "success" | "skipped" | "failed"
          - .is_success, .is_skipped, .is_failed booleans
          - .error: error description if failed, else None
          - .source_lang, .target_lang, .original_text
    """
    # Normalize input text type safely
    if text is None:
        raw_text = ""
    elif not isinstance(text, str):
        logger.warning("translate() expected string input, received %s", type(text).__name__)
        raw_text = str(text)
    else:
        raw_text = text

    # Normalize language codes
    norm_source = source_lang.strip().lower() if isinstance(source_lang, str) else ""
    norm_target = target_lang.strip().lower() if isinstance(target_lang, str) else "en"

    # 1. Validate target language first (only English is currently supported)
    # Language validation strictly precedes text emptiness checks so invalid target
    # requests fail immediately rather than returning a misleading skipped status.
    if norm_target != "en":
        err_msg = (
            f"Unsupported target language '{target_lang}'. "
            f"Only English ('en') is currently supported."
        )
        logger.warning(err_msg)
        return TranslationResult(
            raw_text,
            status=STATUS_FAILED,
            source_lang=norm_source,
            target_lang=norm_target,
            error=err_msg,
            original_text=raw_text,
        )

    # 2. Validate supported source language before checking text content or loading models
    # Valid source languages are: 'en' (pass-through) or supported MarianMT models ('ur', 'zh', 'hi')
    if norm_source != "en" and norm_source not in SUPPORTED_MODELS:
        err_msg = (
            f"Unsupported source language '{source_lang}'. "
            f"Supported languages: {list(SUPPORTED_MODELS.keys())}"
        )
        logger.warning(err_msg)
        return TranslationResult(
            raw_text,
            status=STATUS_FAILED,
            source_lang=norm_source,
            target_lang=norm_target,
            error=err_msg,
            original_text=raw_text,
        )

    # 3. Handle empty or whitespace-only input safely (SKIPPED)
    # Only skipped if the language pair was verified as valid above
    if not raw_text.strip():
        return TranslationResult(
            raw_text,
            status=STATUS_SKIPPED,
            source_lang=norm_source,
            target_lang=norm_target,
            original_text=raw_text,
        )

    # 4. Perform English-to-English pass-through (SKIPPED)
    if norm_source == "en":
        logger.debug(
            "Source language is English ('%s'); skipping translation",
            source_lang,
        )
        return TranslationResult(
            raw_text,
            status=STATUS_SKIPPED,
            source_lang=norm_source,
            target_lang=norm_target,
            original_text=raw_text,
        )

    # 5. Lazily load model and tokenizer
    try:
        tokenizer, model = _get_or_load_model(norm_source)
    except (DependencyError, ModelLoadError) as exc:
        logger.error(
            "Failed to load translation model for '%s' (%s): %s",
            norm_source,
            SUPPORTED_MODELS.get(norm_source),
            exc,
            exc_info=True,
        )
        return TranslationResult(
            raw_text,
            status=STATUS_FAILED,
            source_lang=norm_source,
            target_lang=norm_target,
            error=str(exc),
            original_text=raw_text,
        )
    except Exception as exc:
        err = ModelLoadError(
            f"Unexpected error loading translation model for '{norm_source}': {exc}"
        )
        logger.error(str(err), exc_info=True)
        return TranslationResult(
            raw_text,
            status=STATUS_FAILED,
            source_lang=norm_source,
            target_lang=norm_target,
            error=str(err),
            original_text=raw_text,
        )

    # 6. Chunk text by paragraphs and sentences, then translate safely
    try:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_text) if p.strip()]
        if not paragraphs:
            return TranslationResult(
                raw_text,
                status=STATUS_SKIPPED,
                source_lang=norm_source,
                target_lang=norm_target,
                original_text=raw_text,
            )

        logger.debug(
            "Translating %d chars (%d paragraph(s)) from '%s' to '%s'",
            len(raw_text),
            len(paragraphs),
            norm_source,
            norm_target,
        )

        translated_paragraphs: list[str] = []
        for paragraph in paragraphs:
            chunks = _chunk_text(paragraph, tokenizer, max_tokens=MAX_CHUNK_TOKENS)
            translated_chunks: list[str] = []
            for chunk in chunks:
                translated_chunk = _translate_chunk(chunk, tokenizer, model)
                if translated_chunk:
                    translated_chunks.append(translated_chunk)

            if translated_chunks:
                translated_paragraphs.append(" ".join(translated_chunks).strip())

        result_str = "\n\n".join(translated_paragraphs).strip()
        if not result_str:
            err_msg = "Translation produced empty output"
            logger.warning(err_msg)
            return TranslationResult(
                raw_text,
                status=STATUS_FAILED,
                source_lang=norm_source,
                target_lang=norm_target,
                error=err_msg,
                original_text=raw_text,
            )

        return TranslationResult(
            result_str,
            status=STATUS_SUCCESS,
            source_lang=norm_source,
            target_lang=norm_target,
            original_text=raw_text,
        )

    except Exception as exc:
        err = (
            exc
            if isinstance(exc, TranslationError)
            else InferenceError(
                f"Translation inference error from '{norm_source}' to '{norm_target}': {exc}"
            )
        )
        logger.error(str(err), exc_info=True)
        return TranslationResult(
            raw_text,
            status=STATUS_FAILED,
            source_lang=norm_source,
            target_lang=norm_target,
            error=str(err),
            original_text=raw_text,
        )
