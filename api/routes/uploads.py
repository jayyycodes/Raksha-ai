"""
FastAPI Router — Sandboxed Data Uploads (BYOD)
Owner: Jay
Stage: 3 (M9c: Bring Your Own Data & Safe Uploads)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel

from common.auth import get_current_user, require_role
from common.db import get_db, text
from common.upload_service import process_sandboxed_upload, SANDBOX_STORAGE_DIR
from common.audit import log_audit_event
from common.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["Sandboxed Uploads"])


@router.get("")
def list_uploads(
    workspace_id: Optional[int] = Query(None, description="Filter by workspace ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List uploaded files within workspace."""
    ws_id = workspace_id or current_user.get("workspace_id") or 1

    with get_db() as db:
        rows = db.execute(
            text(
                """
                SELECT u.id, u.filename, u.file_hash, u.mime_type, u.file_size,
                       u.workspace_id, u.uploader_id, u.source_type, u.status,
                       u.parse_summary, u.created_at, usr.email as uploader_email
                FROM uploads u
                LEFT JOIN users usr ON u.uploader_id = usr.id
                WHERE u.workspace_id = :ws_id
                ORDER BY u.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"ws_id": ws_id, "limit": limit, "offset": offset},
        ).fetchall()

        total = db.execute(
            text("SELECT COUNT(*) FROM uploads WHERE workspace_id = :ws_id"),
            {"ws_id": ws_id},
        ).scalar() or 0

        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "filename": r[1],
                "file_hash": r[2],
                "mime_type": r[3],
                "file_size": r[4],
                "workspace_id": r[5],
                "uploader_id": r[6],
                "source_type": r[7],
                "status": r[8],
                "parse_summary": r[9] or {},
                "created_at": r[10].isoformat() if r[10] else None,
                "uploader_email": r[11] or "Unknown",
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "workspace_id": ws_id,
            "items": items,
        }


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    workspace_id: Optional[int] = Form(None),
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """
    Safely process and store user-uploaded OSINT file (CSV, TXT, PDF).
    Enforces 15MB size limit, 50-page PDF limit, magic bytes check,
    and sandboxed storage outside web root.
    """
    content = await file.read()
    ws_id = workspace_id or current_user.get("workspace_id") or 1

    try:
        result = process_sandboxed_upload(
            filename=file.filename or "uploaded_data.txt",
            content=content,
            workspace_id=ws_id,
            uploader_id=current_user["id"],
            actor_email=current_user["email"],
        )
        return {"status": "ok", "message": "File processed and safely stored", "upload": result}
    except ValueError as e:
        logger.warning(f"Upload validation rejected file '{file.filename}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload processing unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/{upload_id}")
def get_upload_detail(
    upload_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve details and parsed summary of an uploaded file."""
    with get_db() as db:
        row = db.execute(
            text(
                """
                SELECT u.id, u.filename, u.file_hash, u.mime_type, u.file_size,
                       u.workspace_id, u.uploader_id, u.source_type, u.status,
                       u.storage_path, u.parse_summary, u.created_at, usr.email as uploader_email
                FROM uploads u
                LEFT JOIN users usr ON u.uploader_id = usr.id
                WHERE u.id = :uid
                """
            ),
            {"uid": upload_id},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Upload record not found")

        return {
            "id": row[0],
            "filename": row[1],
            "file_hash": row[2],
            "mime_type": row[3],
            "file_size": row[4],
            "workspace_id": row[5],
            "uploader_id": row[6],
            "source_type": row[7],
            "status": row[8],
            "storage_path": row[9],
            "parse_summary": row[10] or {},
            "created_at": row[11].isoformat() if row[11] else None,
            "uploader_email": row[12] or "Unknown",
        }


@router.delete("/{upload_id}")
def delete_upload(
    upload_id: int,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """Delete an uploaded file record and purge its sandboxed disk storage."""
    with get_db() as db:
        row = db.execute(
            text("SELECT id, filename, storage_path, workspace_id FROM uploads WHERE id = :uid"),
            {"uid": upload_id},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Upload record not found")

        storage_path = row[2]
        filename = row[1]
        ws_id = row[3]

        # Purge file on disk safely
        try:
            p = Path(storage_path)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete sandboxed file {storage_path}: {e}")

        db.execute(text("DELETE FROM uploads WHERE id = :uid"), {"uid": upload_id})

        # Log audit event
        log_audit_event(
            db,
            action="DATA_UPLOAD_DELETE",
            user_id=current_user["id"],
            entity_type="uploads",
            entity_id=str(upload_id),
            details={"filename": filename, "workspace_id": ws_id, "deleted": True},
        )

    return {"status": "ok", "message": f"Upload #{upload_id} deleted"}
