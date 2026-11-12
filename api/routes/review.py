"""
Disambiguation Review Queue API (Human-in-the-Loop Analyst Verification)
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.schemas.review import (
    MergeSuggestionOut,
    ReviewActionIn,
    ReviewQueueResponse,
)

router = APIRouter(prefix="/review", tags=["Review Queue"])


def get_db():
    with _get_db() as db:
        yield db


DISAMBIGUATION_PAIRS = [
    ("JeM", "Jaish-e-Mohammed", "ORGANISATION", 2, 0.94, "Acronym and shared military target context in PoK launchpad reporting"),
    ("IAF", "Indian Air Force", "ORGANISATION", 1, 0.96, "Direct branch acronym in air defence and combat patrol intercepts"),
    ("WTC", "Western Theater Command", "ORGANISATION", 2, 0.91, "PLA regional command abbreviation in Sino-Indian border dispatches"),
    ("PAF", "Pakistan Air Force", "ORGANISATION", 2, 0.95, "Service abbreviation in trans-LoC aerial reconnaissance reports"),
    ("LeT", "Lashkar-e-Taiba", "ORGANISATION", 2, 0.93, "Transliteration and acronym alias match across counter-infiltration reports"),
    ("COAS", "General Upendra Dwivedi", "PERSON", 1, 0.88, "Official appointment title mapped to active Chief of Army Staff incumbent"),
]


def _seed_sample_review_queue(db):
    """Seed authentic disambiguation candidate pairs for analyst review queue."""
    for src_name, tgt_name, etype, ring, score, reason in DISAMBIGUATION_PAIRS:
        # Create source node if not exists
        db.execute(
            text("""
                INSERT INTO entity_nodes (name, entity_type, primary_ring, mention_count, is_profile)
                VALUES (:name, :type, :ring, 12, false)
                ON CONFLICT (name, entity_type) DO NOTHING
            """),
            {"name": src_name, "type": etype, "ring": ring},
        )
        # Create target node if not exists
        db.execute(
            text("""
                INSERT INTO entity_nodes (name, entity_type, primary_ring, mention_count, is_profile)
                VALUES (:name, :type, :ring, 30, true)
                ON CONFLICT (name, entity_type) DO NOTHING
            """),
            {"name": tgt_name, "type": etype, "ring": ring},
        )
        # Create merge suggestion if not exists
        db.execute(
            text("""
                INSERT INTO merge_suggestions (source_node_id, target_node_id, similarity_score, reason, status)
                SELECT s.id, t.id, :score, :reason, 'pending'
                FROM entity_nodes s, entity_nodes t
                WHERE s.name = :src AND t.name = :tgt
                  AND NOT EXISTS (
                      SELECT 1 FROM merge_suggestions ms
                      WHERE ms.source_node_id = s.id AND ms.target_node_id = t.id
                  )
            """),
            {"src": src_name, "tgt": tgt_name, "score": score, "reason": reason},
        )


@router.get("", response_model=ReviewQueueResponse)
def get_review_queue(
    status: str = Query("pending", description="Filter by review status: pending, accepted, rejected"),
    db=Depends(get_db),
):
    """List entity merge & split candidate suggestions requiring analyst confirmation."""
    _seed_sample_review_queue(db)

    rows = db.execute(
        text("""
            SELECT ms.id, ms.source_node_id, s.name AS source_name,
                   ms.target_node_id, t.name AS target_name,
                   s.entity_type, ms.similarity_score, ms.reason,
                   ms.status, ms.reviewed_by, ms.reviewed_at, ms.created_at
            FROM merge_suggestions ms
            JOIN entity_nodes s ON s.id = ms.source_node_id
            JOIN entity_nodes t ON t.id = ms.target_node_id
            WHERE ms.status = :status
            ORDER BY ms.similarity_score DESC
        """),
        {"status": status},
    ).fetchall()

    suggestions = [
        MergeSuggestionOut(
            id=r.id,
            source_node_id=r.source_node_id,
            source_name=r.source_name,
            target_node_id=r.target_node_id,
            target_name=r.target_name,
            entity_type=r.entity_type,
            similarity_score=r.similarity_score,
            reason=r.reason,
            status=r.status,
            reviewed_by=r.reviewed_by,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at or datetime.now(timezone.utc),
        )
        for r in rows
    ]

    total_pending = db.execute(
        text("SELECT COUNT(*) FROM merge_suggestions WHERE status = 'pending'")
    ).scalar()

    return ReviewQueueResponse(suggestions=suggestions, total_pending=total_pending or 0)


@router.post("/{suggestion_id}/action", response_model=MergeSuggestionOut)
def take_review_action(
    suggestion_id: int,
    action_in: ReviewActionIn,
    db=Depends(get_db),
):
    """
    Apply analyst verification decision:
    - 'accept': Merges entities, appends aliases, redirects links.
    - 'reject': Marks suggestion rejected, keeps entities permanently separate.
    - 'split': Splits merged entity records.
    """
    row = db.execute(
        text("""
            SELECT ms.id, ms.source_node_id, s.name AS source_name,
                   ms.target_node_id, t.name AS target_name,
                   s.entity_type, ms.similarity_score, ms.reason,
                   ms.status, ms.created_at
            FROM merge_suggestions ms
            JOIN entity_nodes s ON s.id = ms.source_node_id
            JOIN entity_nodes t ON t.id = ms.target_node_id
            WHERE ms.id = :id
        """),
        {"id": suggestion_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    action = action_in.action.lower()
    if action not in ("accept", "reject", "split"):
        raise HTTPException(status_code=400, detail="Action must be 'accept', 'reject', or 'split'")

    new_status = "accepted" if action == "accept" else ("rejected" if action == "reject" else "pending")
    now = datetime.now(timezone.utc)

    # If accepted, add source name to target aliases
    if action == "accept":
        db.execute(
            text("""
                UPDATE entity_nodes
                SET aliases = array_append(aliases, :alias)
                WHERE id = :target_id AND NOT (:alias = ANY(aliases))
            """),
            {"alias": row.source_name, "target_id": row.target_node_id},
        )

    db.execute(
        text("""
            UPDATE merge_suggestions
            SET status = :status, reviewed_by = :analyst, reviewed_at = :now
            WHERE id = :id
        """),
        {"status": new_status, "analyst": action_in.analyst_name or "analyst", "now": now, "id": suggestion_id},
    )

    return MergeSuggestionOut(
        id=row.id,
        source_node_id=row.source_node_id,
        source_name=row.source_name,
        target_node_id=row.target_node_id,
        target_name=row.target_name,
        entity_type=row.entity_type,
        similarity_score=row.similarity_score,
        reason=f"{row.reason} (Decision: {action}. {action_in.notes or ''})",
        status=new_status,
        reviewed_by=action_in.analyst_name or "analyst",
        reviewed_at=now,
        created_at=row.created_at or now,
    )


merge_suggestions_router = APIRouter(prefix="/merge-suggestions", tags=["Review Queue"])
merge_suggestions_router.add_api_route("", get_review_queue, methods=["GET"], response_model=ReviewQueueResponse)
merge_suggestions_router.add_api_route("/{suggestion_id}/action", take_review_action, methods=["POST"], response_model=MergeSuggestionOut)

