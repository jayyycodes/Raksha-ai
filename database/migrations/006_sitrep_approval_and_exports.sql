-- Migration 006: SitRep Analyst Approval Flow & Export Metadata
-- Stage 3 Solid (Milestone M9 & M9b)
-- Owner: Jaish (Data Expansion, Intelligence & Grounding)

ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'draft';
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS approved_by VARCHAR(128);
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;
ALTER TABLE sitreps ADD COLUMN IF NOT EXISTS analyst_notes TEXT;

CREATE INDEX IF NOT EXISTS idx_sitreps_status ON sitreps (status);
