-- Migration: add source_health table and provenance fields to article_analysis
CREATE TABLE IF NOT EXISTS source_health (
    source_id INTEGER PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
    last_fetched TIMESTAMP,
    last_success TIMESTAMP,
    article_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ok' -- ok, stale, failed, empty
);

-- Add provenance columns to article_analysis if not exist
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS source_ids INTEGER[];
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS method VARCHAR(50);
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS model_version VARCHAR(50);
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0);
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS claim_status VARCHAR(30);
ALTER TABLE article_analysis ADD COLUMN IF NOT EXISTS source_type VARCHAR(20);

