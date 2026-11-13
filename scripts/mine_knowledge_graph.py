"""
Batch Knowledge Graph Miner & Link Extraction
Mines entities from all 390 articles, runs resolution, and constructs
a rich, connected Palantir-style Entity Knowledge Graph in PostgreSQL.
"""
from datetime import datetime, timezone
from sqlalchemy import text
from common.db import get_db
from agents.extraction.agent import ExtractionAgent
from agents.resolution.agent import ResolutionAgent
from common.schemas.articles import ArticleIn

def run_graph_miner():
    ext_agent = ExtractionAgent()
    res_agent = ResolutionAgent()

    with get_db() as db:
        articles = db.execute(text("""
            SELECT a.id, a.title, a.content, a.url, a.published_at,
                   COALESCE(s.ring, 1) as ring, s.id as source_id
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            ORDER BY a.id ASC
        """)).fetchall()

        print(f"Mining entities and links from {len(articles)} articles...")
        total_extracted = 0

        for r in articles:
            aid = r.id
            title = r.title or ""
            content = r.content or ""
            ring = r.ring or 1
            source_id = r.source_id

            art_in = ArticleIn(
                id=aid,
                title=title,
                content=content,
                url=r.url or "https://example.com",
                ring=ring,
                source_id=source_id,
            )

            out = ext_agent.run(art_in)
            if not out.entities:
                continue

            total_extracted += len(out.entities)

            # Store raw entities
            db.execute(text("DELETE FROM entities WHERE article_id = :aid"), {"aid": aid})
            article_node_ids = []

            for ent in out.entities:
                db.execute(text("""
                    INSERT INTO entities (article_id, entity_type, entity_value, confidence)
                    VALUES (:aid, :etype, :eval, :conf)
                """), {
                    "aid": aid,
                    "etype": ent.entity_type[:30],
                    "eval": ent.entity_value[:200],
                    "conf": float(ent.confidence),
                })

                # Upsert into entity_nodes
                node_row = db.execute(text("""
                    INSERT INTO entity_nodes (name, entity_type, aliases, primary_ring, mention_count, source_count, is_profile)
                    VALUES (:name, :etype, ARRAY[:name], :ring, 1, 1, FALSE)
                    ON CONFLICT (name, entity_type) DO UPDATE SET
                        mention_count = entity_nodes.mention_count + 1,
                        source_count = GREATEST(entity_nodes.source_count, 1),
                        last_seen_at = NOW(),
                        is_profile = CASE WHEN entity_nodes.mention_count >= 3 THEN TRUE ELSE entity_nodes.is_profile END
                    RETURNING id
                """), {
                    "name": ent.entity_value.strip(),
                    "etype": ent.entity_type.strip(),
                    "ring": ring,
                }).fetchone()

                if node_row:
                    article_node_ids.append((node_row.id, ent.entity_type))

            # Generate pairwise co-occurrence edges between entities in this article
            for i in range(len(article_node_ids)):
                for j in range(i + 1, len(article_node_ids)):
                    src_id, src_type = article_node_ids[i]
                    tgt_id, tgt_type = article_node_ids[j]
                    if src_id == tgt_id:
                        continue

                    # Determine link type from entity types
                    if src_type == "PERSON" and tgt_type == "ORGANISATION":
                        ltype = "ASSOCIATED_WITH"
                    elif src_type == "ORGANISATION" and tgt_type == "LOCATION":
                        ltype = "LOCATED_IN"
                    elif src_type == "ORGANISATION" and tgt_type == "EQUIPMENT":
                        ltype = "EQUIPPED_WITH"
                    elif src_type == "EQUIPMENT" and tgt_type == "LOCATION":
                        ltype = "DEPLOYED_AT"
                    elif src_type == "LOCATION" and tgt_type == "ORGANISATION":
                        ltype = "HOSTS"
                    else:
                        ltype = "INVOLVES"

                    db.execute(text("""
                        INSERT INTO entity_links (source_node_id, target_node_id, link_type, confidence, article_id, method)
                        VALUES (:src, :tgt, :ltype, 0.88, :aid, 'ner_co_occurrence')
                        ON CONFLICT DO NOTHING
                    """), {
                        "src": src_id,
                        "tgt": tgt_id,
                        "ltype": ltype,
                        "aid": aid,
                    })

        db.commit()

        # Check total nodes and links now
        nodes_count = db.execute(text("SELECT count(*) FROM entity_nodes")).scalar()
        links_count = db.execute(text("SELECT count(*) FROM entity_links")).scalar()
        entities_count = db.execute(text("SELECT count(*) FROM entities")).scalar()
        print(f"Mining complete: Extracted {total_extracted} raw mentions.")
        print(f"Total entity_nodes: {nodes_count}")
        print(f"Total entity_links: {links_count}")
        print(f"Total entities: {entities_count}")

if __name__ == "__main__":
    run_graph_miner()
