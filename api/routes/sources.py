"""
GET /api/sources        — all sources with last scraped time
GET /api/sources/health — per-source freshness and health status
Owner: Jay | Stage: 1 MVP
"""
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
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
            SELECT s.id,
                   s.id AS source_id,
                   s.name,
                   s.ring,
                   s.language,
                   s.country,
                   s.url,
                   s.url AS source_url,
                   s.rss_url,
                   COALESCE(sh.last_fetched, MAX(a.scraped_at), s.last_scraped_at) AS last_collected_at,
                   COALESCE(sh.last_fetched, MAX(a.scraped_at), s.last_scraped_at) AS last_fetched,
                   COALESCE(sh.last_success, MAX(a.scraped_at), s.last_scraped_at) AS last_success_at,
                   COALESCE(sh.last_success, MAX(a.scraped_at), s.last_scraped_at) AS last_success,
                   COUNT(a.id) AS total_articles,
                   COUNT(a.id) AS article_count,
                   COUNT(a.id) FILTER (WHERE a.scraped_at >= NOW() - INTERVAL '24 hours' OR a.published_at >= NOW() - INTERVAL '24 hours') AS articles_today,
                   CASE
                       WHEN NOT s.is_active THEN 'failed'
                       WHEN sh.last_error IS NOT NULL OR COALESCE(sh.retries, 0) >= 3 OR sh.status = 'failed' THEN 'failed'
                       WHEN COUNT(a.id) = 0 THEN 'empty'
                       WHEN COUNT(a.id) > 0 AND (
                           COUNT(a.id) FILTER (WHERE a.scraped_at >= NOW() - INTERVAL '24 hours' OR a.published_at >= NOW() - INTERVAL '24 hours') > 0
                           OR COALESCE(sh.last_success, MAX(a.scraped_at), s.last_scraped_at) >= NOW() - INTERVAL '48 hours'
                       ) THEN 'ok'
                       ELSE 'stale'
                   END AS status,
                   sh.last_error,
                   COALESCE(sh.retries, 0) AS retries
            FROM sources s
            LEFT JOIN source_health sh ON sh.source_id = s.id
            LEFT JOIN articles a ON a.source_id = s.id
            GROUP BY s.id, s.name, s.ring, s.language, s.country, s.url, s.rss_url, s.is_active,
                     sh.last_fetched, sh.last_success, sh.status, sh.last_error, sh.retries, s.last_scraped_at
            ORDER BY s.ring ASC, s.name ASC
        """)
    ).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/refresh")
def trigger_sources_refresh(background_tasks: BackgroundTasks):
    """
    On-demand live intelligence refresh:
    Triggers an immediate scrape cycle across all monitored sources,
    deduplicates and processes new articles through the NLP pipeline.
    """
    from scraper.scheduler import run_scrape_cycle
    background_tasks.add_task(run_scrape_cycle)
    return {
        "status": "triggered",
        "message": "Live scrape cycle initiated across all monitored intelligence sources.",
    }


# ── Stage 3 Connector Framework Endpoints (Milestone M7) ───────────────

@router.get("/connectors")
def list_connectors():
    """
    Stage 3 Connector Registry inspection:
    Lists all 96+ plug-in connectors across Rings 1–4, APIs, and Social/Telegram.
    """
    from connectors.registry import registry
    registry.populate_stage3_sources()
    return {
        "total_connectors": registry.total_count(),
        "connectors": [c.to_dict() for c in registry.list_connectors()],
    }


@router.get("/connectors/health")
def connectors_health_report(limit: Optional[int] = None):
    """
    Health checks across active connectors (executed concurrently).
    Optional query param `limit` (e.g. ?limit=10) to probe a subset for rapid UI checks.
    """
    from connectors.registry import registry
    registry.populate_stage3_sources()
    return {
        "total": registry.total_count(),
        "report": registry.health_report(limit=limit),
    }


@router.post("/connectors/{connector_name}/trigger")
def trigger_connector_ingestion(connector_name: str, background_tasks: BackgroundTasks):
    """
    On-demand ingestion from a single plug-in connector.
    """
    from connectors.registry import registry
    registry.populate_stage3_sources()
    conn = registry.get(connector_name)
    if not conn:
        return {"status": "error", "message": f"Connector '{connector_name}' not found."}

    def _task():
        items = conn.fetch_articles()
        return len(items)

    background_tasks.add_task(_task)
    return {
        "status": "triggered",
        "connector": connector_name,
        "source_type": conn.source_type,
    }
