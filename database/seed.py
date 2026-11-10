"""
Seeds the sources table from scraper/sources.py
Run: python -m database.seed
"""
from sqlalchemy import text
from common.db import get_db
from common.logger import get_logger
from scraper.sources import RSS_SOURCES

logger = get_logger(__name__)


def seed_sources():
    with get_db() as db:
        inserted = 0
        for source in RSS_SOURCES:
            result = db.execute(
                text("""
                    INSERT INTO sources (name, url, rss_url, ring, country, language)
                    VALUES (:name, :url, :rss_url, :ring, :country, :language)
                    ON CONFLICT (name) DO UPDATE SET
                        url = EXCLUDED.url,
                        rss_url = EXCLUDED.rss_url,
                        ring = EXCLUDED.ring,
                        country = EXCLUDED.country,
                        language = EXCLUDED.language
                """),
                source,
            )
            if result.rowcount:
                inserted += 1
        logger.info(
            f"Seeded / updated {inserted} sources "
            f"({len(RSS_SOURCES)} total in registry)"
        )


if __name__ == "__main__":
    seed_sources()
