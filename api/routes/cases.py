"""
Cases & Investigations Router — Raksha AI Stage 3 Solid
Owner: Jay (Lead & Platform) | Milestone: M9b
Allows intelligence analysts to group evidence, document working hypotheses, and collaborate on dossiers.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text

from common.auth import get_db, get_current_user_optional, require_analyst_or_admin
from common.audit import log_audit_event

router = APIRouter(prefix="/cases", tags=["Investigations & Cases"])


class CaseCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    classification: str = "restricted"
    tags: Optional[List[str]] = []
    workspace_id: Optional[int] = None


class CaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    classification: Optional[str] = None
    tags: Optional[List[str]] = None


class CaseItemAddRequest(BaseModel):
    item_type: str  # 'article', 'entity', 'event', 'incident'
    item_id: str
    title: Optional[str] = None
    analyst_notes: Optional[str] = None


class CaseNoteAddRequest(BaseModel):
    note_text: str
    hypothesis: Optional[str] = None


@router.get("")
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """List ongoing investigations and analytical case folders."""
    where_clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": (page - 1) * limit}

    if status_filter and status_filter != "all":
        where_clauses.append("c.status = :status")
        params["status"] = status_filter
    if priority and priority != "all":
        where_clauses.append("c.priority = :priority")
        params["priority"] = priority
    if q:
        where_clauses.append("(c.title ILIKE :q OR c.description ILIKE :q)")
        params["q"] = f"%{q.strip()}%"

    where_sql = " AND ".join(where_clauses)

    rows = db.execute(
        text(f"""
            SELECT c.id, c.title, c.description, c.status, c.priority, c.classification,
                   c.lead_analyst_id, c.workspace_id, c.tags, c.created_at, c.updated_at,
                   u.full_name AS lead_analyst_name,
                   w.name AS workspace_name,
                   (SELECT COUNT(*) FROM case_items WHERE case_id = c.id) AS evidence_count,
                   (SELECT COUNT(*) FROM case_notes WHERE case_id = c.id) AS notes_count
            FROM cases c
            LEFT JOIN users u ON u.id = c.lead_analyst_id
            LEFT JOIN workspaces w ON w.id = c.workspace_id
            WHERE {where_sql}
            ORDER BY
                CASE c.priority
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                c.updated_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    total = db.execute(
        text(f"SELECT COUNT(*) FROM cases c WHERE {where_sql}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).scalar() or 0

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "cases": [dict(r._mapping) for r in rows],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_case(
    req: CaseCreateRequest,
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Open a new intelligence case folder."""
    ws_id = req.workspace_id
    if not ws_id:
        ws = db.execute(text("SELECT id FROM workspaces WHERE is_shared = TRUE LIMIT 1")).fetchone()
        ws_id = ws[0] if ws else 1

    row = db.execute(
        text("""
            INSERT INTO cases (
                title, description, status, priority, classification,
                lead_analyst_id, workspace_id, tags, created_at, updated_at
            ) VALUES (
                :title, :description, 'active', :priority, :classification,
                :analyst_id, :ws_id, :tags, NOW(), NOW()
            )
            RETURNING id, title, status, priority
        """),
        {
            "title": req.title.strip(),
            "description": req.description,
            "priority": req.priority,
            "classification": req.classification,
            "analyst_id": current_user["id"],
            "ws_id": ws_id,
            "tags": req.tags or [],
        },
    ).fetchone()
    db.commit()

    log_audit_event(
        db,
        action="case.created",
        user_id=current_user["id"],
        entity_type="case",
        entity_id=str(row.id),
        details={"title": req.title, "priority": req.priority},
    )

    return {"id": row.id, "title": row.title, "status": row.status, "priority": row.priority}


@router.get("/{case_id}")
def get_case(
    case_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """Retrieve full case details, attached evidence, and chronological analyst notes."""
    case_row = db.execute(
        text("""
            SELECT c.id, c.title, c.description, c.status, c.priority, c.classification,
                   c.lead_analyst_id, c.workspace_id, c.tags, c.created_at, c.updated_at,
                   u.full_name AS lead_analyst_name, u.email AS lead_analyst_email,
                   w.name AS workspace_name
            FROM cases c
            LEFT JOIN users u ON u.id = c.lead_analyst_id
            LEFT JOIN workspaces w ON w.id = c.workspace_id
            WHERE c.id = :cid
        """),
        {"cid": case_id},
    ).fetchone()

    if not case_row:
        raise HTTPException(status_code=404, detail="Investigation case not found")

    items = db.execute(
        text("""
            SELECT ci.id, ci.item_type, ci.item_id, ci.title, ci.analyst_notes,
                   ci.added_at, u.full_name AS added_by_name
            FROM case_items ci
            LEFT JOIN users u ON u.id = ci.added_by
            WHERE ci.case_id = :cid
            ORDER BY ci.added_at DESC
        """),
        {"cid": case_id},
    ).fetchall()

    notes = db.execute(
        text("""
            SELECT cn.id, cn.note_text, cn.hypothesis, cn.created_at,
                   u.full_name AS analyst_name, u.role AS analyst_role
            FROM case_notes cn
            LEFT JOIN users u ON u.id = cn.analyst_id
            WHERE cn.case_id = :cid
            ORDER BY cn.created_at ASC
        """),
        {"cid": case_id},
    ).fetchall()

    return {
        "case": dict(case_row._mapping),
        "evidence_items": [dict(i._mapping) for i in items],
        "notes": [dict(n._mapping) for n in notes],
    }


@router.put("/{case_id}")
def update_case(
    case_id: int,
    req: CaseUpdateRequest,
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Update case status, priority, or metadata."""
    updates = ["updated_at = NOW()"]
    params: dict = {"cid": case_id}

    if req.title is not None:
        updates.append("title = :title")
        params["title"] = req.title.strip()
    if req.description is not None:
        updates.append("description = :description")
        params["description"] = req.description
    if req.status is not None:
        updates.append("status = :status")
        params["status"] = req.status
    if req.priority is not None:
        updates.append("priority = :priority")
        params["priority"] = req.priority
    if req.classification is not None:
        updates.append("classification = :classification")
        params["classification"] = req.classification
    if req.tags is not None:
        updates.append("tags = :tags")
        params["tags"] = req.tags

    sql = f"UPDATE cases SET {', '.join(updates)} WHERE id = :cid RETURNING id, status, priority"
    row = db.execute(text(sql), params).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    db.commit()

    log_audit_event(
        db,
        action="case.updated",
        user_id=current_user["id"],
        entity_type="case",
        entity_id=str(case_id),
        details={"updated_fields": list(params.keys())},
    )

    return {"id": row.id, "status": row.status, "priority": row.priority}


@router.post("/{case_id}/items")
def add_case_item(
    case_id: int,
    req: CaseItemAddRequest,
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Attach evidence item (article, entity, event, incident) to case folder."""
    case_exists = db.execute(text("SELECT id FROM cases WHERE id = :cid"), {"cid": case_id}).fetchone()
    if not case_exists:
        raise HTTPException(status_code=404, detail="Case not found")

    title = req.title
    if not title:
        if req.item_type == "article":
            a = db.execute(text("SELECT title FROM articles WHERE id = :aid"), {"aid": int(req.item_id)}).fetchone()
            title = a[0] if a else f"Article #{req.item_id}"
        elif req.item_type == "entity":
            title = f"Entity: {req.item_id}"
        else:
            title = f"{req.item_type.title()} #{req.item_id}"

    row = db.execute(
        text("""
            INSERT INTO case_items (case_id, item_type, item_id, title, analyst_notes, added_by, added_at)
            VALUES (:cid, :itype, :iid, :title, :notes, :uid, NOW())
            RETURNING id, title, item_type
        """),
        {
            "cid": case_id,
            "itype": req.item_type,
            "iid": req.item_id,
            "title": title,
            "notes": req.analyst_notes,
            "uid": current_user["id"],
        },
    ).fetchone()

    db.execute(text("UPDATE cases SET updated_at = NOW() WHERE id = :cid"), {"cid": case_id})
    db.commit()

    log_audit_event(
        db,
        action="case.evidence_attached",
        user_id=current_user["id"],
        entity_type="case",
        entity_id=str(case_id),
        details={"item_type": req.item_type, "item_id": req.item_id, "title": title},
    )

    return {"id": row.id, "title": row.title, "item_type": row.item_type}


@router.delete("/{case_id}/items/{item_id}")
def remove_case_item(
    case_id: int,
    item_id: int,
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Remove attached evidence from case."""
    row = db.execute(
        text("DELETE FROM case_items WHERE id = :iid AND case_id = :cid RETURNING id"),
        {"iid": item_id, "cid": case_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Evidence item not found")

    db.execute(text("UPDATE cases SET updated_at = NOW() WHERE id = :cid"), {"cid": case_id})
    db.commit()

    log_audit_event(
        db,
        action="case.evidence_removed",
        user_id=current_user["id"],
        entity_type="case",
        entity_id=str(case_id),
        details={"case_item_id": item_id},
    )

    return {"removed": True, "id": item_id}


@router.post("/{case_id}/notes")
def add_case_note(
    case_id: int,
    req: CaseNoteAddRequest,
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Record an analytical note or testable hypothesis."""
    case_exists = db.execute(text("SELECT id FROM cases WHERE id = :cid"), {"cid": case_id}).fetchone()
    if not case_exists:
        raise HTTPException(status_code=404, detail="Case not found")

    row = db.execute(
        text("""
            INSERT INTO case_notes (case_id, analyst_id, note_text, hypothesis, created_at)
            VALUES (:cid, :uid, :note, :hypo, NOW())
            RETURNING id, note_text, hypothesis, created_at
        """),
        {
            "cid": case_id,
            "uid": current_user["id"],
            "note": req.note_text.strip(),
            "hypo": req.hypothesis.strip() if req.hypothesis else None,
        },
    ).fetchone()

    db.execute(text("UPDATE cases SET updated_at = NOW() WHERE id = :cid"), {"cid": case_id})
    db.commit()

    log_audit_event(
        db,
        action="case.note_added",
        user_id=current_user["id"],
        entity_type="case",
        entity_id=str(case_id),
        details={"hypothesis": req.hypothesis},
    )

    return {
        "id": row.id,
        "note_text": row.note_text,
        "hypothesis": row.hypothesis,
        "created_at": row.created_at.isoformat(),
    }


@router.get("/{case_id}/export")
def export_case_dossier(
    case_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """Export complete intelligence case dossier as structured bundle."""
    case_data = get_case(case_id=case_id, current_user=current_user, db=db)

    log_audit_event(
        db,
        action="case.dossier_exported",
        user_id=current_user["id"] if current_user else None,
        entity_type="case",
        entity_id=str(case_id),
        details={"title": case_data["case"]["title"]},
    )

    return {
        "format": "raksha_intelligence_dossier_v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "dossier": case_data,
    }
