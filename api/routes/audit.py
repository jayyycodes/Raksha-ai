"""
Immutable Audit Log Router — Raksha AI Stage 3 Solid
Owner: Jay (Lead & Platform) | Milestone: M8
Enforces accountability and traceability across all intelligence operations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from common.auth import get_db, require_analyst_or_admin

router = APIRouter(prefix="/audit", tags=["Audit Log & Compliance"])


@router.get("")
def list_audit_events(
    action: Optional[str] = Query(None, description="Filter by action name e.g. auth.login_success"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type e.g. profile, user"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """
    Retrieve immutable audit log records.
    Accessible to Analysts and Administrators only.
    """
    where_clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": (page - 1) * limit}

    if action:
        where_clauses.append("a.action = :action")
        params["action"] = action
    if entity_type:
        where_clauses.append("a.entity_type = :entity_type")
        params["entity_type"] = entity_type
    if user_id is not None:
        where_clauses.append("a.user_id = :user_id")
        params["user_id"] = user_id

    where_sql = " AND ".join(where_clauses)

    rows = db.execute(
        text(f"""
            SELECT a.id, a.user_id, a.action, a.entity_type, a.entity_id,
                   a.ip_address, a.user_agent, a.details, a.created_at,
                   u.email AS user_email, u.full_name AS user_name, u.role AS user_role
            FROM audit_log a
            LEFT JOIN users u ON u.id = a.user_id
            WHERE {where_sql}
            ORDER BY a.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    total = db.execute(
        text(f"""
            SELECT COUNT(*) FROM audit_log a
            WHERE {where_sql}
        """),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).scalar() or 0

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "events": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_email": r.user_email or "System / Anonymous",
                "user_name": r.user_name or "System",
                "user_role": r.user_role or "system",
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "details": r.details or {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/summary")
def get_audit_summary(
    current_user: dict = Depends(require_analyst_or_admin),
    db=Depends(get_db),
):
    """Action breakdown and high-level activity telemetry."""
    top_actions = db.execute(
        text("""
            SELECT action, COUNT(*) as count
            FROM audit_log
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """)
    ).fetchall()

    recent_24h = db.execute(
        text("SELECT COUNT(*) FROM audit_log WHERE created_at >= NOW() - INTERVAL '24 hours'")
    ).scalar() or 0

    total_logs = db.execute(text("SELECT COUNT(*) FROM audit_log")).scalar() or 0

    return {
        "total_audit_records": total_logs,
        "records_last_24h": recent_24h,
        "action_breakdown": [{"action": r.action, "count": r.count} for r in top_actions],
    }
