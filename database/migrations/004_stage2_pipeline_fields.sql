-- ============================================================================
-- Migration 004: Stage 2 Pipeline Provenance, Threading & Alert Enhancements
-- Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
-- ============================================================================

-- 1. Widen event_articles.link_method for descriptive Stage 2 methods & add explanation
ALTER TABLE event_articles ALTER COLUMN link_method TYPE VARCHAR(64);
ALTER TABLE event_articles ADD COLUMN IF NOT EXISTS explanation TEXT;

-- 2. Extend alerts table with watchlist linkage and provenance article IDs
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE SET NULL;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_article_ids INTEGER[];

-- 3. Ensure unique constraint on article_embeddings(article_id) for safe upserts
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_article_embeddings_article_id'
    ) THEN
        -- Deduplicate any legacy duplicate rows before adding unique constraint
        DELETE FROM article_embeddings a
        USING article_embeddings b
        WHERE a.id < b.id AND a.article_id = b.article_id;

        ALTER TABLE article_embeddings
        ADD CONSTRAINT uq_article_embeddings_article_id UNIQUE (article_id);
    END IF;
END $$;

-- 4. Ensure unique constraint on sources(name) so seed.py upserts work cleanly
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_sources_name'
    ) THEN
        ALTER TABLE sources ADD CONSTRAINT uq_sources_name UNIQUE (name);
    END IF;
END $$;

-- 5. Ensure sitreps table stores executive summary & citations metadata cleanly
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS executive_summary TEXT;
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS citations JSONB DEFAULT '[]';
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS grounding_rate FLOAT DEFAULT 1.0;

