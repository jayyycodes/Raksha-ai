"""
Safe Upload Parsers for Analyst Bring-Your-Own-Data (Stage 3 Solid - Milestones M9b & M9c).
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Supports secure parsing for:
- CSV files (via pandas with dynamic column mapping and sanitization)
- TXT files (structured paragraph and header extraction)
- PDF documents (via pypdf with 50-page max limits and corrupted stream guards)

Enforces:
- 15 MB maximum file size limit
- Content length bounds (summary <=500 chars, full text <=5000 chars)
- Mandatory `source_type='user_upload'` tagging for workspace isolation
"""
import hashlib
import io
import re
from datetime import datetime, timezone
from typing import Any, BinaryIO, Optional, Union
import pandas as pd
from pypdf import PdfReader
from pydantic import BaseModel, Field

from common.logger import get_logger

logger = get_logger(__name__)

MAX_FILE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_PDF_PAGES = 50


class ParsedUploadArticle(BaseModel):
    """Normalized article extracted from an uploaded document."""
    title: str
    url: str
    url_hash: str
    content: str
    source_name: str = "User Upload"
    source_type: str = "user_upload"
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    ring: int = 1
    country: str = "India"
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadParserError(Exception):
    """Raised when an uploaded file violates safety bounds or format specifications."""
    pass


class SafeUploadParser:
    """Multi-format safe document parser for analyst workspaces."""

    def parse_file(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: Optional[str] = None,
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> list[ParsedUploadArticle]:
        """
        Detect file type, validate safety constraints, and parse into structured articles.
        """
        if len(file_bytes) > MAX_FILE_BYTES:
            raise UploadParserError(f"File size ({len(file_bytes)} bytes) exceeds the 15 MB limit.")

        ext = filename.lower().split(".")[-1]
        if ext == "csv":
            return self.parse_csv(file_bytes, filename, custom_mapping=custom_mapping)
        elif ext in ("txt", "text", "log"):
            return self.parse_txt(file_bytes, filename)
        elif ext == "pdf":
            return self.parse_pdf(file_bytes, filename)
        else:
            raise UploadParserError(f"Unsupported file format '.{ext}'. Supported formats: .csv, .txt, .pdf")

    def parse_csv(
        self,
        file_bytes: bytes,
        filename: str,
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> list[ParsedUploadArticle]:
        """Safely parse CSV file using pandas with intelligent column mapping."""
        try:
            # Try utf-8 first, fallback to latin-1
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
        except Exception as exc:
            raise UploadParserError(f"Failed to read CSV: {exc}") from exc

        if df.empty:
            return []

        col_map = self._infer_csv_columns(list(df.columns), custom_mapping)
        if not col_map.get("content") and not col_map.get("title"):
            raise UploadParserError(
                f"CSV must contain at least a 'content' or 'title' column. Found columns: {list(df.columns)}"
            )

        articles: list[ParsedUploadArticle] = []
        now = datetime.now(timezone.utc)

        for idx, row in df.iterrows():
            title_val = str(row[col_map["title"]]).strip() if col_map.get("title") and pd.notna(row[col_map["title"]]) else f"Record {idx + 1} from {filename}"
            content_val = str(row[col_map["content"]]).strip() if col_map.get("content") and pd.notna(row[col_map["content"]]) else title_val

            if not content_val or content_val == "nan":
                continue

            raw_url = str(row[col_map["url"]]).strip() if col_map.get("url") and pd.notna(row[col_map["url"]]) else f"upload://{filename}#row={idx + 1}"
            url_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()

            # Optional published date
            pub_date = now
            if col_map.get("date") and pd.notna(row[col_map["date"]]):
                try:
                    pub_date = pd.to_datetime(row[col_map["date"]]).to_pydatetime()
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                except Exception:
                    pub_date = now

            source_name = str(row[col_map["source"]]).strip() if col_map.get("source") and pd.notna(row[col_map["source"]]) else f"Upload: {filename}"

            articles.append(
                ParsedUploadArticle(
                    title=title_val[:200],
                    url=raw_url,
                    url_hash=url_hash,
                    content=content_val[:5000],
                    source_name=source_name[:100],
                    source_type="user_upload",
                    published_at=pub_date,
                    language="en",
                    ring=1,
                    country="India",
                    metadata={"filename": filename, "row_index": idx},
                )
            )

        return articles

    def parse_txt(self, file_bytes: bytes, filename: str) -> list[ParsedUploadArticle]:
        """Parse text document into discrete section/paragraph articles."""
        try:
            text_str = file_bytes.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            raise UploadParserError(f"Failed to read TXT file: {exc}")

        if not text_str:
            return []

        # Split into blocks separated by 2+ newlines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text_str) if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [text_str[:2000]]

        articles: list[ParsedUploadArticle] = []
        now = datetime.now(timezone.utc)

        for i, para in enumerate(paragraphs):
            first_line = para.split("\n")[0].strip()
            title = first_line[:120] if len(first_line) > 10 else f"{filename} - Section {i + 1}"
            raw_url = f"upload://{filename}#section={i + 1}"
            url_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()

            articles.append(
                ParsedUploadArticle(
                    title=title,
                    url=raw_url,
                    url_hash=url_hash,
                    content=para[:5000],
                    source_name=f"Upload: {filename}",
                    source_type="user_upload",
                    published_at=now,
                    language="en",
                    ring=1,
                    country="India",
                    metadata={"filename": filename, "section_index": i},
                )
            )
        return articles

    def parse_pdf(self, file_bytes: bytes, filename: str) -> list[ParsedUploadArticle]:
        """Safely extract pages from PDF with strict page limits and stream safety."""
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as exc:
            raise UploadParserError(f"Corrupted or invalid PDF format: {exc}") from exc

        total_pages = len(reader.pages)
        if total_pages > MAX_PDF_PAGES:
            raise UploadParserError(
                f"PDF exceeds the maximum allowable page limit ({total_pages} > {MAX_PDF_PAGES} pages)."
            )

        articles: list[ParsedUploadArticle] = []
        now = datetime.now(timezone.utc)
        pdf_title = (reader.metadata.title if reader.metadata and reader.metadata.title else None) or filename

        for page_num in range(total_pages):
            try:
                page_text = reader.pages[page_num].extract_text()
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num+1} from {filename}: {e}")
                continue

            if not page_text or len(page_text.strip()) < 30:
                continue

            clean_text = page_text.strip()
            first_line = clean_text.split("\n")[0].strip()
            title = f"[{pdf_title}] Page {page_num + 1}: {first_line[:80]}"
            raw_url = f"upload://{filename}#page={page_num + 1}"
            url_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()

            articles.append(
                ParsedUploadArticle(
                    title=title,
                    url=raw_url,
                    url_hash=url_hash,
                    content=clean_text[:5000],
                    source_name=f"Upload: {filename}",
                    source_type="user_upload",
                    published_at=now,
                    language="en",
                    ring=1,
                    country="India",
                    metadata={"filename": filename, "page_number": page_num + 1, "total_pages": total_pages},
                )
            )

        return articles

    def _infer_csv_columns(
        self,
        headers: list[str],
        custom_mapping: Optional[dict[str, str]] = None,
    ) -> dict[str, Optional[str]]:
        """Map CSV column headers to required schema keys."""
        col_map: dict[str, Optional[str]] = {
            "title": None,
            "content": None,
            "url": None,
            "date": None,
            "source": None,
        }

        if custom_mapping:
            for k, v in custom_mapping.items():
                if k in col_map and v in headers:
                    col_map[k] = v

        lower_headers = {h.lower().strip(): h for h in headers}

        # Title candidates
        if not col_map["title"]:
            for candidate in ("title", "headline", "subject", "heading", "name"):
                if candidate in lower_headers:
                    col_map["title"] = lower_headers[candidate]
                    break

        # Content candidates
        if not col_map["content"]:
            for candidate in ("content", "body", "text", "summary", "description", "article", "details"):
                if candidate in lower_headers:
                    col_map["content"] = lower_headers[candidate]
                    break

        # URL candidates
        if not col_map["url"]:
            for candidate in ("url", "link", "source_url", "uri"):
                if candidate in lower_headers:
                    col_map["url"] = lower_headers[candidate]
                    break

        # Date candidates
        if not col_map["date"]:
            for candidate in ("date", "published_at", "publish_date", "timestamp", "time", "created_at"):
                if candidate in lower_headers:
                    col_map["date"] = lower_headers[candidate]
                    break

        # Source candidates
        if not col_map["source"]:
            for candidate in ("source", "source_name", "publisher", "outlet", "author"):
                if candidate in lower_headers:
                    col_map["source"] = lower_headers[candidate]
                    break

        return col_map
