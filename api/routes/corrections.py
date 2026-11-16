"""
FastAPI Router — Correction & Takedown Requests (DPDP Act Compliance)
Owner: Jay
Stage: 3 (M9c: Verification & Ethics Compliance)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from common.auth import get_current_user, require_role
from common.db import get_db, text
from common.audit import log_audit_event
from common.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/corrections", tags=["Correction Requests"])


class CorrectionSubmitRequest(BaseModel):
    target_type: str  # 'entity', 'article', 'event', 'threat_score'
    target_id: str
    requester_email: EmailStr
    claim_details: str
    supporting_evidence: Optional[str] = None
    workspace_id: Optional[int] = 1


class CorrectionResolutionRequest(BaseModel):
    status: str  # 'in_review', 'accepted', 'rejected'
    resolution_notes: str


@router.post("")
def submit_correction_request(payload: CorrectionSubmitRequest):
    """
    Public / Analyst endpoint to submit a correction or takedown claim
    in accordance with Digital Personal Data Protection (DPDP) Act requirements.
    """
    valid_types = {"entity", "article", "event", "threat_score"}
    if payload.target_type.lower() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target_type. Must be one of: {sorted(list(valid_types))}"
        )

    with get_db() as db:
        res = db.execute(
            text(
                """
                INSERT INTO correction_requests (
                    target_type, target_id, requester_email,
                    claim_details, supporting_evidence,
                    status, workspace_id, created_at
                )
                VALUES (
                    :target_type, :target_id, :requester_email,
                    :claim_details, :supporting_evidence,
                    'submitted', :workspace_id, NOW()
                )
                RETURNING id, created_at
                """
            ),
            {
                "target_type": payload.target_type.lower(),
                "target_id": payload.target_id,
                "requester_email": payload.requester_email,
                "claim_details": payload.claim_details,
                "supporting_evidence": payload.supporting_evidence,
                "workspace_id": payload.workspace_id or 1,
            },
        ).fetchone()

        corr_id = res[0]
        created_at = res[1].isoformat() if res[1] else None

        # Log immutable audit event
        log_audit_event(
            db,
            action="CORRECTION_SUBMITTED",
            user_id=None,
            entity_type="correction_requests",
            entity_id=str(corr_id),
            details={
                "target_type": payload.target_type,
                "target_id": payload.target_id,
                "requester_email": payload.requester_email,
                "workspace_id": payload.workspace_id or 1,
            },
        )

    return {
        "status": "ok",
        "message": "Correction request lodged successfully. It will be reviewed by intelligence governance.",
        "id": corr_id,
        "created_at": created_at,
    }


@router.get("")
def list_corrections(
    status: Optional[str] = Query(None, description="Filter by status: submitted, in_review, accepted, rejected"),
    target_type: Optional[str] = Query(None, description="Filter by target_type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List correction requests with governance filtering."""
    where_clauses = ["1=1"]
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("c.status = :status")
        params["status"] = status
    if target_type:
        where_clauses.append("c.target_type = :target_type")
        params["target_type"] = target_type

    where_sql = " AND ".join(where_clauses)

    with get_db() as db:
        rows = db.execute(
            text(
                f"""
                SELECT c.id, c.target_type, c.target_id, c.requester_email,
                       c.claim_details, c.supporting_evidence, c.status,
                       c.resolution_notes, c.resolved_by, c.workspace_id,
                       c.created_at, c.resolved_at, u.email as resolver_email
                FROM correction_requests c
                LEFT JOIN users u ON c.resolved_by = u.id
                WHERE {where_sql}
                ORDER BY c.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).fetchall()

        total = db.execute(
            text(f"SELECT COUNT(*) FROM correction_requests c WHERE {where_sql}"),
            params,
        ).scalar() or 0

        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "target_type": r[1],
                "target_id": r[2],
                "requester_email": r[3],
                "claim_details": r[4],
                "supporting_evidence": r[5],
                "status": r[6],
                "resolution_notes": r[7],
                "resolved_by": r[8],
                "workspace_id": r[9],
                "created_at": r[10].isoformat() if r[10] else None,
                "resolved_at": r[11].isoformat() if r[11] else None,
                "resolver_email": r[12] or None,
            })

        return {"total": total, "limit": limit, "offset": offset, "items": items}


@router.put("/{request_id}")
def resolve_correction_request(
    request_id: int,
    payload: CorrectionResolutionRequest,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
):
    """Resolve or update status of a correction request."""
    valid_statuses = {"submitted", "in_review", "accepted", "rejected"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {sorted(list(valid_statuses))}",
        )

    with get_db() as db:
        row = db.execute(
            text("SELECT id, target_type, target_id, status FROM correction_requests WHERE id = :id"),
            {"id": request_id},
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Correction request not found")

        db.execute(
            text(
                """
                UPDATE correction_requests
                SET status = :status,
                    resolution_notes = :notes,
                    resolved_by = :resolved_by,
                    resolved_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": request_id,
                "status": payload.status,
                "notes": payload.resolution_notes,
                "resolved_by": current_user["id"],
            },
        )

        # Log immutable audit event
        log_audit_event(
            db,
            action="CORRECTION_RESOLVED",
            user_id=current_user["id"],
            entity_type="correction_requests",
            entity_id=str(request_id),
            details={
                "old_status": row[3],
                "new_status": payload.status,
                "target_type": row[1],
                "target_id": row[2],
                "resolution_notes": payload.resolution_notes,
                "workspace_id": current_user.get("workspace_id", 1),
            },
        )

    return {"status": "ok", "message": f"Correction request #{request_id} updated to {payload.status}"}
