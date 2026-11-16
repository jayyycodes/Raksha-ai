"""
Uploaded Document NLP Pipeline — Raksha AI Stage 3 Solid
Floor 2 — Language & Knowledge Agents
Owner: Ary

Enables uploaded documents (PDF, CSV, TXT) to enter the Language & Knowledge
pipeline safely and consistently:
    1. Text extraction & page/section mapping (PDF, CSV, TXT)
    2. Noisy-text cleanup (strips encoding glitches, headers/footers, preserves intelligence markers)
    3. Sentence-boundary aware long-document chunking with configurable overlap
    4. Language detection & translation via TranslationAgent (where appropriate)
    5. Entity extraction via ExtractionAgent
    6. Canonical entity resolution via ResolutionAgent (strictly workspace-isolated)
    7. Cross-chunk entity deduplication
    8. Event threading via ThreadingAgent
    9. Mandatory provenance enforcement: source_type='user_upload', workspace_id attribution
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import io
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from agents.extraction.agent import ExtractionAgent
from agents.resolution.agent import ResolutionAgent
from agents.resolution.feedback import normalize_workspace_id
from agents.threading.agent import ThreadingAgent
from agents.translation.agent import TranslationAgent
from common.logger import get_logger
from common.schemas.articles import ArticleIn, EntityOut
from common.schemas.events import EventThreadingIn
from common.schemas.provenance import ClaimStatus, Provenance, SourceType

logger = get_logger(__name__)

# Constants and limits
MAX_DOCUMENT_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
DEFAULT_CHUNK_SIZE_CHARS = 1200
DEFAULT_CHUNK_OVERLAP_CHARS = 200
MIN_CHUNK_SIZE_CHARS = 100

SUPPORTED_EXTENSIONS = {".txt", ".csv", ".pdf"}
SUPPORTED_MIME_TYPES = {
    "text/plain",
    "text/csv",
    "application/pdf",
    "application/octet-stream",  # Often sent for plain text or generic files
}

# Regex for sentence boundaries and structural breaks
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u0600-\u06FF\u0900-\u097F])")
PARAGRAPH_SPLIT_REGEX = re.compile(r"\n\s*\n")

# Common running headers / security banners to strip from noisy documents
RUNNING_HEADER_REGEX = re.compile(
    r"^(?:CONFIDENTIAL|RESTRICTED|SECRET|TOP\s+SECRET|CLASSIFIED|PAGE\s+\d+(?:\s+OF\s+\d+)?|\d+\s*/\s*\d+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class UploadNLPError(Exception):
    """Base exception for upload NLP pipeline errors."""
    pass


class UnsupportedFormatError(UploadNLPError):
    """Raised when an unsupported file format is provided."""
    pass


class EmptyDocumentError(UploadNLPError):
    """Raised when an uploaded document has no extractable text."""
    pass


class DocumentCorruptedError(UploadNLPError):
    """Raised when an uploaded document is malformed or corrupted."""
    pass


class DocumentTooLargeError(UploadNLPError):
    """Raised when an uploaded document exceeds size limits."""
    pass


class DependencyMissingError(UploadNLPError):
    """Raised when an external or optional library (such as pypdf) is missing."""
    pass


# Languages supported by the existing MarianMT translation engine in engine.translator
SUPPORTED_TRANSLATION_LANGUAGES = {"hi", "ur", "zh", "en"}

# Conservative incident indicators required to establish legitimate event evidence
INCIDENT_INDICATORS: Set[str] = {
    # Kinetic / tactical actions
    "clash", "skirmish", "standoff", "patrol", "intercept", "scrambled", "fired", "firing",
    "shelling", "ambush", "encounter", "incursion", "intrusion", "infiltration", "attack",
    "strike", "blast", "explosion", "ied", "terrorist", "militant", "casualty", "casualties",
    # Operational readiness & deployments
    "mobilization", "mobilised", "mobilized", "deployed", "deployment", "exercise", "drills",
    "air patrol", "combat air patrol", "sortie", "sorties", "test flight", "missile test",
    "flight test", "naval exercise", "surveillance", "reconnaissance", "alert", "readiness",
    # Cyber & Information operations
    "cyber attack", "malware", "ransomware", "data breach", "ddos", "espionage", "propaganda",
    # Diplomatic friction & border mechanisms
    "border talks", "corps commander", "flag meeting", "ceasefire violation", "de-escalation",
}


def evaluate_event_evidence(
    text: str,
    extracted_entities: List[Dict[str, Any]],
    event_type: str = "general",
) -> Tuple[bool, str]:
    """
    Conservative event-evidence gate to prevent ungrounded event thread creation.
    Rejects generic, administrative, or non-incident documents from spawning event threads.
    Preserves legitimate incidents even if entity extraction is partial.
    Returns: (has_event_evidence, rationale)
    """
    if not text or not text.strip():
        return False, "Empty document text; no event evidence."

    cleaned_lower = text.lower()

    # Find matching incident indicators
    matched_indicators = [
        ind for ind in INCIDENT_INDICATORS
        if re.search(r"\b" + re.escape(ind) + r"\b", cleaned_lower)
    ]

    is_specific_event_type = event_type not in ("general", "unknown", "")

    # Gate logic:
    # 1. No incident indicators and generic event classification -> reject
    if not matched_indicators and not is_specific_event_type:
        return False, "No incident indicators or specific event type detected; document is informational or administrative."

    # 2. Corroborated incident indicators present
    if matched_indicators:
        return True, f"Detected incident indicators: [{', '.join(sorted(matched_indicators)[:3])}]"

    # 3. Specific event type classified with at least one corroborating entity
    if is_specific_event_type and len(extracted_entities) >= 1:
        return True, f"Specific event type '{event_type}' with {len(extracted_entities)} corroborated entities."

    return False, "Insufficient operational evidence to establish an event thread."


def detect_document_language(text: str) -> Tuple[str, float, bool]:
    """
    Detect language using actual text features with conservative script-aware heuristics.
    Returns: (language_code, confidence, is_mixed)
    - Distinguishes Hindi (Devanagari), Urdu (Perso-Arabic), Punjabi (Gurmukhi), Bengali, and English.
    - Handles short or ambiguous text via explicit script fallback.
    - Accurately identifies mixed-language documents.
    """
    if not text or not text.strip():
        return "unknown", 0.0, False

    stripped = text.strip()

    # Count script character blocks (excluding generic punctuation like danda \u0964)
    devanagari = len(re.findall(r"[\u0904-\u0939\u0958-\u0961]", stripped))
    perso_arabic = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]", stripped))
    gurmukhi = len(re.findall(r"[\u0A05-\u0A39\u0A59-\u0A5E]", stripped))
    bengali = len(re.findall(r"[\u0985-\u09B9\u09DC-\u09DF]", stripped))
    latin = len(re.findall(r"[a-zA-Z]", stripped))
    total_letters = devanagari + perso_arabic + gurmukhi + bengali + latin

    if total_letters == 0:
        return "unknown", 0.0, False

    # Short text fallback (< 25 characters) where statistical n-gram detectors are unreliable
    if len(stripped) < 25:
        if devanagari > 0:
            return "hi", 1.0, False
        if perso_arabic > 0:
            return "ur", 1.0, False
        if gurmukhi > 0:
            return "pa", 1.0, False
        if bengali > 0:
            return "bn", 1.0, False
        if latin > 0:
            return "en", 0.8, False
        return "unknown", 0.0, False

    # Check for mixed-language text (substantial Latin + substantial Indic script)
    dominant_indic = max(devanagari, perso_arabic, gurmukhi, bengali)
    is_mixed = dominant_indic > 10 and latin > 10

    # Try statistical language detection using langdetect
    try:
        import langdetect
        langs = langdetect.detect_langs(stripped)
        top = langs[0]

        # Cross-check dominant non-Latin scripts if statistical detector misidentifies
        if devanagari > 15 and devanagari > max(gurmukhi, bengali, perso_arabic, latin):
            return "hi", top.prob if top.lang == "hi" else 0.95, is_mixed
        if gurmukhi > 15 and gurmukhi > max(devanagari, bengali, perso_arabic, latin):
            return "pa", top.prob if top.lang == "pa" else 0.95, is_mixed
        if bengali > 15 and bengali > max(devanagari, gurmukhi, perso_arabic, latin):
            return "bn", top.prob if top.lang == "bn" else 0.95, is_mixed
        if perso_arabic > 15 and perso_arabic > max(devanagari, gurmukhi, bengali, latin):
            return "ur", top.prob if top.lang == "ur" else 0.95, is_mixed

        return top.lang, top.prob, is_mixed
    except Exception:
        # Script-based deterministic fallback when langdetect encounters errors
        if devanagari > 0:
            return "hi", 0.75, is_mixed
        if perso_arabic > 0:
            return "ur", 0.75, is_mixed
        if gurmukhi > 0:
            return "pa", 0.75, is_mixed
        if bengali > 0:
            return "bn", 0.75, is_mixed
        if latin > 0:
            return "en", 0.75, is_mixed
        return "unknown", 0.0, False


@dataclass
class DocumentChunk:
    """Represents a bounded chunk of an uploaded document with full provenance."""
    chunk_id: str
    document_id: str
    text: str
    page_number: Optional[int] = None
    section_index: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentExtractionResult:
    """Container for raw extraction output before chunking and NLP inference."""
    raw_text: str
    cleaned_text: str
    format: str
    pages: Dict[int, str] = field(default_factory=dict)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    total_characters: int = 0
    cleaned_characters: int = 0


@dataclass
class UploadedDocumentAnalysis:
    """Complete structured output of the Uploaded-Document NLP pipeline."""
    document_id: str
    filename: str
    format: str
    workspace_id: str
    source_type: str = "user_upload"
    chunks: List[DocumentChunk] = field(default_factory=list)
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)
    resolved_entities: List[Dict[str, Any]] = field(default_factory=list)
    event_threads: List[Dict[str, Any]] = field(default_factory=list)
    detected_language: str = "en"
    provenance: Optional[Provenance] = None
    status: str = "success"
    warnings: List[str] = field(default_factory=list)


def clean_document_text(text: str, remove_running_headers: bool = True) -> str:
    """
    Sanitize and clean noisy document text while preserving intelligence content.
    - Strips control characters and null bytes (\x00).
    - Normalizes Unicode whitespace (including \u00a0, \r\n, \t).
    - Removes common running headers/footers (e.g. 'CONFIDENTIAL', 'PAGE X OF Y').
    - Preserves defense identifiers, military ranks, coordinates (e.g. 34.12, 77.58),
      dates (2026-11-16), and equipment names.
    """
    if not text:
        return ""

    # 1. Remove null bytes and non-printable control characters (except newline, tab)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 2. Normalize Windows/Mac line endings
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Normalize non-breaking spaces and unusual unicode spaces to standard space
    cleaned = re.sub(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]", " ", cleaned)

    # 4. Strip repeated running headers/footers if requested
    if remove_running_headers:
        cleaned = RUNNING_HEADER_REGEX.sub("", cleaned)

    # 5. Collapse 3+ consecutive newlines to double newlines (paragraph boundary)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 6. Collapse excessive horizontal spaces on each line while preserving indentation
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    cleaned = "\n".join(line for line in lines if line)

    return cleaned.strip()


def chunk_document_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE_CHARS,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    page_map: Optional[Dict[int, str]] = None,
    document_id: str = "doc_upload",
) -> List[DocumentChunk]:
    """
    Split long document text into overlapping chunks using sentence-aware boundaries.
    Preserves document and page provenance where available.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str for text, got {type(text).__name__}")
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be a positive integer, got {chunk_size}")
    if chunk_overlap < 0:
        raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})")

    chunks: List[DocumentChunk] = []

    # If page_map is provided (e.g. from a PDF), chunk per page while preserving page numbers
    if page_map and len(page_map) > 0:
        chunk_idx = 0
        for page_num in sorted(page_map.keys()):
            page_text = clean_document_text(page_map[page_num])
            if not page_text:
                continue

            page_chunks = _split_text_into_windows(
                page_text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            for p_chunk_text, start_pos, end_pos in page_chunks:
                chunk_id = f"{document_id}_p{page_num}_c{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        text=p_chunk_text,
                        page_number=page_num,
                        char_start=start_pos,
                        char_end=end_pos,
                        metadata={"page": page_num, "chunk_index": chunk_idx},
                    )
                )
                chunk_idx += 1
        return chunks

    stripped = text.strip()
    if not stripped:
        return []

    # Single continuous document chunking
    windowed = _split_text_into_windows(
        stripped,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    for idx, (chunk_str, start_pos, end_pos) in enumerate(windowed):
        chunk_id = f"{document_id}_c{idx}"
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                text=chunk_str,
                char_start=start_pos,
                char_end=end_pos,
                metadata={"chunk_index": idx},
            )
        )

    return chunks


def _split_text_into_windows(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> List[Tuple[str, int, int]]:
    """
    Helper to slice text into overlapping windows without cutting mid-sentence when possible.
    Returns: List of (chunk_text, start_char, end_char)
    """
    total_len = len(text)
    if total_len <= chunk_size:
        return [(text, 0, total_len)]

    # Break into natural sentence or paragraph units
    paragraphs = PARAGRAPH_SPLIT_REGEX.split(text)
    units: List[str] = []
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue
        sentences = SENTENCE_SPLIT_REGEX.split(p_clean)
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                units.append(s_clean)

    if not units:
        units = [text]

    chunks: List[Tuple[str, int, int]] = []
    current_tokens: List[str] = []
    current_len = 0
    current_start = 0

    for unit in units:
        unit_len = len(unit)
        # If a single sentence exceeds chunk_size, split by character budget
        if unit_len > chunk_size:
            if current_tokens:
                chunk_text = " ".join(current_tokens)
                chunks.append((chunk_text, current_start, current_start + len(chunk_text)))
                current_tokens = []
                current_len = 0

            # Sub-chunk the oversized unit
            sub_start = 0
            while sub_start < unit_len:
                sub_end = min(unit_len, sub_start + chunk_size)
                sub_slice = unit[sub_start:sub_end].strip()
                if sub_slice:
                    chunks.append((sub_slice, sub_start, sub_end))
                sub_start += (chunk_size - chunk_overlap)
            current_start += unit_len
            continue

        if current_len + unit_len + 1 > chunk_size and current_tokens:
            chunk_text = " ".join(current_tokens)
            chunks.append((chunk_text, current_start, current_start + len(chunk_text)))

            # Carry over overlap units from the end of current_tokens
            overlap_tokens: List[str] = []
            overlap_len = 0
            for t in reversed(current_tokens):
                if overlap_len + len(t) + 1 <= chunk_overlap:
                    overlap_tokens.insert(0, t)
                    overlap_len += len(t) + 1
                else:
                    break

            current_tokens = list(overlap_tokens)
            current_len = sum(len(t) for t in current_tokens) + max(0, len(current_tokens) - 1)
            current_start += (len(chunk_text) - current_len)

        current_tokens.append(unit)
        current_len += unit_len + (1 if len(current_tokens) > 1 else 0)

    if current_tokens:
        chunk_text = " ".join(current_tokens)
        chunks.append((chunk_text, current_start, min(total_len, current_start + len(chunk_text))))

    return chunks


def extract_text_from_upload(
    content: bytes,
    filename: str,
    mime_type: Optional[str] = None,
) -> DocumentExtractionResult:
    """
    Extract raw text and structural components from uploaded bytes.
    Enforces format limits, magic byte security, and empty document rejection.
    """
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError(f"content must be bytes, got {type(content).__name__}")
    if len(content) == 0:
        raise EmptyDocumentError("Uploaded file is completely empty (0 bytes).")
    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise DocumentTooLargeError(
            f"File size ({len(content) / (1024*1024):.1f}MB) exceeds {MAX_DOCUMENT_SIZE_BYTES / (1024*1024):.0f}MB limit."
        )

    # Magic byte checks for dangerous executables
    if content.startswith(b"MZ") or content.startswith(b"\x7fELF"):
        raise UnsupportedFormatError("Binary executable files (.exe, ELF, DLL) are strictly prohibited.")
    if content.startswith(b"PK\x03\x04") or content.startswith(b"PK\x05\x06"):
        # We only accept raw PDF, CSV, TXT; archives are disallowed
        raise UnsupportedFormatError("Compressed archives (.zip, .jar) are not supported.")

    ext = os.path.splitext(filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Unsupported file extension '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    # 1. Plain Text (.txt)
    if ext == ".txt":
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = content.decode("latin-1")
            except Exception as exc:
                raise DocumentCorruptedError(f"Failed to decode text document: {exc}")

        cleaned = clean_document_text(raw_text)
        if not cleaned:
            raise EmptyDocumentError("Uploaded text file contains no readable text content.")

        return DocumentExtractionResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            format="txt",
            total_characters=len(raw_text),
            cleaned_characters=len(cleaned),
        )

    # 2. CSV Document (.csv)
    if ext == ".csv":
        try:
            decoded_csv = content.decode("utf-8-sig", errors="replace")
        except Exception as exc:
            raise DocumentCorruptedError(f"Failed to decode CSV document: {exc}")

        reader = csv.reader(io.StringIO(decoded_csv))
        try:
            rows = list(reader)
        except Exception as exc:
            raise DocumentCorruptedError(f"CSV parsing error: {exc}")

        if not rows:
            raise EmptyDocumentError("Uploaded CSV file contains no rows.")

        headers = [h.strip() for h in rows[0]] if rows else []
        sections: List[Dict[str, Any]] = []
        text_lines: List[str] = []

        for row_idx, r in enumerate(rows[1:], start=1):
            row_dict = {}
            row_fragments = []
            for col_idx, col_name in enumerate(headers):
                val = r[col_idx].strip() if col_idx < len(r) else ""
                if val:
                    row_dict[col_name] = val
                    row_fragments.append(f"{col_name}: {val}")
            if row_fragments:
                row_str = ". ".join(row_fragments)
                text_lines.append(row_str)
                sections.append({"row_index": row_idx, "data": row_dict, "text": row_str})

        raw_text = "\n".join(text_lines)
        cleaned = clean_document_text(raw_text)
        if not cleaned:
            raise EmptyDocumentError("Uploaded CSV contains no non-empty text rows.")

        return DocumentExtractionResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            format="csv",
            sections=sections,
            total_characters=len(raw_text),
            cleaned_characters=len(cleaned),
        )

    # 3. PDF Document (.pdf)
    if ext == ".pdf":
        page_map: Dict[int, str] = {}
        full_text_list: List[str] = []

        try:
            import pypdf
        except ImportError:
            raise DependencyMissingError(
                "PDF parsing requires the maintained 'pypdf' package (pypdf>=4.0.0). "
                "Dependency is missing from shared requirements.txt; please coordinate with Jay."
            )

        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise EmptyDocumentError("PDF contains 0 pages.")
            if num_pages > 50:
                raise DocumentTooLargeError(f"PDF exceeds maximum page limit of 50 pages (has {num_pages}).")

            for p_idx in range(num_pages):
                page_text = reader.pages[p_idx].extract_text() or ""
                page_map[p_idx + 1] = page_text
                full_text_list.append(page_text)
        except (EmptyDocumentError, DocumentTooLargeError):
            raise
        except Exception as exc:
            raise DocumentCorruptedError(f"Corrupt or unreadable PDF: {exc}")

        raw_text = "\n".join(full_text_list)
        cleaned = clean_document_text(raw_text)
        if not cleaned:
            raise EmptyDocumentError("Uploaded PDF contains no extractable text.")

        return DocumentExtractionResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            format="pdf",
            pages=page_map,
            total_characters=len(raw_text),
            cleaned_characters=len(cleaned),
        )

    raise UnsupportedFormatError(f"Unsupported file format for '{filename}'.")


class UploadedDocumentNLPPipeline:
    """
    Orchestrates the end-to-end processing of sandboxed user uploaded documents
    through Floor 2 Language & Knowledge Agents.
    """

    def __init__(
        self,
        translation_agent: Optional[TranslationAgent] = None,
        extraction_agent: Optional[ExtractionAgent] = None,
        resolution_agent: Optional[ResolutionAgent] = None,
        threading_agent: Optional[ThreadingAgent] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE_CHARS,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    ):
        self.translation_agent = translation_agent or TranslationAgent()
        self.extraction_agent = extraction_agent or ExtractionAgent()
        self.resolution_agent = resolution_agent or ResolutionAgent()
        self.threading_agent = threading_agent or ThreadingAgent()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document(
        self,
        content: Union[bytes, str],
        filename: str,
        workspace_id: Union[int, str],
        document_id: Optional[str] = None,
        uploader_id: Optional[int] = None,
        mime_type: Optional[str] = None,
    ) -> UploadedDocumentAnalysis:
        """
        Execute full document NLP pipeline:
        Extraction -> Cleaning -> Chunking -> Translation -> NER -> Entity Resolution -> Threading.
        Strictly enforces caller-supplied workspace_id and provenance attribution.
        """
        norm_ws = normalize_workspace_id(workspace_id)
        if norm_ws is None:
            raise ValueError("Trusted workspace_id must be provided for uploaded document processing.")

        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, (bytes, bytearray)):
            content_bytes = bytes(content)
        else:
            raise TypeError(f"content must be bytes or str, got {type(content).__name__}")

        doc_hash = hashlib.sha256(content_bytes).hexdigest()
        doc_id = str(document_id).strip() if document_id else f"upload_{doc_hash[:12]}"

        logger.info(
            "Starting upload NLP processing for doc_id=%s, filename=%s, workspace_id=%s, size_bytes=%d",
            doc_id,
            filename,
            norm_ws,
            len(content_bytes),
        )

        # 1. Text Extraction
        extract_res = extract_text_from_upload(
            content=content_bytes,
            filename=filename,
            mime_type=mime_type,
        )

        # Detect document-level language
        doc_lang, doc_conf, doc_is_mixed = detect_document_language(extract_res.cleaned_text)
        warnings: List[str] = []

        if doc_lang != "en" and doc_lang not in SUPPORTED_TRANSLATION_LANGUAGES and doc_lang != "unknown":
            warnings.append(
                f"Detected language '{doc_lang}' is not supported by the translation engine; original text preserved."
            )

        # 2. Chunking
        chunks = chunk_document_text(
            text=extract_res.cleaned_text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            page_map=extract_res.pages if extract_res.format == "pdf" else None,
            document_id=doc_id,
        )

        if not chunks:
            # Fallback single chunk if non-empty text was extracted
            chunks = [
                DocumentChunk(
                    chunk_id=f"{doc_id}_c0",
                    document_id=doc_id,
                    text=extract_res.cleaned_text,
                    char_start=0,
                    char_end=len(extract_res.cleaned_text),
                )
            ]

        # 3. Process Chunks through Language, Extraction, and Resolution
        all_raw_entities: List[Dict[str, Any]] = []
        all_resolved_entities: List[Dict[str, Any]] = []
        seen_entity_keys: Set[Tuple[str, str]] = set()  # (canonical_name, entity_type) to prevent duplicates
        collected_event_types: List[str] = []

        for chunk in chunks:
            chunk_text = chunk.text.strip()
            if not chunk_text:
                continue

            # Determine chunk language
            chunk_lang = doc_lang
            if doc_is_mixed or doc_lang == "unknown":
                c_lang, _, _ = detect_document_language(chunk_text)
                if c_lang != "unknown":
                    chunk_lang = c_lang

            # Translate only if chunk is non-English and supported by the translation engine
            translated_chunk_text = chunk_text
            if chunk_lang in ("hi", "ur", "zh"):
                trans_input = {
                    "title": "",
                    "content": chunk_text,
                    "language": chunk_lang,
                }
                trans_result = self.translation_agent.run(trans_input)
                translated_chunk_text = (
                    trans_result.get("translated_content")
                    or trans_result.get("translated_text")
                    or chunk_text
                )

            # 3b. ExtractionAgent
            article_in = ArticleIn(
                id=None,
                title=f"Document Upload {doc_id} Chunk {chunk.chunk_id}",
                content=translated_chunk_text,
                url=f"upload://{norm_ws}/{doc_id}/{chunk.chunk_id}",
                language=chunk_lang if chunk_lang != "unknown" else "en",
            )
            analysis_out = self.extraction_agent.run(article_in)
            if analysis_out.event_type and analysis_out.event_type != "general":
                collected_event_types.append(analysis_out.event_type)

            chunk_mentions = [
                {
                    "name": ent.entity_value,
                    "entity_type": ent.entity_type,
                    "context": translated_chunk_text,
                }
                for ent in analysis_out.entities
            ]

            # Check for known workspace feedback aliases in the text (workspace-isolated overlay)
            seen_mention_names = {m["name"].lower().strip() for m in chunk_mentions}
            if hasattr(self.resolution_agent, "feedback_store") and self.resolution_agent.feedback_store:
                fb_store = self.resolution_agent.feedback_store
                candidate_fb_records = []
                if norm_ws in fb_store._workspace_stores:
                    for entry in fb_store._workspace_stores[norm_ws].values():
                        if entry.record and entry.record.decision == "accepted":
                            candidate_fb_records.append(entry.record)
                for entry in fb_store._global_store.values():
                    if entry.record and entry.record.decision == "accepted":
                        candidate_fb_records.append(entry.record)

                for fb_rec in candidate_fb_records:
                    s_mention = fb_rec.source_mention
                    if s_mention.lower().strip() not in seen_mention_names:
                        if re.search(r"\b" + re.escape(s_mention) + r"\b", translated_chunk_text, re.IGNORECASE):
                            chunk_mentions.append({
                                "name": s_mention,
                                "entity_type": fb_rec.entity_type or "ORGANISATION",
                                "context": translated_chunk_text,
                            })
                            seen_mention_names.add(s_mention.lower().strip())

            # 3c. ResolutionAgent (strictly using trusted norm_ws)
            if chunk_mentions:
                res_out = self.resolution_agent.run(chunk_mentions, workspace_id=norm_ws)
                resolved_list = res_out.get("resolved_entities", [])

                for m_dict, res_ent in zip(chunk_mentions, resolved_list):
                    raw_val = m_dict["name"]
                    c_name = res_ent.get("canonical_name") or raw_val
                    e_type = res_ent.get("entity_type") or m_dict.get("entity_type") or "UNKNOWN"
                    dedup_key = (c_name.lower().strip(), e_type.upper().strip())

                    # Enrich resolved entity with mandatory user_upload provenance
                    res_ent_enriched = dict(res_ent)
                    res_ent_enriched["source_type"] = SourceType.USER_UPLOAD.value
                    res_ent_enriched["workspace_id"] = norm_ws
                    res_ent_enriched["document_id"] = doc_id
                    res_ent_enriched["chunk_id"] = chunk.chunk_id
                    if chunk.page_number:
                        res_ent_enriched["page_number"] = chunk.page_number

                    all_raw_entities.append(
                        {
                            "raw_name": raw_val,
                            "entity_type": e_type,
                            "chunk_id": chunk.chunk_id,
                            "page_number": chunk.page_number,
                            "confidence": res_ent.get("confidence", 1.0),
                            "source_type": SourceType.USER_UPLOAD.value,
                            "workspace_id": norm_ws,
                        }
                    )

                    # Deduplicate in the document-level canonical entity list
                    if dedup_key not in seen_entity_keys:
                        seen_entity_keys.add(dedup_key)
                        all_resolved_entities.append(res_ent_enriched)

        # 4. Conservative Event Threading Gate
        primary_event_type = collected_event_types[0] if collected_event_types else "general"
        has_event_evidence, event_rationale = evaluate_event_evidence(
            text=extract_res.cleaned_text,
            extracted_entities=all_resolved_entities,
            event_type=primary_event_type,
        )

        event_threads_list: List[Dict[str, Any]] = []
        if has_event_evidence:
            threading_input = EventThreadingIn(
                article_id=0,
                title=f"Uploaded Document: {filename}",
                content=extract_res.cleaned_text[:2000],
                entities=[e["canonical_name"] for e in all_resolved_entities if "canonical_name" in e][:10],
                event_type=primary_event_type if primary_event_type != "general" else "border_incident",
                region="National",
            )
            threading_out = self.threading_agent.run(threading_input)
            top_link = threading_out.candidate_links[0] if threading_out.candidate_links else None
            event_threads_list = [
                {
                    "event_id": threading_out.matched_event_id,
                    "action": "linked_existing" if threading_out.matched_event_id else "created_new_cluster",
                    "created_new_event": threading_out.created_new_event,
                    "new_event_title": threading_out.new_event_title,
                    "confidence": top_link.confidence if top_link else 1.0,
                    "rationale": f"{event_rationale}; {top_link.explanation if top_link else ''}".strip("; "),
                    "workspace_id": norm_ws,
                    "source_type": SourceType.USER_UPLOAD.value,
                }
            ]
        else:
            event_threads_list = [
                {
                    "event_id": None,
                    "action": "skipped_no_event_evidence",
                    "created_new_event": False,
                    "new_event_title": None,
                    "confidence": 0.0,
                    "rationale": event_rationale,
                    "workspace_id": norm_ws,
                    "source_type": SourceType.USER_UPLOAD.value,
                }
            ]

        # 5. Document-level Provenance
        avg_conf = 1.0
        if all_resolved_entities:
            avg_conf = round(sum(e.get("confidence", 1.0) for e in all_resolved_entities) / len(all_resolved_entities), 4)

        doc_prov = Provenance(
            source_ids=[],
            method="uploaded_document_nlp_pipeline",
            model_version=f"upload_nlp:0.1.0",
            confidence=avg_conf,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.USER_UPLOAD,
        )

        logger.info(
            "Completed upload NLP for doc_id=%s: chunks=%d, raw_entities=%d, resolved_entities=%d",
            doc_id,
            len(chunks),
            len(all_raw_entities),
            len(all_resolved_entities),
        )

        return UploadedDocumentAnalysis(
            document_id=doc_id,
            filename=filename,
            format=extract_res.format,
            workspace_id=norm_ws,
            source_type=SourceType.USER_UPLOAD.value,
            chunks=chunks,
            extracted_entities=all_raw_entities,
            resolved_entities=all_resolved_entities,
            event_threads=event_threads_list,
            detected_language=doc_lang,
            provenance=doc_prov,
            status="success",
            warnings=warnings,
        )
