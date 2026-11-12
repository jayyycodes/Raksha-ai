"""
Watchlists API routes — Analyst-Configured Monitoring Rules.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)

Endpoints:
    GET    /api/watchlists       -> all analyst watchlists + recent match counts
    POST   /api/watchlists       -> create a new region/entity/keyword watchlist
    PATCH  /api/watchlists/{id}  -> toggle active/paused status
    DELETE /api/watchlists/{id}  -> delete a watchlist
"""
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from common.db import get_db as _get_db
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


def get_db():
    with _get_db() as db:
        yield db


class WatchlistCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    query_type: Literal["entity", "region", "keyword"]
    query_value: str = Field(..., min_length=2, max_length=255)


class WatchlistToggleIn(BaseModel):
    is_active: bool


@router.get("")
def list_watchlists(db=Depends(get_db)):
    """Return all configured watchlists with recent matched alert counts and live article hit counts."""
    rows = db.execute(
        text("""
            SELECT w.id, w.name, w.query_type, w.query_value, w.is_active, w.created_at,
                   COUNT(al.id) AS alert_count,
                   MAX(al.triggered_at) AS last_triggered_at
            FROM watchlists w
            LEFT JOIN alerts al ON al.watchlist_id = w.id
            GROUP BY w.id
            ORDER BY w.created_at DESC, w.id DESC
        """)
    ).fetchall()

    items = []
    for r in rows:
        # Also calculate direct recent matching article count for instant analyst context
        qpattern = f"%{r.query_value}%"
        art_matches = db.execute(
            text("""
                SELECT a.id, a.title, a.published_at, s.name AS source_name
                FROM articles a
                LEFT JOIN sources s ON s.id = a.source_id
                WHERE a.title ILIKE :qp OR a.content ILIKE :qp
                ORDER BY a.published_at DESC
                LIMIT 5
            """),
            {"qp": qpattern},
        ).fetchall()

        items.append(
            {
                "id": r.id,
                "name": r.name,
                "query_type": r.query_type,
                "query_value": r.query_value,
                "is_active": bool(r.is_active),
                "created_at": r.created_at,
                "alert_count": int(r.alert_count or 0),
                "last_triggered_at": r.last_triggered_at,
                "recent_matches": [
                    {
                        "article_id": m.id,
                        "title": m.title,
                        "source_name": m.source_name or "Open Source Wire",
                        "published_at": m.published_at,
                    }
                    for m in art_matches
                ],
            }
        )

    return {"watchlists": items, "total": len(items)}


@router.post("")
def create_watchlist(payload: WatchlistCreateIn, db=Depends(get_db)):
    """Create a new watchlist and run an initial check against recent articles."""
    row = db.execute(
        text("""
            INSERT INTO watchlists (name, query_type, query_value, is_active, created_at)
            VALUES (:name, :qtype, :qval, TRUE, NOW())
            RETURNING id, name, query_type, query_value, is_active, created_at
        """),
        {
            "name": payload.name.strip(),
            "qtype": payload.query_type,
            "qval": payload.query_value.strip(),
        },
    ).fetchone()
    db.commit()

    # Scan immediately so matching alerts appear right away
    try:
        from report.anomaly import detect_anomalies

        detect_anomalies(window_hours=72)
    except Exception as exc:
        logger.debug("Immediate watchlist alert check skipped: %s", exc)

    return {
        "id": row.id,
        "name": row.name,
        "query_type": row.query_type,
        "query_value": row.query_value,
        "is_active": bool(row.is_active),
        "created_at": row.created_at,
    }


@router.patch("/{watchlist_id}")
def toggle_watchlist(watchlist_id: int, payload: WatchlistToggleIn, db=Depends(get_db)):
    """Enable or pause a watchlist."""
    row = db.execute(
        text("""
            UPDATE watchlists
            SET is_active = :active
            WHERE id = :wid
            RETURNING id, name, query_type, query_value, is_active, created_at
        """),
        {"active": payload.is_active, "wid": watchlist_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {
        "id": row.id,
        "name": row.name,
        "query_type": row.query_type,
        "query_value": row.query_value,
        "is_active": bool(row.is_active),
        "created_at": row.created_at,
    }


@router.delete("/{watchlist_id}")
def delete_watchlist(watchlist_id: int, db=Depends(get_db)):
    """Remove an analyst watchlist."""
    row = db.execute(
        text("DELETE FROM watchlists WHERE id = :wid RETURNING id"),
        {"wid": watchlist_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"deleted": True, "id": watchlist_id}

