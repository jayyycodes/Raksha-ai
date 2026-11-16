-- =============================================================================
-- Migration 007: Stage 3 (Solid Build) — Cases & Investigations Workspace
-- Aligned with docs/raksha-ai-proposal.md Section 6 (Cap 14) & Section 11 (M9b)
-- =============================================================================

-- 1. Cases Table
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'in_review', 'closed', 'archived')),
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    classification VARCHAR(50) NOT NULL DEFAULT 'restricted' CHECK (classification IN ('unclassified', 'restricted', 'confidential', 'secret')),
    lead_analyst_id INT REFERENCES users(id) ON DELETE SET NULL,
    workspace_id INT REFERENCES workspaces(id) ON DELETE CASCADE,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON cases(priority);
CREATE INDEX IF NOT EXISTS idx_cases_lead_analyst ON cases(lead_analyst_id);
CREATE INDEX IF NOT EXISTS idx_cases_workspace ON cases(workspace_id);

-- 2. Case Evidence Items (Articles, Entities, Events, Incidents)
CREATE TABLE IF NOT EXISTS case_items (
    id SERIAL PRIMARY KEY,
    case_id INT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('article', 'entity', 'event', 'incident')),
    item_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    analyst_notes TEXT,
    added_by INT REFERENCES users(id) ON DELETE SET NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_items_case_id ON case_items(case_id);
CREATE INDEX IF NOT EXISTS idx_case_items_type ON case_items(item_type, item_id);

-- 3. Case Notes & Working Hypotheses
CREATE TABLE IF NOT EXISTS case_notes (
    id SERIAL PRIMARY KEY,
    case_id INT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    analyst_id INT REFERENCES users(id) ON DELETE SET NULL,
    note_text TEXT NOT NULL,
    hypothesis VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_notes_case_id ON case_notes(case_id);
