"""
Backfill intelligence summaries, strategic impacts for India, and entity resolution
across all articles currently in the database.
"""
from common.db import get_db
from sqlalchemy import text
from pipeline.runner import _generate_intelligence_assessment

def backfill():
    with get_db() as db:
        rows = db.execute(text("""
            SELECT a.id, a.title, a.content, COALESCE(s.ring, 1) as ring,
                   aa.event_type, aa.sentiment, aa.threat_level
            FROM articles a
            LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_analysis aa ON aa.article_id = a.id
        """)).fetchall()

        print(f"Backfilling intelligence assessment for {len(rows)} articles...")
        updated = 0
        for r in rows:
            aid = r.id
            title = r.title or "Untitled Report"
            content = r.content or ""
            ring = r.ring or 1
            event_type = r.event_type or "general"
            sentiment = r.sentiment or "neutral"
            threat_level = r.threat_level or 3

            assessment = _generate_intelligence_assessment(
                title=title,
                content=content,
                event_type=event_type,
                sentiment=sentiment,
                threat_level=threat_level,
                ring=ring,
            )

            # Update article_analysis
            db.execute(text("""
                INSERT INTO article_analysis (
                    article_id, summary, positive_impact_in, negative_impact_in, strategic_implications,
                    event_type, sentiment, threat_level, method, model_version, confidence,
                    claim_status, source_type, created_at
                ) VALUES (
                    :aid, :summary, :pos, :neg, :strat,
                    :etype, :sent, :threat, 'stage2_backfill_assessment', 'v0.2.0-mid', 0.88,
                    'reported', 'public', NOW()
                )
                ON CONFLICT (article_id) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    positive_impact_in = EXCLUDED.positive_impact_in,
                    negative_impact_in = EXCLUDED.negative_impact_in,
                    strategic_implications = EXCLUDED.strategic_implications
            """), {
                "aid": aid,
                "summary": assessment["summary"],
                "pos": assessment["positive_impact_in"],
                "neg": assessment["negative_impact_in"],
                "strat": assessment["strategic_implications"],
                "etype": event_type,
                "sent": sentiment,
                "threat": threat_level,
            })
            updated += 1

        db.commit()
        print(f"Successfully backfilled {updated} articles with summaries and bilateral impact analysis.")

if __name__ == "__main__":
    backfill()

