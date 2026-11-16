"""
Immutable Audit Logging — Raksha AI Stage 3 Solid
Records all security-relevant and analyst-initiated actions to PostgreSQL audit_log.
"""
import json
from typing import Optional, Any, Dict
from sqlalchemy import text
from common.logger import get_logger

logger = get_logger(__name__)


def log_audit_event(
    db,
    action: str,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Append-only audit record writer.
    Never fails the calling request if logging fails, but logs warning.
    """
    try:
        row = db.execute(
            text("""
                INSERT INTO audit_log (
                    user_id, action, entity_type, entity_id, ip_address, user_agent, details, created_at
                ) VALUES (
                    :user_id, :action, :entity_type, :entity_id, :ip_address, :user_agent, CAST(:details AS jsonb), NOW()
                )
                RETURNING id
            """),
            {
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id is not None else None,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "details": json.dumps(details or {}),
            },
        ).fetchone()
        db.commit()
        return row[0] if row else None
    except Exception as exc:
        logger.warning(f"Failed to record audit event '{action}': {exc}")
        return None
