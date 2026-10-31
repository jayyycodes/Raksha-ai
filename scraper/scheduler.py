"""
Main scraper entry point.
Run: python -m scraper.scheduler

Executes one full cycle on startup, then repeats every SCRAPE_INTERVAL_HOURS.
"""
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import text

from common.config import settings
from common.db import get_db, check_connection
from common.logger import get_logger
from scraper.rss_scraper import scrape_all_sources
from scraper.news_api import fetch_newsapi
from scraper.sources import RSS_SOURCES

logger = get_logger(__name__)


def _insert_articles(articles: list[dict]) -> tuple[int, int]:
    """Insert new articles, skip duplicates via url_hash."""
    inserted = skipped = 0

    with get_db() as db:
        existing = set(
            row[0] for row in db.execute(text("SELECT url_hash FROM articles")).fetchall()
        )

        for article in articles:
            if article["url_hash"] in existing:
                skipped += 1
                continue

            row = db.execute(
                text("SELECT id FROM sources WHERE name = :name LIMIT 1"),
                {"name": article["source_name"]},
            ).fetchone()

            db.execute(
                text("""
                    INSERT INTO articles
                        (source_id, title, content, url, url_hash, language, published_at)
                    VALUES
                        (:source_id, :title, :content, :url, :url_hash, :language, :published_at)
                    ON CONFLICT (url_hash) DO NOTHING
                """),
                {
                    "source_id":    row[0] if row else None,
                    "title":        article["title"],
                    "content":      article["content"],
                    "url":          article["url"],
                    "url_hash":     article["url_hash"],
                    "language":     article["language"],
                    "published_at": article["published_at"],
                },
            )
            existing.add(article["url_hash"])
            inserted += 1

        db.execute(text(
            "UPDATE sources SET last_scraped_at = NOW() WHERE is_active = TRUE"
        ))

    return inserted, skipped


def run_scrape_cycle():
    """One full cycle: fetch all sources → deduplicate → store."""
    start = datetime.utcnow()
    logger.info("=" * 60)
    logger.info(f"Scrape cycle started at {start.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    rss_articles = scrape_all_sources(RSS_SOURCES)
    api_articles = fetch_newsapi()
    all_articles = rss_articles + api_articles

    inserted, skipped = _insert_articles(all_articles)
    # Run the NLP pipeline on newly inserted articles
    from pipeline.runner import process_new_articles
    process_new_articles()

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(
        f"Cycle complete in {elapsed:.1f}s — "
        f"Fetched: {len(all_articles)} | Inserted: {inserted} | Skipped: {skipped}"
    )
    logger.info("=" * 60)


def _shutdown(signum, frame):
    logger.info("Shutdown signal received — stopping.")
    sys.exit(0)


def main():
    if not check_connection():
        logger.error("Cannot connect to PostgreSQL. Check DATABASE_URL in .env")
        sys.exit(1)

    logger.info(f"Raksha AI Scraper | Sources: {len(RSS_SOURCES)} RSS + NewsAPI | Interval: {settings.SCRAPE_INTERVAL_HOURS}h")

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Run immediately on startup
    run_scrape_cycle()

    # Then schedule recurring
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_scrape_cycle,
        trigger=IntervalTrigger(hours=settings.SCRAPE_INTERVAL_HOURS),
        id="scrape_cycle",
        misfire_grace_time=300,
    )
    logger.info(f"Next cycle in {settings.SCRAPE_INTERVAL_HOURS} hours. Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
