"""
Stage 2 NLP & Ontology Pipeline Runner — Jay (Lead) + Ary (NLP)
Orchestrates the full multi-stage intelligence pipeline for unprocessed articles:
    1. Translation (TranslationAgent)
    2. NER & Event Classification (ExtractionAgent)
    3. Article Threat Scoring (ThreatClassifierV0)
    4. 768-d Semantic Embeddings (engine.embeddings -> article_embeddings)
    5. Entity Resolution & Disambiguation (ResolutionAgent -> entity_nodes, entity_links, merge_suggestions)
    6. Event Threading (ThreadingAgent -> events, event_articles)
    7. Batch Regional Threat Scoring & Anomaly/Watchlist Alerts (report.scorer + report.anomaly)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from agents.extraction.agent import ExtractionAgent
from agents.resolution.agent import ResolutionAgent
from agents.scoring.classifier_v0 import ThreatClassifierV0
from agents.scoring.regional_scorer import map_article_to_regions
from agents.threading.agent import ThreadingAgent
from agents.translation.agent import TranslationAgent
from common.db import get_db
from common.schemas.articles import ArticleIn
from common.schemas.events import EventThreadingIn
from common.schemas.intelligence import ThreatClassifyIn

logger = logging.getLogger(__name__)

# Lazy-initialized shared agent singletons
_translation: Optional[TranslationAgent] = None
_extraction: Optional[ExtractionAgent] = None
_scoring: Optional[ThreatClassifierV0] = None
_resolution: Optional[ResolutionAgent] = None


def _get_agents() -> Tuple[TranslationAgent, ExtractionAgent, ThreatClassifierV0, ResolutionAgent]:
    global _translation, _extraction, _scoring, _resolution
    if _translation is None:
        _translation = TranslationAgent()
    if _extraction is None:
        _extraction = ExtractionAgent()
    if _scoring is None:
        _scoring = ThreatClassifierV0()
    if _resolution is None:
        _resolution = ResolutionAgent()
    return _translation, _extraction, _scoring, _resolution


def _fetch_unprocessed(db, limit: int = 200) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT a.id, a.source_id, a.title, a.content, a.url, a.url_hash,
                   a.language, a.published_at, COALESCE(s.ring, 1) AS ring
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            WHERE a.is_processed = FALSE
            ORDER BY a.published_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def _fetch_article_by_id(db, article_id: int) -> Optional[dict]:
    row = db.execute(
        text("""
            SELECT a.id, a.source_id, a.title, a.content, a.url, a.url_hash,
                   a.language, a.published_at, COALESCE(s.ring, 1) AS ring
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            WHERE a.id = :aid
        """),
        {"aid": article_id},
    ).fetchone()
    return dict(row._mapping) if row else None


def _store_analysis(db, result: dict) -> None:
    """Insert or update one row in article_analysis with full Stage 2 provenance."""
    db.execute(
        text("""
            INSERT INTO article_analysis (
                article_id, translated_text, event_type, sentiment, threat_level,
                method, model_version, source_ids, confidence, claim_status, source_type, created_at
            ) VALUES (
                :article_id, :translated_text, :event_type, :sentiment, :threat_level,
                :method, :model_version, :source_ids, :confidence, 'reported', 'public', :created_at
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
                claim_status    = EXCLUDED.claim_status,
                source_type     = EXCLUDED.source_type,
                created_at      = EXCLUDED.created_at
        """),
        result,
    )


def _store_embedding(db, article_id: int, text_for_embedding: str) -> bool:
    """Generate and persist 768-dim semantic embedding when model is available."""
    if not text_for_embedding.strip():
        return False
    try:
        from engine.embeddings import DEFAULT_MODEL, generate_embedding

        vec = generate_embedding(text_for_embedding)
        vec_literal = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        db.execute(
            text("""
                INSERT INTO article_embeddings (article_id, embedding, model_used, created_at)
                VALUES (:aid, CAST(:vec AS vector), :model, NOW())
                ON CONFLICT (article_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    model_used = EXCLUDED.model_used
            """),
            {"aid": article_id, "vec": vec_literal, "model": DEFAULT_MODEL[:50]},
        )
        return True
    except Exception as exc:
        logger.debug("Skipping embedding persistence for article %s (%s)", article_id, exc)
        return False


def _upsert_entity_node(
    db,
    name: str,
    entity_type: str,
    ring: int,
    alias: Optional[str] = None,
) -> int:
    """Upsert entity_node and enforce the candidate-to-profile promotion rule (>=3 mentions, >=2 sources)."""
    existing = db.execute(
        text("""
            SELECT id, mention_count, source_count, aliases, is_profile
            FROM entity_nodes
            WHERE name = :name AND entity_type = :etype
        """),
        {"name": name, "etype": entity_type},
    ).fetchone()

    if existing:
        new_mentions = int(existing.mention_count or 0) + 1
        new_sources = max(int(existing.source_count or 1), 1)
        aliases = list(existing.aliases or [])
        if alias and alias not in aliases:
            aliases.append(alias)
        promote = bool(existing.is_profile) or (new_mentions >= 3 and new_sources >= 2)
        db.execute(
            text("""
                UPDATE entity_nodes
                SET mention_count = :mentions,
                    aliases = :aliases,
                    is_profile = :is_profile,
                    last_seen_at = NOW()
                WHERE id = :nid
            """),
            {
                "mentions": new_mentions,
                "aliases": aliases,
                "is_profile": promote,
                "nid": existing.id,
            },
        )
        return int(existing.id)

    aliases_init = [alias] if alias and alias != name else [name]
    row = db.execute(
        text("""
            INSERT INTO entity_nodes (
                name, entity_type, aliases, primary_ring, mention_count, source_count, is_profile
            ) VALUES (
                :name, :etype, :aliases, :ring, 1, 1, FALSE
            )
            ON CONFLICT (name, entity_type) DO UPDATE SET
                mention_count = entity_nodes.mention_count + 1,
                last_seen_at = NOW()
            RETURNING id
        """),
        {
            "name": name[:255],
            "etype": entity_type[:50],
            "aliases": aliases_init,
            "ring": max(1, min(4, int(ring or 1))),
        },
    ).fetchone()
    return int(row.id)


def _persist_entities_and_links(
    db,
    article_id: int,
    ring: int,
    entities: list,
    resolution_agent: ResolutionAgent,
    context_text: str,
) -> List[int]:
    """Store raw entities, execute 3-tier disambiguation, and create co-occurrence links."""
    if not entities:
        return []

    # Replace raw entity extraction rows for this article cleanly
    db.execute(text("DELETE FROM entities WHERE article_id = :aid"), {"aid": article_id})
    mentions_payload = []
    for ent in entities:
        db.execute(
            text("""
                INSERT INTO entities (article_id, entity_type, entity_value, confidence)
                VALUES (:aid, :etype, :eval, :conf)
            """),
            {
                "aid": article_id,
                "etype": ent.entity_type[:30],
                "eval": ent.entity_value[:200],
                "conf": float(ent.confidence),
            },
        )
        mentions_payload.append(
            {
                "entity_value": ent.entity_value,
                "entity_type": ent.entity_type,
                "context": context_text[:300],
            }
        )

    resolved = resolution_agent.run(mentions_payload).get("resolved_entities", [])
    resolved_node_ids: List[Tuple[int, str]] = []

    for item in resolved:
        action = item.get("action", "separate")
        raw_name = (item.get("raw_name") or "").strip()
        canonical_name = (item.get("canonical_name") or raw_name).strip()
        etype = item.get("entity_type") or "ORGANISATION"
        conf = float(item.get("confidence", 0.5))

        if not canonical_name:
            continue

        if action == "auto_link":
            nid = _upsert_entity_node(db, canonical_name, etype, ring, alias=raw_name)
            resolved_node_ids.append((nid, etype))
        elif action == "review_queue" and raw_name and raw_name.lower() != canonical_name.lower():
            src_id = _upsert_entity_node(db, raw_name, etype, ring)
            tgt_id = _upsert_entity_node(db, canonical_name, etype, ring)
            if src_id != tgt_id:
                db.execute(
                    text("""
                        INSERT INTO merge_suggestions (
                            source_node_id, target_node_id, similarity_score, reason, status
                        ) VALUES (
                            :src, :tgt, :score, :reason, 'pending'
                        )
                        ON CONFLICT (source_node_id, target_node_id) DO NOTHING
                    """),
                    {
                        "src": src_id,
                        "tgt": tgt_id,
                        "score": max(0.0, min(1.0, conf)),
                        "reason": (item.get("explanation") or "Medium-confidence disambiguation match")[:500],
                    },
                )
            resolved_node_ids.append((src_id, etype))
        else:
            nid = _upsert_entity_node(db, raw_name or canonical_name, etype, ring)
            resolved_node_ids.append((nid, etype))

    # Build co-occurrence links among unique nodes inside this article
    unique_nodes = list({nid: etype for nid, etype in resolved_node_ids}.items())[:6]
    for i in range(len(unique_nodes)):
        for j in range(i + 1, len(unique_nodes)):
            src_id, src_type = unique_nodes[i]
            tgt_id, tgt_type = unique_nodes[j]
            if src_type == "LOCATION" or tgt_type == "LOCATION":
                ltype = "LOCATED_IN"
            elif src_type == "EQUIPMENT" or tgt_type == "EQUIPMENT":
                ltype = "EQUIPPED_WITH"
            else:
                ltype = "ASSOCIATED_WITH"

            db.execute(
                text("""
                    INSERT INTO entity_links (
                        source_node_id, target_node_id, link_type, confidence, article_id, method
                    ) VALUES (
                        :src, :tgt, :ltype, 0.78, :aid, 'ner_co_occurrence'
                    )
                    ON CONFLICT (source_node_id, target_node_id, link_type, article_id) DO NOTHING
                """),
                {"src": src_id, "tgt": tgt_id, "ltype": ltype, "aid": article_id},
            )

    return [nid for nid, _ in unique_nodes]


def _load_ongoing_events(db) -> List[Dict[str, Any]]:
    rows = db.execute(
        text("""
            SELECT id, title, region, event_type, summary, threat_level
            FROM events
            WHERE status = 'ongoing'
            ORDER BY last_updated_at DESC
            LIMIT 50
        """)
    ).mappings().all()
    return [dict(r) for r in rows]


def _persist_event_threading(
    db,
    threading_agent: ThreadingAgent,
    article_in: ArticleIn,
    translated_text: str,
    event_type: str,
    threat_level: int,
    entity_names: List[str],
) -> Optional[int]:
    """Thread the article into an active event cluster or seed a new ongoing event."""
    regions = map_article_to_regions(article_in.title, translated_text, entity_names)
    primary_region = regions[0] if regions else "Global-Strategic"

    threading_out = threading_agent.run(
        EventThreadingIn(
            article_id=article_in.id or 0,
            title=article_in.title,
            content=translated_text,
            entities=entity_names,
            event_type=event_type,
            region=primary_region,
        )
    )

    event_id = threading_out.matched_event_id
    best_link = threading_out.candidate_links[0] if threading_out.candidate_links else None

    if event_id is None and threading_out.created_new_event:
        title = threading_out.new_event_title or article_in.title[:240]
        row = db.execute(
            text("""
                INSERT INTO events (
                    title, region, event_type, status, threat_level,
                    first_seen_at, last_updated_at, article_count, summary
                ) VALUES (
                    :title, :region, :etype, 'ongoing', :threat,
                    :pub_at, NOW(), 1, :summary
                )
                RETURNING id
            """),
            {
                "title": title[:255],
                "region": primary_region[:100],
                "etype": event_type[:50],
                "threat": float(threat_level),
                "pub_at": article_in.published_at or datetime.now(timezone.utc),
                "summary": (translated_text or article_in.title)[:500],
            },
        ).fetchone()
        event_id = int(row.id)
        threading_agent.add_event(
            {
                "id": event_id,
                "title": title,
                "region": primary_region,
                "event_type": event_type,
                "summary": translated_text[:300],
            }
        )
    elif event_id is not None:
        db.execute(
            text("""
                UPDATE events
                SET article_count = COALESCE(article_count, 0) + 1,
                    threat_level = GREATEST(COALESCE(threat_level, 0), :threat),
                    last_updated_at = NOW()
                WHERE id = :eid
            """),
            {"eid": event_id, "threat": float(threat_level)},
        )

    if event_id is not None and article_in.id is not None:
        link_method = (best_link.link_method if best_link else "cluster_seed")[:64]
        conf = float(best_link.confidence if best_link else 0.85)
        explanation = best_link.explanation if best_link else "Matched via Stage 2 threading pipeline."
        is_seed = bool(threading_out.created_new_event)

        try:
            db.execute(
                text("""
                    INSERT INTO event_articles (
                        event_id, article_id, linked_at, link_method, confidence, is_seed, explanation
                    ) VALUES (
                        :eid, :aid, NOW(), :method, :conf, :seed, :expl
                    )
                    ON CONFLICT (event_id, article_id) DO NOTHING
                """),
                {
                    "eid": event_id,
                    "aid": article_in.id,
                    "method": link_method,
                    "conf": conf,
                    "seed": is_seed,
                    "expl": explanation,
                },
            )
        except Exception:
            # Backward-compatible insert if migration 004 explanation/width not yet applied
            db.execute(
                text("""
                    INSERT INTO event_articles (
                        event_id, article_id, linked_at, link_method, confidence, is_seed
                    ) VALUES (
                        :eid, :aid, NOW(), :method, :conf, :seed
                    )
                    ON CONFLICT (event_id, article_id) DO NOTHING
                """),
                {
                    "eid": event_id,
                    "aid": article_in.id,
                    "method": link_method[:20],
                    "conf": conf,
                    "seed": is_seed,
                },
            )

    return event_id


def _update_source_health(db, source_id: Optional[int]) -> None:
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


def _run_single_article(
    db,
    row: dict,
    threading_agent: ThreadingAgent,
) -> dict:
    """Process one article row through Translation -> Extraction -> Scoring -> Embeddings -> Resolution -> Threading."""
    trans_agent, extract_agent, score_agent, res_agent = _get_agents()

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

    # 1. Translation
    trans_out = trans_agent.run(article_in)
    translated_title = trans_out.get("translated_title") or article_in.title
    translated_text = trans_out.get("translated_text") or article_in.content

    # 2. NER & Classification
    article_for_extract = article_in.model_copy(
        update={"title": translated_title, "content": translated_text}
    )
    extract_out = extract_agent.run(article_for_extract)

    # 3. Article Threat Scoring
    threat_out = score_agent.run(
        ThreatClassifyIn(
            title=translated_title,
            content=translated_text,
            event_type=extract_out.event_type,
            ring=article_in.ring,
        )
    )

    analysis_row = {
        "article_id": article_in.id,
        "translated_text": translated_text,
        "event_type": extract_out.event_type,
        "sentiment": extract_out.sentiment,
        "threat_level": threat_out.threat_level,
        "method": "stage2_nlp_pipeline_v2",
        "model_version": f"trans:{trans_agent.version}|extr:{extract_agent.version}|score:{score_agent.version}",
        "source_ids": [article_in.id] if article_in.id else [],
        "confidence": float(threat_out.provenance.confidence),
        "created_at": datetime.now(timezone.utc),
    }
    _store_analysis(db, analysis_row)

    # 4. 768-dim Semantic Embedding
    _store_embedding(db, row["id"], f"{translated_title}. {translated_text}")

    # 5. Entity Resolution & Graph Link Extraction
    _persist_entities_and_links(
        db=db,
        article_id=row["id"],
        ring=article_in.ring,
        entities=extract_out.entities,
        resolution_agent=res_agent,
        context_text=f"{translated_title}. {translated_text}",
    )

    # 6. Event Threading
    entity_names = [e.entity_value for e in extract_out.entities]
    event_id = _persist_event_threading(
        db=db,
        threading_agent=threading_agent,
        article_in=article_in,
        translated_text=translated_text,
        event_type=extract_out.event_type,
        threat_level=threat_out.threat_level,
        entity_names=entity_names,
    )

    _update_source_health(db, row.get("source_id"))

    return {
        "article_id": row["id"],
        "translated_text": translated_text,
        "event_type": extract_out.event_type,
        "sentiment": extract_out.sentiment,
        "threat_level": threat_out.threat_level,
        "entities": [e.model_dump() for e in extract_out.entities],
        "confidence": float(threat_out.provenance.confidence),
        "event_id": event_id,
    }


def process_single_article(article_id: int) -> dict:
    """Process a single article by ID through the complete Stage 2 pipeline."""
    with get_db() as db:
        row = _fetch_article_by_id(db, article_id)
        if not row:
            raise ValueError(f"Article {article_id} not found")
        ongoing_events = _load_ongoing_events(db)
        threading_agent = ThreadingAgent(known_events=ongoing_events)
        res = _run_single_article(db, row, threading_agent)
        db.execute(
            text("UPDATE articles SET is_processed = TRUE WHERE id = :aid"),
            {"aid": article_id},
        )
        return res


def process_new_articles(run_batch_intelligence: bool = True) -> int:
    """
    Main pipeline entry point — processes all unprocessed articles through Stage 2 agents
    and optionally triggers regional threat scoring + anomaly/watchlist detection.
    Returns count of processed articles.
    """
    processed_ids: List[int] = []
    with get_db() as db:
        rows = _fetch_unprocessed(db)
        if not rows:
            logger.info("Pipeline: no unprocessed articles.")
        else:
            logger.info(f"Pipeline: processing {len(rows)} articles with Stage 2 agents.")
            ongoing_events = _load_ongoing_events(db)
            threading_agent = ThreadingAgent(known_events=ongoing_events)

            for row in rows:
                try:
                    _run_single_article(db, row, threading_agent)
                    processed_ids.append(row["id"])
                except Exception as exc:
                    logger.error("Failed processing article %s: %s", row.get("id"), exc)

            if processed_ids:
                db.execute(
                    text("UPDATE articles SET is_processed = TRUE WHERE id = ANY(:ids)"),
                    {"ids": processed_ids},
                )
            logger.info(f"Pipeline: completed NLP & ontology processing for {len(processed_ids)} articles.")

    # Post-batch regional threat scoring and anomaly / watchlist alerting
    if run_batch_intelligence and processed_ids:
        try:
            from report.scorer import calculate_threat_scores
            from report.anomaly import detect_anomalies

            calculate_threat_scores(window_hours=24)
            detect_anomalies(window_hours=24)
        except Exception as exc:
            logger.warning("Post-batch regional scoring / anomaly step skipped: %s", exc)

    return len(processed_ids)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    process_new_articles()
