"""
Pipeline Runner — Jay (MVP Stage 1)
Fetches unprocessed articles from the DB, runs them through the agent chain,
stores analysis results, and marks articles processed.

Agent chain (MVP stubs):
    Translation → Extraction → Threat Scoring
"""
import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import text

from common.db import get_db
from common.schemas.articles import ArticleIn, ArticleAnalysisOut
from common.schemas.intelligence import ThreatClassifyIn
from common.schemas.provenance import ClaimStatus, Provenance, SourceType

from agents.translation.stub import TranslationAgentStub
from agents.extraction.stub import ExtractionAgentStub
from agents.scoring.classifier_v0 import ThreatClassifierV0

logger = logging.getLogger(__name__)

# Initialise agents once (stateless stubs — safe to reuse)
_translation = TranslationAgentStub()
_extraction = ExtractionAgentStub()
_scoring = ThreatClassifierV0()


def _fetch_unprocessed(db) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT a.id, a.source_id, a.title, a.content, a.url, a.url_hash,
                   a.language, a.published_at, s.ring
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            WHERE a.is_processed = FALSE
            LIMIT 200
        """)
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def _store_analysis(db, result: dict):
    """Insert or update one row in article_analysis."""
    db.execute(
        text("""
            INSERT INTO article_analysis (
                article_id, translated_text, event_type, sentiment, threat_level,
                method, model_version, source_ids, confidence, created_at
            ) VALUES (
                :article_id, :translated_text, :event_type, :sentiment, :threat_level,
                :method, :model_version, :source_ids, :confidence, :created_at
            )
            ON CONFLICT (article_id) DO UPDATE SET
                translated_text = EXCLUDED.translated_text,
                event_type      = EXCLUDED.event_type,
                sentiment       = EXCLUDED.sentiment,
                threat_level    = EXCLUDED.threat_level,
                method          = EXCLUDED.method,
                model_version   = EXCLUDED.model_version,
                source_ids      = EXCLUDED.source_ids,
                confidence      = EXCLUDED.confidence,
                created_at      = EXCLUDED.created_at
        """),
        result,
    )


def _update_source_health(db, source_id: int, article_id: int):
    """Upsert the source_health row for the given source."""
    if not source_id:
        return
    db.execute(
        text("""
            INSERT INTO source_health (source_id, last_fetched, last_success, article_count, status)
            VALUES (:sid, NOW(), NOW(), 1, 'ok')
            ON CONFLICT (source_id) DO UPDATE SET
                last_fetched  = NOW(),
                last_success  = NOW(),
                article_count = source_health.article_count + 1,
                status        = 'ok'
        """),
        {"sid": source_id},
    )


def process_new_articles():
    """Entry point — called by the scraper scheduler after each scrape cycle."""
    with get_db() as db:
        rows = _fetch_unprocessed(db)
        if not rows:
            logger.info("Pipeline: no unprocessed articles.")
            return

        logger.info(f"Pipeline: processing {len(rows)} articles.")
        processed_ids = []

        for row in rows:
            article_in = ArticleIn(
                id=row["id"],
                source_id=row["source_id"],
                title=row["title"],
                content=row["content"] or "",
                url=row["url"],
                url_hash=row["url_hash"],
                language=row["language"] or "en",
                ring=row.get("ring") or 1,
                published_at=row["published_at"],
            )

            # 1️⃣ Translation
            trans_out = _translation.run(article_in)

            # 2️⃣ Extraction — pass translated content
            article_for_extract = article_in.model_copy(
                update={"content": trans_out.get("translated_text") or article_in.content}
            )
            extract_out = _extraction.run(article_for_extract)

            # 3️⃣ Threat Scoring
            threat_in = ThreatClassifyIn(
                title=article_in.title,
                content=article_for_extract.content,
                event_type=extract_out.event_type,
                ring=article_in.ring,
            )
            threat_out = _scoring.run(threat_in)

            # Merge everything into one DB row
            analysis_row = {
                "article_id":     article_in.id,
                "translated_text": trans_out.get("translated_text"),
                "event_type":     extract_out.event_type,
                "sentiment":      extract_out.sentiment,
                "threat_level":   threat_out.threat_level,
                "method":         "stub_pipeline_v0",
                "model_version":  f"trans:{_translation.version}|extr:{_extraction.version}|score:{_scoring.version}",
                "source_ids":     [article_in.id] if article_in.id else [],
                "confidence":     threat_out.provenance.confidence,
                "created_at":     datetime.now(timezone.utc),
            }
            _store_analysis(db, analysis_row)
            _update_source_health(db, row.get("source_id"), row["id"])
            processed_ids.append(row["id"])

        # Mark all processed
        if processed_ids:
            db.execute(
                text("UPDATE articles SET is_processed = TRUE WHERE id = ANY(:ids)"),
                {"ids": processed_ids},
            )

        logger.info(f"Pipeline: done — {len(processed_ids)} articles processed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_new_articles()
