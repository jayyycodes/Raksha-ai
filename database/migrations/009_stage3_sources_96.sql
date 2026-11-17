-- 009_stage3_sources_96.sql
-- Stage 3: Scale source monitoring to full 96 sources across 4 Security Rings, APIs, and Telegram

ALTER TABLE sources ADD COLUMN IF NOT EXISTS source_type VARCHAR(32) DEFAULT 'rss';
CREATE INDEX IF NOT EXISTS idx_sources_source_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_ring ON sources(ring);
