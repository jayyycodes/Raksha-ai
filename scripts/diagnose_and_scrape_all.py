"""
Diagnose all 40 RSS sources, fetch live articles from working feeds,
insert into PostgreSQL, run pipeline, and record source health.
"""
import socket
socket.setdefaulttimeout(12.0)

import feedparser
import requests
from datetime import datetime, timezone
from sqlalchemy import text
from common.db import get_db
from scraper.sources import RSS_SOURCES
from scraper.rss_scraper import _parse_date, _detect_language
import hashlib

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 RakshaAI/1.0"

def test_and_scrape():
    print(f"Testing and scraping all {len(RSS_SOURCES)} sources...")
    results = []

    with get_db() as db:
        # Get existing source records from DB
        db_sources = {
            r.name: r.id for r in db.execute(text("SELECT id, name FROM sources")).fetchall()
        }

        # Existing url_hashes to prevent duplicates
        existing_hashes = set(
            r[0] for r in db.execute(text("SELECT url_hash FROM articles")).fetchall()
        )

        total_inserted = 0

        for i, s in enumerate(RSS_SOURCES):
            name = s["name"]
            rss_url = s["rss_url"]
            ring = s["ring"]
            lang = s.get("language", "en")
            source_id = db_sources.get(name)

            print(f"[{i+1}/{len(RSS_SOURCES)}] Checking {name} ({rss_url[:45]}...)...")

            try:
                # Custom request with Chrome User-Agent to prevent 403 blocks
                resp = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=10)
                if resp.status_code != 200:
                    status = "failed"
                    err = f"HTTP {resp.status_code}"
                    articles_found = 0
                else:
                    feed = feedparser.parse(resp.content)
                    articles_found = len(feed.entries)
                    status = "ok" if articles_found > 0 else "empty"
                    err = None

                    # Insert articles if found
                    inserted_this_source = 0
                    for entry in feed.entries[:25]: # up to 25 latest per feed
                        title = getattr(entry, "title", "").strip()
                        url = getattr(entry, "link", "").strip()
                        if not title or not url:
                            continue
                        uhash = hashlib.md5(url.encode("utf-8")).hexdigest()
                        if uhash in existing_hashes:
                            continue

                        raw_content = (getattr(entry, "summary", "") or getattr(entry, "description", "") or "").strip()
                        safe_summary = raw_content[:500] if raw_content else title
                        pub_at = _parse_date(entry)
                        detected_lang = _detect_language(safe_summary or title, lang)

                        db.execute(text("""
                            INSERT INTO articles (source_id, title, content, url, url_hash, language, published_at, is_processed)
                            VALUES (:sid, :title, :content, :url, :uhash, :lang, :pub, FALSE)
                            ON CONFLICT (url_hash) DO NOTHING
                        """), {
                            "sid": source_id,
                            "title": title[:500],
                            "content": safe_summary,
                            "url": url[:1000],
                            "uhash": uhash,
                            "lang": detected_lang[:10],
                            "pub": pub_at,
                        })
                        existing_hashes.add(uhash)
                        inserted_this_source += 1
                        total_inserted += 1

                # Update sources table & source_health table
                if source_id:
                    db.execute(text("""
                        UPDATE sources
                        SET last_scraped_at = NOW()
                        WHERE id = :sid
                    """), {"sid": source_id})

                    db.execute(text("""
                        INSERT INTO source_health (
                            source_id, last_fetched, last_success, article_count, status, last_error
                        ) VALUES (
                            :sid, NOW(), CASE WHEN :status = 'ok' THEN NOW() ELSE NULL END, :cnt, :status, :err
                        )
                        ON CONFLICT (source_id) DO UPDATE SET
                            last_fetched = NOW(),
                            last_success = CASE WHEN EXCLUDED.status = 'ok' THEN NOW() ELSE source_health.last_success END,
                            article_count = source_health.article_count + EXCLUDED.article_count,
                            status = EXCLUDED.status,
                            last_error = EXCLUDED.last_error
                    """), {
                        "sid": source_id,
                        "status": status,
                        "cnt": articles_found,
                        "err": err,
                    })

                db.commit()
                print(f"    -> Status: {status} | Found: {articles_found} | New Inserted: {inserted_this_source}")

            except Exception as e:
                db.rollback()
                print(f"    -> Failed: {e}")
                if source_id:
                    try:
                        db.execute(text("""
                            UPDATE sources SET last_scraped_at = NOW() WHERE id = :sid
                        """), {"sid": source_id})
                        db.execute(text("""
                            INSERT INTO source_health (source_id, last_fetched, status, last_error)
                            VALUES (:sid, NOW(), 'failed', :err)
                            ON CONFLICT (source_id) DO UPDATE SET
                                last_fetched = NOW(),
                                status = 'failed',
                                last_error = :err
                        """), {"sid": source_id, "err": str(e)[:250]})
                        db.commit()
                    except Exception:
                        db.rollback()

        print(f"\n==========================================")
        print(f"Completed scrape: {total_inserted} brand new live articles inserted!")
        total_arts = db.execute(text("SELECT count(*) FROM articles")).scalar()
        unprocessed = db.execute(text("SELECT count(*) FROM articles WHERE is_processed = FALSE")).scalar()
        print(f"Total articles in DB: {total_arts} (Unprocessed: {unprocessed})")

if __name__ == "__main__":
    test_and_scrape()
