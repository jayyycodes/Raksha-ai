-- ============================================================================
-- Migration 003: Ontology Knowledge Graph, Entity Links, Review Queue & Watchlists
-- Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
-- ============================================================================

-- 1. Entity Nodes (The core ontology objects: PERSON, ORGANISATION, LOCATION, EQUIPMENT, EVENT)
CREATE TABLE IF NOT EXISTS entity_nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- PERSON, ORGANISATION, LOCATION, EQUIPMENT, EVENT
    aliases TEXT[] DEFAULT '{}',
    primary_ring INTEGER DEFAULT 1 CHECK (primary_ring BETWEEN 1 AND 4),
    mention_count INTEGER DEFAULT 1,
    source_count INTEGER DEFAULT 1,
    is_profile BOOLEAN DEFAULT FALSE, -- True if >=3 mentions from >=2 sources or analyst promoted
    description TEXT,
    metadata JSONB DEFAULT '{}',
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_entity_nodes_name_type UNIQUE (name, entity_type)
);

CREATE INDEX IF NOT EXISTS idx_entity_nodes_type ON entity_nodes(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_nodes_is_profile ON entity_nodes(is_profile);
CREATE INDEX IF NOT EXISTS idx_entity_nodes_name ON entity_nodes(name);

-- 2. Entity Links (Typed, confidence-scored relationships between entities)
CREATE TABLE IF NOT EXISTS entity_links (
    id SERIAL PRIMARY KEY,
    source_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
    target_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
    link_type VARCHAR(50) NOT NULL, -- INVOLVES, LOCATED_IN, ASSOCIATED_WITH, EQUIPPED_WITH, PART_OF_EVENT, CORROBORATED_BY, CONTRADICTS
    confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0) DEFAULT 0.8,
    article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
    method VARCHAR(50) DEFAULT 'ner_co_occurrence', -- ner_co_occurrence, event_threading, manual_link
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_entity_links_nodes_type_article UNIQUE (source_node_id, target_node_id, link_type, article_id)
);

CREATE INDEX IF NOT EXISTS idx_entity_links_source ON entity_links(source_node_id);
CREATE INDEX IF NOT EXISTS idx_entity_links_target ON entity_links(target_node_id);
CREATE INDEX IF NOT EXISTS idx_entity_links_type ON entity_links(link_type);

-- 3. Disambiguation Review Queue (Human-in-the-loop analyst merges and splits)
CREATE TABLE IF NOT EXISTS merge_suggestions (
    id SERIAL PRIMARY KEY,
    source_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
    target_node_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
    similarity_score FLOAT CHECK (similarity_score BETWEEN 0.0 AND 1.0) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_merge_suggestions_pair UNIQUE (source_node_id, target_node_id)
);

CREATE INDEX IF NOT EXISTS idx_merge_suggestions_status ON merge_suggestions(status);

-- 4. Attributed Profile Facts (Every fact attached to a profile cites its source and status)
CREATE TABLE IF NOT EXISTS profile_facts (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES entity_nodes(id) ON DELETE CASCADE,
    fact TEXT NOT NULL,
    claim_status VARCHAR(30) DEFAULT 'reported', -- reported, official_designation, analyst_verified
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    source_name VARCHAR(100),
    confidence FLOAT DEFAULT 0.8 CHECK (confidence BETWEEN 0.0 AND 1.0),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profile_facts_entity ON profile_facts(entity_id);

-- 5. Watchlists & Alerts (Track key entities, regions, and keywords)
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    query_type VARCHAR(30) NOT NULL, -- entity, region, keyword
    query_value VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Spatial Incident Metadata (Extend events table or provide coordinates for incident map)
ALTER TABLE events ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;
ALTER TABLE events ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
ALTER TABLE events ADD COLUMN IF NOT EXISTS location_name VARCHAR(255);
