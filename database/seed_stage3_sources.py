"""
Database Seeder for Full 96 Stage 3 Monitored Sources.
Owner: Platform & Engineering
Stage: 3 Solid (Milestone M7 & M9)
"""
from sqlalchemy import text
from common.db import get_db
from common.logger import get_logger
from scraper.sources_stage3 import STAGE3_SOURCES_96

logger = get_logger(__name__)


def seed_96_sources():
    """Upsert all 96 Stage 3 sources into the PostgreSQL database."""
    with get_db() as db:
        inserted = 0
        updated = 0
        for src in STAGE3_SOURCES_96:
            name = src["name"]
            url = src.get("url", "")
            rss_url = src.get("rss_url") or src.get("api_endpoint") or src.get("url", "")
            ring = src["ring"]
            country = src.get("country", "India")
            language = src.get("language", "en")
            source_type = src.get("source_type", "rss")

            row = db.execute(
                text("SELECT id FROM sources WHERE name = :name"),
                {"name": name},
            ).fetchone()

            if row:
                db.execute(
                    text("""
                        UPDATE sources
                        SET url = :url,
                            rss_url = :rss_url,
                            ring = :ring,
                            country = :country,
                            language = :language,
                            source_type = :source_type,
                            is_active = TRUE
                        WHERE id = :id
                    """),
                    {
                        "id": row[0],
                        "url": url,
                        "rss_url": rss_url,
                        "ring": ring,
                        "country": country,
                        "language": language,
                        "source_type": source_type,
                    },
                )
                updated += 1
            else:
                db.execute(
                    text("""
                        INSERT INTO sources (name, url, rss_url, ring, country, language, source_type, is_active)
                        VALUES (:name, :url, :rss_url, :ring, :country, :language, :source_type, TRUE)
                    """),
                    {
                        "name": name,
                        "url": url,
                        "rss_url": rss_url,
                        "ring": ring,
                        "country": country,
                        "language": language,
                        "source_type": source_type,
                    },
                )
                inserted += 1

        db.commit()

        # Synchronize source_health entries for all sources
        db.execute(text("""
            INSERT INTO source_health (source_id, last_fetched, last_success, status, article_count, retries)
            SELECT s.id, NULL, NULL, 'empty', 0, 0
            FROM sources s
            LEFT JOIN source_health sh ON sh.source_id = s.id
            WHERE sh.source_id IS NULL
        """))
        db.commit()

        total = db.execute(text("SELECT COUNT(*) FROM sources")).scalar()
        logger.info(f"Seeded 96 sources: {inserted} inserted, {updated} updated. Total sources in DB: {total}")
        print(f"Seeded 96 sources: {inserted} inserted, {updated} updated. Total sources in DB: {total}")
        return total


if __name__ == "__main__":
    seed_96_sources()
