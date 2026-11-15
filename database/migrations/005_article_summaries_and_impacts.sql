-- Migration 005: Article Summaries & Strategic Impact Analysis for India
-- Extends article_analysis with intelligence summaries and bilateral impact fields.

ALTER TABLE article_analysis
    ADD COLUMN IF NOT EXISTS summary TEXT,
    ADD COLUMN IF NOT EXISTS positive_impact_in TEXT,
    ADD COLUMN IF NOT EXISTS negative_impact_in TEXT,
    ADD COLUMN IF NOT EXISTS strategic_implications TEXT;

CREATE INDEX IF NOT EXISTS idx_article_analysis_summary ON article_analysis USING gin(to_tsvector('english', COALESCE(summary, '')));

