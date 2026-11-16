-- 008_stage3_uploads_corrections.sql
-- Stage 3 M9c: Bring Your Own Data & Safe Uploads, plus Correction Requests (DPDP Act compliance)

CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    uploader_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL DEFAULT 'user_upload',
    status VARCHAR(50) NOT NULL DEFAULT 'processed',
    storage_path VARCHAR(500) NOT NULL,
    parse_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_uploads_workspace ON uploads(workspace_id);
CREATE INDEX IF NOT EXISTS idx_uploads_file_hash ON uploads(file_hash);

-- Correction / Takedown Requests table for DPDP Act & provenance dispute tracking
CREATE TABLE IF NOT EXISTS correction_requests (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL, -- 'entity', 'article', 'event', 'threat_score'
    target_id VARCHAR(100) NOT NULL,
    requester_email VARCHAR(255) NOT NULL,
    claim_details TEXT NOT NULL,
    supporting_evidence TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'submitted', -- 'submitted', 'in_review', 'accepted', 'rejected'
    resolution_notes TEXT,
    resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_corrections_target ON correction_requests(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_corrections_status ON correction_requests(status);
