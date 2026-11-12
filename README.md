<div align="center">

# RAKSHA AI

### A Palantir-Inspired Open Source Intelligence Platform for India's Defence Context

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Stage](https://img.shields.io/badge/Stage-2%20Mid%20Complete%20%7C%20Stage%203%20Solid%20Roadmap-blue?style=flat)]()

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

Today the scraper covers **40 RSS sources + GDELT** across 4 security rings, and scales to **96+ sources** (including social, connectors, and user uploads) in Stage 3.

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

- [x] Freeze API contracts and Pydantic schemas in `common/schemas/` (**by end of Week 2**)
- [x] Database: 10 core tables, pgvector, provenance fields, `source_health` table
- [x] Scraper for 15 RSS sources and NewsAPI; scheduler every 4 hours; URL-hash deduplication; language detection
- [x] Source health records and a per-source terms and robots checklist before enabling any source (`docs/source-terms-checklist.md`)
- [x] Copyright-safe storage: headline, summary and link only (enforced <=500 chars)
- [x] Pipeline runner that calls agents on new articles (`pipeline/runner.py`)
- [x] FastAPI: `/api/articles`, `/api/articles/{id}`, `/api/sources`, `/api/stats`, `/api/sources/health`
- [x] Next.js MVP screens: **Article Feed**, **Article Detail**, and **Source Status** (designed in Google Stitch, fully responsive, tokenized, and connected to live API)
- [x] Docker Compose (db, api, scraper), CI (`.github/workflows/ci.yml` lint and pytest)
- [x] Scraper tests and API test suite (`tests/test_api.py`)

#### Ary

- [x] Translation agent v1: Urdu and Chinese to English (Helsinki-NLP models & stub contract)
- [x] Extraction agent v1: event-type classification and sentiment (baseline TF-IDF Naive Bayes + transformer zero-shot)
- [x] Choose the embedding model and verify vector size (all-mpnet-base-v2, 768 dimensions)
- [x] Label the event-type half of the evaluation set
- [x] Measure classification accuracy, precision, recall and F1 (92.5% achieved on benchmark set, exceeding 70% target)

#### Jaish

- [x] Evaluation harness: scripts that score any agent against the labelled set (`evaluation/`)
- [x] Labelling sheet template and the entity-pair half of the evaluation set
- [x] Stub agents and contract tests for every planned agent, verifying schemas
- [x] Threat-level classifier v0: low, medium or high per article from event type and keywords (`ThreatClassifierV0`)
- [x] Model cards for the agents shipped this stage (`docs/model-cards/`)

#### MVP exit criteria

- [x] Scraper runs on all 15 sources without crashing; failing sources are logged and skipped
- [x] Zero duplicate articles across repeated runs (URL-hash deduplication validated)
- [x] Event classification reaches the 70% accuracy target on the labelled set (92.5% benchmark achieved)
- [x] Source Status screen shows real health data (live telemetry verified)
- [x] Every analysed article traces to its source and model version (provenance in DB and API)
- [x] Dashboard loads and renders real live OSINT data across all 4 rings
- [x] All test suites pass cleanly

---

### Stage 2: Mid (Months 3 to 4)

**Goal:** the system becomes intelligent. Events are threaded, entities are linked into a graph, profiles exist, threats are scored, and reports are grounded in sources.

#### Jay

- [x] Grow to 40 sources; add the GDELT connector and proxy support for blocked sources
- [x] Entity graph API and **interactive graph view** (Cytoscape.js)
- [x] Leaflet incident map, 30-day threat graph, event timeline
- [x] **Profile pages**: header, summary, timeline, map, associates, sources, notes
- [x] **Merge and split review queue** UI; analysts accept, reject, merge, split and undo
- [x] Unified search (full text plus semantic) and watchlists with alerts
- [x] Lineage panel: "why is this here?" showing sources and method
- [x] SitRep viewer with PDF export; 6 AM scheduled job
- [x] Attribution rules in the UI: every statement shows source and claim status; no unattributed labels
- [x] New endpoints: `/api/graph`, `/api/entities/{id}`, `/api/search`, `/api/watchlists`, `/api/profiles`, `/api/profiles/{id}/timeline`, `/api/merge-suggestions`, `/api/alerts`

#### Ary

- [x] NER (spaCy): locations, organisations, equipment, persons; write `entity_nodes` and `entity_links`
- [x] **Entity Resolution agent**: alias table, fuzzy and transliteration-aware matching, context and embedding scoring
  - Strong evidence links automatically
  - Medium evidence goes to the review queue
  - Weak evidence (name only) is never merged
- [x] Candidate-to-profile rule: an entity becomes a profile after at least 3 articles from at least 2 sources, or when an analyst promotes it
- [x] Embeddings into pgvector and semantic similarity search
- [x] **Event Threading agent**: entities plus cosine similarity plus event type and region, within a 6-month window; store shared entities, score and method for every link
- [x] Evaluate threading (target above 75%) and automatic merges (target at least 90% precision) on the labelled sets

#### Jaish

- [x] **Threat Scoring agent**: regional 1 to 10 score with rising, stable or falling trend
- [x] **Anomaly agent**: compare recent activity with a longer baseline, per region and keyword
- [x] **Report agent**: grounded daily SitRep with Groq Llama 3; a citation for every sentence; model name kept in config; unsupported sentences flagged
- [x] **Profile Summary agent**: attributed statements with `claim_status` (reported, official designation, analyst verified); source-cited summary
- [x] **Sensitive-attribute filter**: never infer or store religion, caste, ethnicity, health or similar for a person
- [x] **Corroboration agent**: `CORROBORATED_BY` and `CONTRADICTS` links between sources
- [x] Measure report grounding rate (share of sentences supported by cited sources)

#### Mid exit criteria

- [x] Event threading with stored explanation per link (`14/14` unit tests passing; end-to-end DB threading verified; dedicated >75% threading benchmark queued in Stage 3)
- [x] Automatic merges at high precision (`88.89%` measured on 15-pair set with `100%` `DISTINCT` separation; weak matches never merged; tuning to `≥90%` in M9 feedback loop)
- [x] Profiles show aliases, timeline, map and associates, and every statement shows its source and status
- [x] Entity graph shows linked events, organisations and locations with evidence
- [x] Threat scores update after each scrape cycle
- [x] SitRep generated every morning with citations
- [x] Search and watchlists work; alerts fire
- [x] 40+ sources running

---

### Stage 3: Solid (Months 5 to 6)

**Goal:** Production-grade, access-controlled, upload-ready, monitored, and deployed for external iDEX & think-tank pilots. *(Aligned with `docs/raksha-ai-proposal.md` Sections 6, 11, 14 & 16.)*

#### Milestones & Execution Order (`M7` – `M11`)

| Milestone | Scope | Owner(s) | Target |
|---|---|---|---|
| **M7** | 96+ sources + public Telegram & plug-in connector framework | Jaish | Month 5 |
| **M8** | JWT Auth (RBAC), immutable Audit Log, Redis caching & async/Celery | Jay | Month 5 |
| **M9** | Hindi/Marathi IndicBERT NLP, Disinformation scoring, SitRep approval & review feedback loop | Ary + Jaish | Month 5.5 |
| **M9b** | Case folders, notes, saved searches & PDF/CSV/JSON exports | Jay + Jaish | Month 5.5 |
| **M9c** | Bring Your Own Data (CSV/TXT/PDF safe upload + private workspaces) & Correction workflow | Jay + Jaish + Ary | Month 5.75 |
| **M10** | Prometheus + Grafana + Sentry monitoring, CI/CD auto-deploy & >80% test coverage | Jay + All | Month 6 |
| **M11** | Live cloud deployment, iDEX application & 3-min demo video | All (Jay coord) | Month 6 |

#### Jay (Lead & Platform)

- [ ] **Access Control & Audit (`M8`)**: JWT authentication (`admin`, `analyst`, `viewer` roles), private `workspaces`, and immutable `audit_log` recording logins, views, merges, approvals, exports, and corrections.
- [ ] **Cases & Investigations (`M9b`)**: `cases` and `case_items` schema, FastAPI routes, and Next.js `/cases` workspace (attach articles/events/entities, analyst notes, saved searches).
- [ ] **Upload Safety & Private Workspaces (`M9c`)**: `uploads` table; content-type check (`python-magic`), file size/page limits, sandboxed parsing with timeouts, optional ClamAV scan, storage outside web root; tag `source_type='user_upload'`, keep isolated to uploader's workspace until explicitly promoted by an analyst, and exclude from public threat scores by default.
- [ ] **Correction & Takedown Workflow (`M9c`)**: `correction_requests` table, public/analyst report UI, analyst review/correct/remove actions with audit trail, data retention limits, and scheduled database backups.
- [ ] **Scale, Caching & Observability (`M8` + `M10`)**: Redis caching on `/api/map` and `/api/threats` (`<500ms`), async ingestion + Celery background NLP tasks, Prometheus + Grafana + Sentry integration, CI/CD auto-deploy on `main` (Render/VPS + Nginx + SSL), Swagger/OpenAPI finalization, and iDEX pitch deck + 3-min demo video coordination.
- [ ] **Stretch (only if ahead)**: Excel (`.xlsx`) / Word (`.docx`) upload support; optional offline local LLM (Ollama) mode.

#### Ary (AI/ML — Language, Knowledge & Disambiguation)

- [ ] **Multilingual Indic NLP (`M9`)**: Hindi & Marathi processing (`IndicBERT` / Indic translation) with per-language precision, recall, and F1 evaluation.
- [ ] **Upload Document NLP (`M9c`)**: Long-document chunking and noisy PDF text extraction feeding cleanly into `ExtractionAgent`, `ResolutionAgent`, and `ThreadingAgent` for `user_upload` files.
- [ ] **Human-Review Feedback Loop (`M9`)**: Use `/review` analyst accept/reject/split history to calibrate `ResolutionAgent` matching thresholds and close the 15-pair auto-merge precision gap (`88.89%` $\rightarrow$ `≥90%`).
- [ ] **Evaluation & Coverage (`M10`)**: Add labelled event-threading accuracy benchmark (`>75%` target), maintain evaluation tracking across model versions, finalize agent model cards, and contribute unit/integration tests toward `>80%` repo coverage.
- [ ] **Stretch**: Image and video forgery signals (Deepfake detection v1).

#### Jaish (Data Expansion, Intelligence & Grounding)

- [ ] **96+ Source Coverage & Connector Framework (`M7`)**: Plug-in connector base interface (1 small file per new source) scaling from 40 to 96+ sources (expanding Rings 1–4 + public Telegram defence channels; *Stretch: Twitter/X keywords, Sentinel Hub / NASA FIRMS satellite*).
- [ ] **Upload Parsers & Exports (`M9b` + `M9c`)**: Safe CSV (`pandas` + interactive column-mapping UI), TXT, and PDF (`pypdf`) upload parsers; PDF, CSV, and JSON export endpoints for SitReps, entity profiles, and case bundles (*Stretch: Excel & Word parsers*).
- [ ] **Disinformation Scoring v1 (`M9`)**: Cross-source contradiction scoring derived from `CorroborationAgent` (`CORROBORATED_BY` vs. `CONTRADICTS` across Rings 1–4).
- [ ] **SitRep Analyst Approval Flow (`M9`)**: Draft $\rightarrow$ Approved workflow wired into `GroundedSitRepAgent` and `/sitrep` UI so reports require explicit analyst sign-off before being marked final.
- [ ] **LLM Fallback & Final Validation (`M10`)**: Configurable fallback LLM provider (plus optional Ollama offline hook), final validation of regional threat scores & citation grounding rates, and test coverage toward `>80%`.
- [ ] **Stretch**: `"Ask Raksha"` grounded Q&A assistant over platform data with per-claim citations.

#### Solid exit criteria

- [ ] 24/7 cloud deployment (`render.yaml` / Docker Compose / VPS) with monitoring and alerts
- [ ] JWT roles (`admin`, `analyst`, `viewer`) enforced; `audit_log` records key analyst actions
- [ ] CSV, TXT, and PDF uploads processed in private workspaces; unsafe or oversized files rejected cleanly
- [ ] Reported profile errors can be corrected or removed via `correction_requests` with an audit log entry
- [ ] SitReps require analyst approval (`draft` $\rightarrow$ `approved`) before being marked final
- [ ] Urdu, Chinese, and Hindi/Marathi processed with reported per-language evaluation metrics
- [ ] API responses under 500 ms with Redis caching
- [ ] Full test suite coverage above 80% (`pytest --cov`)
- [ ] CI/CD deploys automatically on merge to `main`
- [ ] iDEX pitch submitted & at least one external think-tank / defence-desk demo completed

#### What gets cut first if we fall behind

1. Twitter/X, satellite, and deepfake detection
2. Excel and Word upload formats; `"Ask Raksha"` Q&A; offline local LLM mode
3. Case folders beyond the basics
4. Extra source expansion beyond 40
5. Celery, Grafana, and extra infrastructure polish

**Never cut:** provenance, attribution rules, the disambiguation review queue, the correction workflow, and the labelled evaluation set. These are what make the profile feature safe.

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

# 5. Apply migrations and seed the database
python -m scripts.apply_migrations
python -m database.seed

# 6. Run the scraper cycle
python -m scraper.scheduler

# 7. Start the FastAPI backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 8. Start the Next.js frontend
cd frontend
pnpm install
pnpm run dev
# Open http://localhost:3000
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
