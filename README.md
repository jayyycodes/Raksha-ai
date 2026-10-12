<div align="center">

# RAKSHA AI

### AI-Powered Open Source Intelligence Platform for Indian Defence

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Stage%203-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-Stage%204-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Stage](https://img.shields.io/badge/Stage-1%20MVP-yellow?style=flat)]()

*Monitors 96+ public sources across 4 geopolitical rings · Links today's incident to news from 6 months ago · Generates daily AI Situation Reports · Built for India's threat landscape*

</div>

---

## What is Raksha AI

Raksha AI is a production-grade **Open Source Intelligence (OSINT)** platform built specifically for India's defence and national security landscape.

The system continuously monitors **96+ publicly available news sources** — Indian outlets, adversary media (Pakistan, China), regional neighbours, and global defence publications — and uses AI to:

- **Detect** emerging threats, border tensions, and disinformation automatically
- **Thread events** — link today's article to related articles from months ago to surface escalation patterns
- **Score threats** by region on a 1–10 scale with rising/stable/falling trend
- **Generate** a clean daily Situation Report (SitRep) every morning at 6 AM

Everything runs on **publicly available open-source data** — no classified feeds, no legal grey areas.

---

## The Problem

A security analyst tracking India's threat landscape today:

- Manually browses 50+ news sites in multiple languages every day
- Reads Pakistani and Chinese media to catch what adversaries say first
- Cross-references today's incident with months-old articles — from memory
- Writes a situation report by hand — hours of work per analyst per day

**Raksha AI automates the entire pipeline.**

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               FLOOR 4 — DASHBOARD (Next.js)                  │
│       Live Map · Threat Graph · Daily SitRep Viewer          │
└─────────────────────────┬────────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼────────────────────────────────────┐
│              FLOOR 3 — REPORT ENGINE (FastAPI)               │
│     Threat Scoring · Anomaly Detection · LLM SitRep          │
└─────────────────────────┬────────────────────────────────────┘
                          │ DB reads
┌─────────────────────────▼────────────────────────────────────┐
│               FLOOR 2 — NLP ENGINE (Python)                  │
│   Translation · NER · Event Classification · Embeddings      │
└─────────────────────────┬────────────────────────────────────┘
                          │ raw articles
┌─────────────────────────▼────────────────────────────────────┐
│           FLOOR 1 — DATA COLLECTION  ← CURRENT STAGE        │
│       RSS Scraper · NewsAPI · APScheduler · PostgreSQL       │
└──────────────────────────────────────────────────────────────┘
```

---

## 4-Ring Source Model

| Ring | Coverage | Why Critical |
|------|----------|-------------|
| 1 — India | The Hindu, ANI, PIB, DRDO, Army HQ | Ground truth from Indian perspective |
| 2 — Adversaries | Dawn, Geo, ISPR, Global Times, Xinhua, PLA Daily | Most critical — adversaries announce intent in their own media first |
| 3 — Regional | Tolo News, Kathmandu Post, Daily Star | Neighbourhood signals and proxy indicators |
| 4 — Global | Reuters, BBC, Jane's, RAND, IDSA, CSIS | Neutral corroboration + strategic analysis |

> **Why Ring 2 matters most:** When Global Times runs aggressive anti-India editorials, it historically precedes diplomatic or military escalation. This is a leading indicator.

---

## Key Features

### Event Threading
Automatically links today's article to related articles from months ago using:
1. **Named Entity Matching** — same locations, organizations, weapons
2. **Semantic Similarity** — pgvector cosine similarity > 0.75
3. **Pattern Matching** — same event type + same region within 6-month window

Result: Instead of isolated headlines, analysts see complete **escalation timelines**.

### Multilingual Intelligence
Processes feeds in Urdu (Pakistan), Mandarin (China), Hindi, and Marathi.
Auto-translates using Helsinki-NLP models before analysis.

### AI-Generated Daily SitRep
Every morning at 6:00 AM, Llama 3 (via Groq) auto-generates a structured Situation Report covering top threats, anomalies, ongoing event summaries, and the next-24-hour watch list.

### Zero Classified Data
Operates entirely on publicly available open-source data. Legally deployable without security clearance.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Collection | Python 3.11, feedparser, httpx, APScheduler |
| NLP and AI | HuggingFace Transformers, spaCy, IndicBERT, Helsinki-NLP |
| LLM (SitRep) | Groq API — Llama 3 70B |
| Database | PostgreSQL 15 + pgvector extension |
| ORM | SQLAlchemy 2.0, psycopg2-binary |
| Backend API | FastAPI (Stage 3) |
| Frontend | Next.js 14, Leaflet.js, Recharts (Stage 4) |
| Containerization | Docker, Docker Compose |
| Semantic Search | sentence-transformers + pgvector cosine similarity |
| Testing | pytest, pytest-cov |

---

## Database Design

10-table PostgreSQL schema designed for fast ingestion and complex analytical queries:

```
sources            → Master list of all monitored sources
articles           → Raw scraped articles (url_hash deduplicated)
article_analysis   → NLP output: event type, sentiment, threat level
entities           → Named entities per article
article_embeddings → 768-dim vectors for semantic similarity (pgvector)
events             → Ongoing situations ("Depsang Standoff 2024-25")
event_articles     → Article to Event links with confidence scores
threat_scores      → Regional threat scores with trend direction
sitreps            → Daily AI-generated situation reports
alerts             → Anomaly spike alerts
```

---

## Project Structure

```
raksha-ai/
│
├── README.md
├── .env.example              ← Copy to .env and fill values
├── docker-compose.yml        ← One command PostgreSQL + pgvector setup
├── Dockerfile
├── requirements.txt
│
├── scraper/                  ← STAGE 1: Data Collection (Jaish)
│   ├── sources.py            ← Single source of truth: all 15 sources
│   ├── rss_scraper.py        ← RSS parser, dedup, lang detection
│   ├── news_api.py           ← NewsAPI integration
│   └── scheduler.py         ← Entry point, runs every 4 hours
│
├── engine/                   ← STAGE 2: NLP Analysis (Ary)
│   └── __init__.py           ← translator, ner, classifier, pipeline coming
│
├── report/                   ← STAGE 3: Scoring + SitRep (Ary + Jay)
│   └── __init__.py           ← scorer, anomaly, sitrep, threading coming
│
├── api/                      ← STAGE 3: FastAPI Backend (Jay)
│   └── __init__.py           ← routes: map, threats, events, sitrep coming
│
├── frontend/                 ← STAGE 4: Next.js Dashboard (Jay)
│
├── database/
│   ├── schema.sql            ← All 10 tables + indexes + seeded sources
│   ├── seed.py               ← Seeds sources table
│   └── migrations/
│       └── 001_initial.sql
│
├── common/
│   ├── config.py             ← Typed settings from .env
│   ├── logger.py             ← Rotating file + console logger
│   ├── db.py                 ← SQLAlchemy engine + session factory
│   └── constants.py         ← Rings, event types, keywords
│
├── tests/
│   ├── conftest.py           ← Shared fixtures
│   └── test_scraper.py      ← 4 Stage 1 tests
│
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── raksha-ai-proposal.md ← Full project map: MVP to deploy-ready
│
└── logs/                     ← Auto-created on first run (gitignored)
```

---

## Team

| Member | Role | Owns |
|--------|------|------|
| **Jay** | Lead | Architecture, DB, FastAPI, Frontend, DevOps |
| **Ary** | AI/ML | NLP Engine, Event Threading, Embeddings, SitRep |
| **Jaish** | Dev | Scraper pipeline, NewsAPI, Sources, Testing |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker + Docker Compose
- Free [NewsAPI key](https://newsapi.org/register)

### Setup

```bash
# 1. Clone
git clone https://github.com/jayyycodes/raksha-ai.git
cd raksha-ai

# 2. Environment
cp .env.example .env
# Open .env and add your NEWS_API_KEY

# 3. Start PostgreSQL
docker-compose up -d db
# Wait for "healthy" status: docker-compose ps

# 4. Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Initialize database
docker exec -i rakshaai_db psql -U raksha -d rakshaai < database/schema.sql
python -m database.seed

# 6. Run scraper
python -m scraper.scheduler
```

### Verify

```bash
# Check articles are being stored
docker exec -it rakshaai_db psql -U raksha -d rakshaai -c "
SELECT s.name, COUNT(a.id) AS articles
FROM sources s
LEFT JOIN articles a ON s.id = a.source_id
GROUP BY s.name ORDER BY articles DESC;"
```

---

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=scraper --cov=common
```

Expected:
```
tests/test_scraper.py::test_rss_returns_articles         PASSED
tests/test_scraper.py::test_article_has_required_fields  PASSED
tests/test_scraper.py::test_broken_source_does_not_crash PASSED
tests/test_scraper.py::test_url_hash_is_idempotent       PASSED
```

---

## Development Roadmap

| Stage | Status | Description |
|-------|--------|-------------|
| 1 — Data Collection | In Progress | RSS + NewsAPI scraper, PostgreSQL, scheduler |
| 2 — NLP Engine | Planned | Translation, NER, event classification, sentiment |
| 2.5 — Event Threading | Planned | pgvector embeddings, semantic search, event grouping |
| 3 — Report Engine | Planned | Threat scoring, anomaly detection, LLM SitRep |
| 4 — Dashboard | Planned | Next.js, Leaflet.js map, Recharts, SitRep viewer |

Full details: [docs/raksha-ai-proposal.md](docs/raksha-ai-proposal.md)

---

## Git Workflow

```
main       → always deployable, protected
dev        → integration branch
feat/jay/* → Jay's features
feat/ary/* → Ary's features
feat/jaish/* → Jaish's features
```

Never push directly to main. PR to dev → review → merge.

---

<div align="center">

Built for India's defence-tech ecosystem

**Team Raksha AI** — Jay · Ary · Jaish

GCE Kolhapur · B.Tech AI & Data Science · 2026-27

</div>
