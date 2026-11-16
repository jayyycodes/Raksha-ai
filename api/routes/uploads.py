"""
Uploads API Route — Secure parsing and ingestion for analyst data (Stage 3 Solid - Milestones M9b & M9c).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy import text

from common.db import get_db as _get_db
from pipeline.upload_parsers import SafeUploadParser, UploadParserError

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def get_db():
    with _get_db() as db:
        yield db


@router.post("/parse")
async def parse_uploaded_document(
    file: UploadFile = File(...),
):
    """
    Parse an uploaded document (.csv, .txt, .pdf) safely without writing to DB.
    Returns preview of extracted records and column mappings.
    """
    file_bytes = await file.read()
    parser = SafeUploadParser()

    try:
        articles = parser.parse_file(file_bytes, filename=file.filename or "uploaded_file")
    except UploadParserError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected parsing error: {exc}")

    return {
        "status": "success",
        "filename": file.filename,
        "total_parsed": len(articles),
        "articles": [a.model_dump() for a in articles[:50]],  # Preview up to 50
    }


@router.post("/ingest")
async def ingest_uploaded_document(
    file: UploadFile = File(...),
    workspace_id: str = Form("default_workspace"),
    db=Depends(get_db),
):
    """
    Safely ingest parsed articles into the database under 'user_upload' source_type,
    tagging the workspace and preparing them for the analyst intelligence workflow.
    """
    file_bytes = await file.read()
    parser = SafeUploadParser()

    try:
        articles = parser.parse_file(file_bytes, filename=file.filename or "uploaded_file")
    except UploadParserError as err:
        raise HTTPException(status_code=400, detail=str(err))

    # Ensure a 'user_upload' source exists
    source_row = db.execute(
        text("SELECT id FROM sources WHERE name = 'Analyst User Upload'"),
    ).fetchone()

    if not source_row:
        db.execute(
            text("""
                INSERT INTO sources (name, url, ring, country, language, is_active)
                VALUES ('Analyst User Upload', 'upload://workspace', 1, 'India', 'en', true)
            """)
        )
        db.commit()
        source_row = db.execute(
            text("SELECT id FROM sources WHERE name = 'Analyst User Upload'"),
        ).fetchone()

    source_id = source_row.id if source_row else 1
    inserted_count = 0

    for a in articles:
        # Check for deduplication
        existing = db.execute(
            text("SELECT id FROM articles WHERE url_hash = :hash"),
            {"hash": a.url_hash},
        ).fetchone()

        if not existing:
            db.execute(
                text("""
                    INSERT INTO articles (source_id, title, url, url_hash, content, language, published_at, is_processed)
                    VALUES (:source_id, :title, :url, :hash, :content, :lang, :pub, false)
                """),
                {
                    "source_id": source_id,
                    "title": a.title,
                    "url": a.url,
                    "hash": a.url_hash,
                    "content": a.content,
                    "lang": a.language,
                    "pub": a.published_at,
                },
            )
            inserted_count += 1

    db.commit()
    return {
        "status": "success",
        "filename": file.filename,
        "total_parsed": len(articles),
        "total_inserted": inserted_count,
        "workspace_id": workspace_id,
    }
