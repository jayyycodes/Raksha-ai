<div align="center">

# RAKSHA AI

### A Palantir-Inspired Open Source Intelligence Platform for India's Defence Context

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Stage](https://img.shields.io/badge/Stage-1%20MVP-yellow?style=flat)]()

*Collects public news in several languages · Builds a connected graph of events, people and organisations · Keeps an attributed profile for every named entity · Writes a daily Situation Report where every claim cites its source*

</div>

---

## Contents

1. [What is Raksha AI](#what-is-raksha-ai)
2. [The problem](#the-problem)
3. [Palantir-inspired, not Palantir](#palantir-inspired-not-palantir)
4. [System architecture](#system-architecture)
5. [Team and roles](#team-and-roles)
6. [How we work together](#how-we-work-together)
7. [Stage-wise plan](#stage-wise-plan)
   - [Stage 1: MVP](#stage-1-mvp-months-1-2)
   - [Stage 2: Mid](#stage-2-mid-months-3-4)
   - [Stage 3: Solid](#stage-3-solid-months-5-6)
8. [Responsible use and safeguards](#responsible-use-and-safeguards)
9. [Tech stack](#tech-stack)
10. [Database and ontology](#database-and-ontology)
11. [Project structure](#project-structure)
12. [Getting started](#getting-started)
13. [Running tests](#running-tests)
14. [Git workflow](#git-workflow)

---

## What is Raksha AI

Raksha AI is an **Open Source Intelligence (OSINT) analyst platform** for India's defence and security landscape. It runs on **publicly available data**, plus any data an analyst chooses to upload to their own private workspace.

The system:

- **Collects** news from Indian, adversary, regional and global public sources, in multiple languages
- **Understands** it: translation, named entities, event type, sentiment
- **Connects** it: an ontology (graph) of events, organisations, locations, equipment and people
- **Threads events**: links today's article to related articles from months ago, with an explanation for every link
- **Builds profiles**: one attributed page per person, organisation, group or place, collecting everything reported about them
- **Scores threats** by region (1 to 10, with trend)
- **Writes** a daily Situation Report (SitRep) in which every statement cites its source articles
- **Lets analysts bring their own data** (CSV, text, PDF) into a private workspace

Today the scraper covers 15 sources. The design scales to 96+ sources by the final stage.

---

## The problem

A security analyst tracking India's threat landscape today:

- Browses 50+ news sites in several languages every day
- Reads Pakistani and Chinese media to see how adversaries describe events
- Cross-references today's incident with articles from months ago, from memory
- Writes a situation report by hand, which takes hours
- Has no single place that shows everything reported about one person or group

**Raksha AI automates this pipeline and keeps every result explainable.**

---

## Palantir-inspired, not Palantir

Our aim is a Palantir-like platform for India, built at the open-source layer. We adopt its design principles:

| Principle | In Raksha AI |
|---|---|
| Integrate many sources | Scraper, connector framework, analyst uploads |
| Model the world as an ontology | Entity and link tables; events, organisations, locations, people |
| Explore it | Graph, map, timeline, search, profile pages |
| Explain everything | Provenance on every derived fact; citations on every report sentence |
| Human in the loop | Analysts approve reports and review merges |
| Control and audit | Role-based access, audit log, private workspaces |
| Deploy anywhere | Docker Compose, cloud or on-premise |

**What it is not:** it has no classified data, no security accreditation, and pilot scale for one organisation. Say **"Palantir-inspired"**, never "same as Palantir".

---

## System architecture

```
┌────────────────────────────────────────────────────────────┐
│ FLOOR 4 — ANALYST WORKSPACE (Next.js)                      │
│ Feed · Map · Graph · Timeline · SitRep · Search · Profiles │
│ Watchlists · Alerts · Cases · Notes · Data Upload          │
└────────────────────────────┬───────────────────────────────┘
                             │ REST API (FastAPI, OpenAPI docs)
┌────────────────────────────▼───────────────────────────────┐
│ FLOOR 3 — INTELLIGENCE AGENTS (Jaish)                      │
│ Threat Scoring · Anomaly · Grounded SitRep · Profile       │
│ Summaries · Corroboration                                  │
└────────────────────────────┬───────────────────────────────┘
                             │ DB reads and writes
┌────────────────────────────▼───────────────────────────────┐
│ FLOOR 2 — LANGUAGE AND KNOWLEDGE AGENTS (Ary)              │
│ Translation · Extraction · Entity Resolution · Threading   │
└────────────────────────────┬───────────────────────────────┘
                             │ raw articles
┌────────────────────────────▼───────────────────────────────┐
│ FLOOR 1 — DATA COLLECTION (Jay)                            │
│ Scraper · Connectors · Scheduler · PostgreSQL + pgvector   │
│ Source Health · User Upload (CSV, TXT, PDF) · Safe Parsing │
└────────────────────────────────────────────────────────────┘

CROSS-CUTTING: Provenance · Attribution · Source Health · RBAC · Audit
```

**Data flow**

```
Every 4h    Scraper → dedup → PostgreSQL → source-health record
Every 4h    Pipeline runner → Translation → Extraction → embeddings
Per entity  Entity Resolution → strong match links · medium goes to review queue · weak stays separate
Per article Event Threading → similar past articles → explainable links
Daily 6 AM  Scoring + Anomaly → grounded SitRep (analyst approves)
On upload   Validate → safe parse → same pipeline → private workspace
```

### Four-ring source model

| Ring | Coverage | Why it matters |
|------|----------|----------------|
| 1: India | The Hindu, ANI, PIB, DRDO, Army HQ | Ground truth from the Indian side |
| 2: Adversaries | Dawn, Geo, ISPR, Global Times, Xinhua, PLA Daily | Shows how adversary media frames events; may signal narrative shifts early |
| 3: Regional | Tolo News, Kathmandu Post, Daily Star | Neighbourhood signals |
| 4: Global | Reuters, BBC, Jane's, RAND, IDSA, CSIS | Neutral corroboration and analysis |

---

## Team and roles

| Member | Role | Owns |
|--------|------|------|
| **Jay** | Lead and platform | Architecture and API contracts · database and ontology schema · scraper, connectors, scheduler, upload parsers · FastAPI and all middleware (auth, roles, audit, caching) · pipeline orchestration · full Next.js frontend · safeguards and correction workflow · DevOps, CI/CD, deployment · documents and pitch |
| **Ary** | AI/ML: language and knowledge agents | Translation agent · Extraction agent (entities, event type, sentiment, embeddings) · Entity Resolution agent · Event Threading agent · evaluation of these agents |
| **Jaish** | AI/ML: intelligence and generation agents | Threat Scoring and Anomaly agent · Report agent (grounded SitRep) · Profile Summary agent · Corroboration agent · Q&A agent (stretch) · evaluation harness and report grounding checks |

**Rules**

- Jay has the final call on architecture and API contracts.
- Each person owns their modules end to end: design, build, test, document.
- Ary and Jaish each write a short model card for every agent they ship.
- If Jay falls behind, upload parsers and exports move to Jaish, and source-health checks move to Ary.

---

## How we work together

### Agents are modules with a fixed contract

Every agent lives in `agents/<name>/` and exposes one function with typed input and output. Jay defines the schemas in `common/schemas/` in **Week 2**, and the pipeline runner calls the agents. Jay builds the frontend and API against **stub agents** that return sample data, so nobody waits for anyone.

```python
# agents/base.py (example shape; exact schemas live in common/schemas/)
class Agent(Protocol):
    name: str
    version: str
    def run(self, batch: list[ArticleIn]) -> list[AnalysisOut]: ...
```

Every output carries **provenance**: `source_ids`, `method`, `model_version`, `confidence`, `claim_status`.

### Shared tasks in every stage

| Task | Who |
|---|---|
| Hand-label the evaluation set (event types, entity pairs, report claims) | All three |
| Weekly 30-minute sync: demo, blockers, scope check | All three |
| PR review: every PR is reviewed by Jay; agent PRs also include metrics | Jay (reviewer) |
| Update this README's checkboxes at the end of each stage | Jay |

### Definition of done for any task

1. Code merged into `dev` through a reviewed PR
2. Tests pass (`pytest`)
3. For agents: metrics reported on the labelled evaluation set
4. Short note or model card in `docs/`
5. Demonstrable in the running system

---

## Stage-wise plan

Three stages over about six months. Adjust to the college calendar. Tick the boxes as work lands in `main`.

| Stage | Goal | Months |
|---|---|---|
| **1: MVP** | Collect, classify, display, deployed | 1 to 2 |
| **2: Mid** | Intelligence: graph, profiles, threat scores, grounded reports | 3 to 4 |
| **3: Solid** | Production-ready: security, uploads, corrections, deployment | 5 to 6 |

---

### Stage 1: MVP (Months 1 to 2)

**Goal:** a working system that collects news, classifies it, and shows it on a deployed dashboard.

#### Jay

- [ ] Freeze API contracts and Pydantic schemas in `common/schemas/` (**by end of Week 2**)
- [ ] Database: 10 core tables, pgvector, provenance fields, `source_health` table
- [ ] Scraper for 15 RSS sources and NewsAPI; scheduler every 4 hours; URL-hash deduplication; language detection
- [ ] Source health records and a per-source terms and robots checklist before enabling any source
- [ ] Copyright-safe storage: headline, summary and link only
- [ ] Pipeline runner that calls agents on new articles (stub agents first)
- [ ] FastAPI: `/api/articles`, `/api/articles/{id}`, `/api/sources`, `/api/stats`, `/api/sources/health`
- [ ] Next.js MVP screens: **Article Feed** (filter by ring, event type, date) and **Source Status**
- [ ] Docker Compose, CI (lint and pytest), deployment on Railway or Render
- [ ] Scraper tests (4 pytest tests) plus health tests

#### Ary

- [ ] Translation agent v1: Urdu and Chinese to English (Helsinki-NLP models)
- [ ] Extraction agent v1: event-type classification and sentiment (start with a keyword or zero-shot baseline, then a transformer)
- [ ] Choose the embedding model and tell Jay the vector size so the database column matches
- [ ] Label the event-type half of the evaluation set
- [ ] Measure classification accuracy, precision, recall and F1, and report against the 70% target

#### Jaish

- [ ] Evaluation harness: scripts that score any agent against the labelled set (`evaluation/`)
- [ ] Labelling sheet template and the entity-pair half of the evaluation set
- [ ] Stub agents and contract tests for every planned agent, so Jay can integrate early
- [ ] Threat-level classifier v0: low, medium or high per article from event type and keywords
- [ ] Model cards for the agents shipped this stage (with Ary)

#### MVP exit criteria

- [ ] Scraper runs on all 15 sources without crashing; failing sources are logged and skipped
- [ ] Zero duplicate articles across repeated runs
- [ ] Event classification reaches the 70% accuracy target on the labelled set (target, to be validated)
- [ ] Source Status screen shows real health data
- [ ] Every analysed article traces to its source and model version
- [ ] Dashboard is deployed (not just localhost) and loads real data
- [ ] All tests pass

---

### Stage 2: Mid (Months 3 to 4)

**Goal:** the system becomes intelligent. Events are threaded, entities are linked into a graph, profiles exist, threats are scored, and reports are grounded in sources.

#### Jay

- [ ] Grow to 40 sources; add the GDELT connector and proxy support for blocked sources
- [ ] Entity graph API and **interactive graph view** (Cytoscape.js)
- [ ] Leaflet incident map, 30-day threat graph (Recharts), event timeline
- [ ] **Profile pages**: header, summary, timeline, map, associates, sources, notes
- [ ] **Merge and split review queue** UI; analysts accept, reject, merge, split and undo
- [ ] Unified search (full text plus semantic) and watchlists with alerts
- [ ] Lineage panel: "why is this here?" showing sources and method
- [ ] SitRep viewer with PDF export; 6 AM scheduled job
- [ ] Attribution rules in the UI: every statement shows source and claim status; no unattributed labels
- [ ] New endpoints: `/api/graph`, `/api/entities/{id}`, `/api/search`, `/api/watchlists`, `/api/profiles`, `/api/profiles/{id}/timeline`, `/api/merge-suggestions`, `/api/alerts`

#### Ary

- [ ] NER (spaCy): locations, organisations, equipment, persons; write `entity_nodes` and `entity_links`
- [ ] **Entity Resolution agent**: alias table, fuzzy and transliteration-aware matching, context and embedding scoring
  - Strong evidence links automatically
  - Medium evidence goes to the review queue
  - Weak evidence (name only) is never merged
- [ ] Candidate-to-profile rule: an entity becomes a profile after at least 3 articles from at least 2 sources, or when an analyst promotes it
- [ ] Embeddings into pgvector and semantic similarity search
- [ ] **Event Threading agent**: entities plus cosine similarity plus event type and region, within a 6-month window; store shared entities, score and method for every link
- [ ] Evaluate threading (target above 75%) and automatic merges (target at least 90% precision) on the labelled sets

#### Jaish

- [ ] **Threat Scoring agent**: regional 1 to 10 score with rising, stable or falling trend
- [ ] **Anomaly agent**: compare recent activity with a longer baseline, per region and keyword
- [ ] **Report agent**: grounded daily SitRep with Groq Llama 3; a citation for every sentence; model name kept in config; unsupported sentences flagged
- [ ] **Profile Summary agent**: attributed statements with `claim_status` (reported, official designation, analyst verified); source-cited summary
- [ ] **Sensitive-attribute filter**: never infer or store religion, caste, ethnicity, health or similar for a person
- [ ] **Corroboration agent**: `CORROBORATED_BY` and `CONTRADICTS` links between sources
- [ ] Measure report grounding rate (share of sentences supported by cited sources)

#### Mid exit criteria

- [ ] Event threading above 75% accuracy on reviewed pairs, each link with a stored explanation
- [ ] Automatic merges at high precision (target at least 90%); weak matches never merged
- [ ] Profiles show aliases, timeline, map and associates, and every statement shows its source and status
- [ ] Entity graph shows linked events, organisations and locations with evidence
- [ ] Threat scores update after each scrape cycle
- [ ] SitRep generated every morning with citations
- [ ] Search and watchlists work; alerts fire
- [ ] 40+ sources running

---

### Stage 3: Solid (Months 5 to 6)

**Goal:** production-grade, safe to use, deployed, and ready to demo to outsiders.

#### Jay

- [ ] JWT authentication with admin, analyst and viewer roles; workspace isolation
- [ ] Audit log of key actions
- [ ] **Bring Your Own Data**: CSV, TXT and PDF upload; type checked by content; size and page limits; sandboxed parsing with timeouts; optional antivirus scan; CSV column-mapping UI; files stored outside the web root; marked as user-uploaded and kept private until an analyst promotes them
- [ ] Case folders, notes and saved searches
- [ ] **Correction and takedown workflow** for wrong or harmful profile content
- [ ] Retention limits and scheduled database backups
- [ ] Redis caching, async scraper and engine, Celery for background jobs where needed
- [ ] Prometheus, Grafana and Sentry
- [ ] CI/CD auto-deploy on merge to `main`; VPS, Nginx and SSL; Swagger docs
- [ ] PDF, CSV and JSON exports
- [ ] One-command on-premise Docker Compose
- [ ] iDEX pitch deck and demo video coordination
- [ ] Stretch, only if ahead: Excel and Word upload; Telegram, X or satellite connectors

#### Ary

- [ ] Hindi and Marathi support (IndicBERT)
- [ ] Make agents work well on uploaded documents: long-document chunking, PDF text quality
- [ ] Human-review feedback loop: use analyst accept and reject decisions to tune matching thresholds
- [ ] Model evaluation tracking and final model cards
- [ ] Agent tests to support the 80% coverage goal
- [ ] Stretch: image and video forgery signals (deepfake detection v1)

#### Jaish

- [ ] Disinformation scoring v1 from cross-source contradictions
- [ ] Analyst approval flow for SitReps (draft, approved) wired to the Report agent
- [ ] Fallback LLM provider; optional local model (Ollama) for offline use
- [ ] Final validation of threat scores and report grounding
- [ ] Agent tests to support the 80% coverage goal
- [ ] Stretch: "Ask Raksha" question answering over the data, with citations

#### Solid exit criteria

- [ ] 24/7 deployment with monitoring and alerts
- [ ] Roles enforced; audit log records key analyst actions
- [ ] Uploads (CSV, TXT, PDF) processed privately; unsafe or oversized files rejected
- [ ] A reported profile error can be corrected or removed, with a log entry
- [ ] SitReps require analyst approval before final
- [ ] Urdu, Chinese and Hindi processed correctly
- [ ] API responses under 500 ms with caching
- [ ] Test coverage above 80%
- [ ] CI/CD deploys on merge to `main`
- [ ] One external demo completed

#### What gets cut first if we fall behind

1. Telegram, X, satellite and deepfake work
2. Excel and Word upload; "Ask Raksha"; offline local model
3. Case folders beyond the basics
4. Source expansion beyond 40
5. Celery, Grafana and extra infrastructure polish

**Never cut:** provenance, attribution rules, the review queue, the correction workflow and the evaluation set. These make the profile feature safe.

---

## Responsible use and safeguards

Building profiles of people and accepting uploads carry real risks. We handle them in the design.

| Risk | What we do |
|---|---|
| Wrong person linked | Three-level matching; precision over recall; analyst review queue; merges are logged and reversible |
| Unfair labels on a person | The system never assigns labels such as "terrorist" or "criminal". Statements are attributed to a source with a claim status |
| Too many junk profiles | Candidates become profiles only after repeated mentions from several sources, or analyst promotion |
| Privacy and law (for example India's DPDP Act 2023, defamation) | Public reporting only; no scraping of private individuals; no facial recognition; retention limits; correction workflow; ask our guide or college for legal guidance |
| Sensitive attributes | Never inferred or stored |
| Hallucinated reports | Every sentence cites a source; unsupported sentences are flagged; analysts approve |
| Unsafe uploads | Type checks by content, size limits, sandboxed parsing, optional virus scan |
| Uploaded data leaking | Private workspace by default; analyst must explicitly share |
| Scraping terms and copyright | Terms checked per source; headline, summary and link only |
| Over-claiming | Accuracy measured on a labelled set; targets stay targets until validated |

The full risk register is in [docs/raksha-ai-proposal.md](docs/raksha-ai-proposal.md), Section 17.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Data collection | Python 3.11, feedparser, httpx, APScheduler |
| NLP and agents | Hugging Face Transformers, spaCy, sentence-transformers, Helsinki-NLP, IndicBERT (Stage 3), rapidfuzz |
| LLM (reports and summaries) | Groq API, Llama 3 (model name in config; fallback provider; optional local Ollama) |
| Database | PostgreSQL 15 with pgvector and full-text search |
| ORM | SQLAlchemy 2.0, psycopg2-binary |
| Backend | FastAPI, Pydantic; Redis and Celery in Stage 3 |
| Frontend | Next.js 14, Leaflet.js, Cytoscape.js, Recharts |
| Upload parsing (Stage 3) | pandas, pypdf, python-magic, optional ClamAV |
| Containers | Docker, Docker Compose |
| Testing | pytest, pytest-cov |

---

## Database and ontology

Ten core tables, extended in Mid and Solid:

```
sources              → every monitored source
articles             → raw articles (url_hash deduplicated)
article_analysis     → event type, sentiment, threat level
entities             → named entities per article
article_embeddings   → vectors for semantic similarity (pgvector)
events               → ongoing situations ("Depsang Standoff 2024-25")
event_articles       → article-to-event links with confidence and method
threat_scores        → regional scores with trend
sitreps              → daily situation reports
alerts               → anomaly alerts
```

Added later: `entity_nodes`, `entity_links`, `entity_aliases`, `profile_facts`, `merge_suggestions`, `source_health`, `watchlists`, `cases`, `case_items`, `users`, `workspaces`, `uploads`, `audit_log`, `correction_requests`.

**Ontology objects:** Event · Organisation · Location · Equipment · Person · Source · Article · Assessment · Profile · Upload

**Link types:** `MENTIONS` · `OCCURRED_IN` · `INVOLVES` · `PART_OF_EVENT` · `ESCALATES` · `FOLLOWS` · `CORROBORATED_BY` · `CONTRADICTS` · `REPORTED_BY`

**Provenance on every derived record:** `source_ids` · `method` · `model_version` · `confidence` · `claim_status` · `source_type` (public or user_upload) · `created_at`

---

## Project structure

```
raksha-ai/
│
├── README.md
├── .env.example               ← Copy to .env and fill values
├── docker-compose.yml         ← One command PostgreSQL + pgvector
├── Dockerfile
├── requirements.txt
│
├── common/                    ← Jay
│   ├── config.py              ← Typed settings from .env
│   ├── logger.py
│   ├── db.py                  ← SQLAlchemy engine and sessions
│   ├── constants.py           ← Rings, event types, keywords
│   └── schemas/               ← Agent input/output contracts (frozen by Week 2)
│
├── scraper/                   ← Jay: collection
│   ├── sources.py             ← Single source of truth for all sources
│   ├── rss_scraper.py
│   ├── news_api.py
│   └── scheduler.py           ← Runs every 4 hours
│
├── pipeline/                  ← Jay: runs agents on new data
│
├── agents/
│   ├── base.py                ← Agent interface
│   ├── translation/           ← Ary
│   ├── extraction/            ← Ary
│   ├── resolution/            ← Ary: entity resolution
│   ├── threading/             ← Ary: event threading
│   ├── scoring/               ← Jaish: threat scoring and anomaly
│   ├── report/                ← Jaish: grounded SitRep
│   ├── profile/               ← Jaish: profile summaries and filters
│   └── corroboration/         ← Jaish
│
├── api/                       ← Jay: FastAPI, auth, middleware
├── frontend/                  ← Jay: Next.js workspace
│
├── evaluation/                ← Labelled sets and the scoring harness (Jaish harness; all label)
│
├── database/
│   ├── schema.sql
│   ├── seed.py
│   └── migrations/
│
├── tests/
│
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── model-cards/           ← One per agent
│   └── raksha-ai-proposal.md  ← Full project map
│
└── logs/                      ← Auto-created (gitignored)
```

> The earlier `engine/` and `report/` placeholder folders are replaced by `agents/`.

---

## Getting started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- A free [NewsAPI key](https://newsapi.org/register)

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
# Wait for "healthy": docker-compose ps

# 4. Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Initialise the database
docker exec -i rakshaai_db psql -U raksha -d rakshaai < database/schema.sql
python -m database.seed

# 6. Run the scraper
python -m scraper.scheduler
```

### Verify

```bash
docker exec -it rakshaai_db psql -U raksha -d rakshaai -c "
SELECT s.name, COUNT(a.id) AS articles
FROM sources s
LEFT JOIN articles a ON s.id = a.source_id
GROUP BY s.name ORDER BY articles DESC;"
```

---

## Running tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=scraper --cov=common --cov=agents
```

Stage 1 expected output:

```
tests/test_scraper.py::test_rss_returns_articles         PASSED
tests/test_scraper.py::test_article_has_required_fields  PASSED
tests/test_scraper.py::test_broken_source_does_not_crash PASSED
tests/test_scraper.py::test_url_hash_is_idempotent       PASSED
```

---

## Git workflow

```
main          → always deployable, protected
dev           → integration branch
feat/jay/*    → Jay's features
feat/ary/*    → Ary's features
feat/jaish/*  → Jaish's features
```

- Never push directly to `main`.
- Open a PR into `dev`; Jay reviews and merges.
- `dev` goes to `main` only at the end of a stage.
- Commit prefixes: `feat:` `fix:` `refactor:` `docs:` `test:`
- Agent PRs must include the metrics from the evaluation harness.

---

<div align="center">

Built for India's defence-tech ecosystem

**Team Raksha AI** — Jay (lead) · Ary · Jaish

Government College of Engineering Kolhapur · B.Tech AI & Data Science · 2026-27

</div>
