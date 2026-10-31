"""
GET /api/stats — summary counts for the dashboard
Owner: Jay | Stage: 1 MVP
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text

from common.db import get_db as _get_db

router = APIRouter(prefix="/stats", tags=["Stats"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def get_stats(db=Depends(get_db)):
    """Dashboard summary: total articles, today, per-ring, per-source, last scrape."""
    total = db.execute(text("SELECT COUNT(*) FROM articles")).scalar()
    today = db.execute(
        text("SELECT COUNT(*) FROM articles WHERE published_at >= NOW() - INTERVAL '24 hours'")
    ).scalar()
    processed = db.execute(text("SELECT COUNT(*) FROM articles WHERE is_processed = TRUE")).scalar()

    per_ring = db.execute(
        text("""
            SELECT s.ring, COUNT(a.id) AS count
            FROM articles a JOIN sources s ON s.id = a.source_id
            GROUP BY s.ring ORDER BY s.ring
        """)
    ).fetchall()

    per_source = db.execute(
        text("""
            SELECT s.id, s.name, COUNT(a.id) AS count
            FROM articles a JOIN sources s ON s.id = a.source_id
            GROUP BY s.id, s.name ORDER BY count DESC LIMIT 15
        """)
    ).fetchall()

    last_scrape = db.execute(
        text("SELECT MAX(last_scraped_at) FROM sources WHERE is_active = TRUE")
    ).scalar()

    event_types = db.execute(
        text("""
            SELECT event_type, COUNT(*) AS count
            FROM article_analysis
            WHERE event_type IS NOT NULL
            GROUP BY event_type ORDER BY count DESC
        """)
    ).fetchall()

    return {
        "total_articles": total,
        "todays_articles": today,
        "processed_articles": processed,
        "last_scrape_at": str(last_scrape) if last_scrape else None,
        "per_ring": {r.ring: r.count for r in per_ring},
        "per_source": [{"id": r.id, "name": r.name, "count": r.count} for r in per_source],
        "event_type_breakdown": {r.event_type: r.count for r in event_types},
    }
