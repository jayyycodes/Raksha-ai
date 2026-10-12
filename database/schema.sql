-- ============================================================
-- Raksha AI — PostgreSQL Schema
-- All 10 tables for all 5 stages
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- TABLE 1: sources
CREATE TABLE IF NOT EXISTS sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)  NOT NULL,
    url             VARCHAR(255)  NOT NULL,
    rss_url         VARCHAR(255),
    ring            INTEGER       NOT NULL CHECK (ring BETWEEN 1 AND 4),
    country         VARCHAR(50),
    language        VARCHAR(20)   DEFAULT 'en',
    is_active       BOOLEAN       DEFAULT TRUE,
    last_scraped_at TIMESTAMP
);

-- TABLE 2: articles
CREATE TABLE IF NOT EXISTS articles (
    id           SERIAL PRIMARY KEY,
    source_id    INTEGER     REFERENCES sources(id) ON DELETE SET NULL,
    title        TEXT        NOT NULL,
    content      TEXT,
    url          VARCHAR(500) NOT NULL,
    url_hash     VARCHAR(64)  UNIQUE NOT NULL,
    language     VARCHAR(10)  DEFAULT 'en',
    published_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    scraped_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    is_processed BOOLEAN      DEFAULT FALSE
);

-- TABLE 3: article_analysis
CREATE TABLE IF NOT EXISTS article_analysis (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    translated_text TEXT,
    event_type      VARCHAR(50),
    sentiment       VARCHAR(20),
    threat_level    INTEGER CHECK (threat_level BETWEEN 1 AND 10),
    confidence      FLOAT   CHECK (confidence BETWEEN 0.0 AND 1.0),
    analyzed_at     TIMESTAMP DEFAULT NOW()
);

-- TABLE 4: entities
CREATE TABLE IF NOT EXISTS entities (
    id           SERIAL PRIMARY KEY,
    article_id   INTEGER     REFERENCES articles(id) ON DELETE CASCADE,
    entity_type  VARCHAR(30) NOT NULL,
    entity_value VARCHAR(200) NOT NULL,
    confidence   FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0)
);

-- TABLE 5: article_embeddings (requires pgvector)
CREATE TABLE IF NOT EXISTS article_embeddings (
    id         SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    embedding  VECTOR(768),
    model_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- TABLE 6: events
CREATE TABLE IF NOT EXISTS events (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    region          VARCHAR(100),
    event_type      VARCHAR(50),
    status          VARCHAR(20)  DEFAULT 'ongoing',
    threat_level    FLOAT        DEFAULT 0.0,
    first_seen_at   TIMESTAMP    DEFAULT NOW(),
    last_updated_at TIMESTAMP    DEFAULT NOW(),
    article_count   INTEGER      DEFAULT 0,
    summary         TEXT
);

-- TABLE 7: event_articles
CREATE TABLE IF NOT EXISTS event_articles (
    id          SERIAL PRIMARY KEY,
    event_id    INTEGER REFERENCES events(id)   ON DELETE CASCADE,
    article_id  INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    linked_at   TIMESTAMP DEFAULT NOW(),
    link_method VARCHAR(20),
    confidence  FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0),
    is_seed     BOOLEAN   DEFAULT FALSE,
    UNIQUE(event_id, article_id)
);

-- TABLE 8: threat_scores
CREATE TABLE IF NOT EXISTS threat_scores (
    id            SERIAL PRIMARY KEY,
    region        VARCHAR(100) NOT NULL,
    score         FLOAT        NOT NULL CHECK (score BETWEEN 0.0 AND 10.0),
    trend         VARCHAR(20)  DEFAULT 'stable',
    article_count INTEGER      DEFAULT 0,
    calculated_at TIMESTAMP    DEFAULT NOW()
);

-- TABLE 9: sitreps
CREATE TABLE IF NOT EXISTS sitreps (
    id            SERIAL PRIMARY KEY,
    report_date   DATE      UNIQUE NOT NULL,
    content       TEXT,
    top_threats   JSONB,
    article_count INTEGER   DEFAULT 0,
    generated_at  TIMESTAMP DEFAULT NOW()
);

-- TABLE 10: alerts
CREATE TABLE IF NOT EXISTS alerts (
    id           SERIAL PRIMARY KEY,
    alert_type   VARCHAR(50),
    region       VARCHAR(100),
    description  TEXT,
    severity     VARCHAR(20)  DEFAULT 'low',
    is_read      BOOLEAN      DEFAULT FALSE,
    triggered_at TIMESTAMP    DEFAULT NOW()
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_source_id    ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_is_processed ON articles(is_processed);
CREATE INDEX IF NOT EXISTS idx_entities_type_value   ON entities(entity_type, entity_value);
CREATE INDEX IF NOT EXISTS idx_threat_region         ON threat_scores(region, calculated_at);
CREATE INDEX IF NOT EXISTS idx_events_status         ON events(status, last_updated_at);
CREATE INDEX IF NOT EXISTS idx_alerts_severity       ON alerts(severity, triggered_at);

-- SEED: 15 Week-1 Sources
INSERT INTO sources (name, url, rss_url, ring, country, language) VALUES
('The Hindu',      'https://www.thehindu.com',    'https://www.thehindu.com/news/national/feeder/default.rss',1,'India','en'),
('ANI News',       'https://www.aninews.in',      'https://www.aninews.in/rss/india.xml',                     1,'India','en'),
('The Print',      'https://theprint.in',         'https://theprint.in/feed/',                                1,'India','en'),
('PIB India',      'https://pib.gov.in',          'https://pib.gov.in/RssMain.aspx',                          1,'India','en'),
('Dawn Pakistan',  'https://www.dawn.com',        'https://www.dawn.com/feed',                                2,'Pakistan','en'),
('Geo News',       'https://www.geo.tv',          'https://www.geo.tv/rss/1',                                 2,'Pakistan','en'),
('Global Times',   'https://www.globaltimes.cn',  'https://www.globaltimes.cn/rss/outbrain.xml',              2,'China','en'),
('Xinhua',         'https://english.news.cn',     'http://www.xinhuanet.com/english/rss/chinalatestnews.xml', 2,'China','en'),
('SCMP',           'https://www.scmp.com',        'https://www.scmp.com/rss/91/feed',                         2,'China','en'),
('Tolo News',      'https://tolonews.com',        'https://tolonews.com/rss.xml',                             3,'Afghanistan','en'),
('Kathmandu Post', 'https://kathmandupost.com',   'https://kathmandupost.com/rss',                            3,'Nepal','en'),
('Reuters',        'https://www.reuters.com',     'https://feeds.reuters.com/reuters/INtopNews',              4,'Global','en'),
('BBC Asia',       'https://www.bbc.com',         'http://feeds.bbci.co.uk/news/world/asia/rss.xml',          4,'Global','en'),
('Al Jazeera',     'https://www.aljazeera.com',   'https://www.aljazeera.com/xml/rss/all.xml',                4,'Global','en'),
('Defense News',   'https://www.defensenews.com', 'https://www.defensenews.com/arc/outboundfeeds/rss/',       4,'Global','en')
ON CONFLICT DO NOTHING;
