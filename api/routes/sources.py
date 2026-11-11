"""
GET /api/sources        — all sources with last scraped time
GET /api/sources/health — per-source freshness and health status
Owner: Jay | Stage: 1 MVP
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text

from common.db import get_db as _get_db

router = APIRouter(prefix="/sources", tags=["Sources"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("")
def list_sources(db=Depends(get_db)):
    """All monitored sources with metadata and last scrape time."""
    rows = db.execute(
        text("""
            SELECT s.id, s.name, s.url, s.rss_url, s.ring, s.country, s.language,
                   s.is_active, s.last_scraped_at,
                   COUNT(a.id) AS total_articles,
                   COUNT(a.id) FILTER (WHERE a.published_at >= NOW() - INTERVAL '24 hours') AS articles_today
            FROM sources s
            LEFT JOIN articles a ON a.source_id = s.id
            GROUP BY s.id
            ORDER BY s.ring, s.name
        """)
    ).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/health")
def sources_health(db=Depends(get_db)):
    """Per-source freshness across all registered monitoring outlets."""
    rows = db.execute(
        text("""
            SELECT s.id AS source_id, s.name, s.ring, s.language, s.country, s.url, s.rss_url,
                   COALESCE(sh.last_fetched, s.last_scraped_at) AS last_fetched,
                   COALESCE(sh.last_success, s.last_scraped_at) AS last_success,
                   COALESCE(sh.article_count, COUNT(a.id)) AS article_count,
                   COALESCE(sh.status, CASE WHEN s.is_active THEN 'operational' ELSE 'inactive' END) AS status
            FROM sources s
            LEFT JOIN source_health sh ON sh.source_id = s.id
            LEFT JOIN articles a ON a.source_id = s.id
            GROUP BY s.id, s.name, s.ring, s.language, s.country, s.url, s.rss_url, sh.last_fetched, sh.last_success, sh.article_count, sh.status
            ORDER BY s.ring ASC, s.name ASC
        """)
    ).fetchall()
    return [dict(r._mapping) for r in rows]
