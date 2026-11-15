"""
Alerts API routes — Anomaly Detection & Watchlist Alert Feed.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)

Endpoints:
    GET  /api/alerts            -> anomaly and watchlist alert feed
    POST /api/alerts/{id}/read  -> acknowledge/mark alert as read
    POST /api/alerts/scan       -> trigger an immediate anomaly & watchlist scan
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def list_alerts(
    unread_only: bool = Query(False, description="Return only unread alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    alert_type: Optional[str] = Query(None, description="Filter by type: VOLUME_SPIKE, THREAT_ESCALATION, SENTIMENT_ANOMALY, WATCHLIST_MATCH"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """Anomaly and watchlist alerts feed ordered by most recent first."""
    where_clauses = []
    params: dict = {"limit": limit}

    if unread_only:
        where_clauses.append("is_read = FALSE")
    if severity and severity.lower() != "all":
        where_clauses.append("LOWER(severity) = :severity")
        params["severity"] = severity.lower()
    if alert_type and alert_type.lower() != "all":
        where_clauses.append("UPPER(alert_type) = :atype")
        params["atype"] = alert_type.upper()

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = db.execute(
        text(f"""
            SELECT id, alert_type, region, description, severity, is_read,
                   triggered_at, watchlist_id, source_article_ids
            FROM alerts
            {where_sql}
            ORDER BY triggered_at DESC, id DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    unread_count = db.execute(
        text("SELECT COUNT(*) FROM alerts WHERE is_read = FALSE")
    ).scalar() or 0

    alerts = [
        {
            "id": r.id,
            "alert_type": r.alert_type or "ANOMALY",
            "region": r.region or "Multi-Region",
            "description": r.description,
            "severity": r.severity or "low",
            "is_read": bool(r.is_read),
            "triggered_at": r.triggered_at,
            "watchlist_id": r.watchlist_id,
            "source_article_ids": list(r.source_article_ids or []),
        }
        for r in rows
    ]

    return {
        "alerts": alerts,
        "total": len(alerts),
        "unread_count": int(unread_count),
    }


@router.post("/{alert_id}/read")
def mark_alert_read(alert_id: int, db=Depends(get_db)):
    """Mark a single alert as acknowledged/read."""
    row = db.execute(
        text("UPDATE alerts SET is_read = TRUE WHERE id = :aid RETURNING id, is_read"),
        {"aid": alert_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": row.id, "is_read": True}


@router.post("/scan")
def trigger_anomaly_scan():
    """
    Full real-time intelligence refresh:
    1. Ingests and processes new articles through Stage 2 NLP pipeline
    2. Recalculates regional threat scores across all 9 operational theatres (updates 30-day trajectory)
    3. Executes anomaly and watchlist detection
    """
    from pipeline.runner import process_new_articles
    from report.scorer import calculate_threat_scores
    from report.anomaly import detect_anomalies

    # 1. Process all pending / incoming articles through NLP pipeline
    processed_count = process_new_articles(run_batch_intelligence=False)

    # 2. Recalculate regional threat scores (appends new historical data point to threat_scores)
    fresh_scores = calculate_threat_scores(window_hours=24)

    # 3. Detect anomalies and watchlist triggers
    new_alerts = detect_anomalies(window_hours=24)

    return {
        "scanned": True,
        "processed_articles": processed_count,
        "threat_scores_updated": len(fresh_scores),
        "new_alerts_count": len(new_alerts),
        "new_alerts": new_alerts,
    }
