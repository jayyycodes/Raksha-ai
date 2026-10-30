# Raksha AI — Full Project Proposal
## A Palantir-Inspired Intelligence Platform for India — Built on Public Data, Open to Your Own

---

## 0. Project Identity

| Field | Detail |
|---|---|
| **Project Name** | Raksha AI |
| **Tagline** | One connected, explainable picture of India's security landscape, built from public information |
| **Domain** | Defence Tech · Open Source Intelligence (OSINT) · Analyst Workbench |
| **Reference model** | Palantir-style platform design (integrate → ontology → link analysis → AI-assisted analyst workflow), applied to open-source data for India |
| **Design stance** | The aim is a Palantir-like platform for India. Other open-source tools (for example World Monitor) were studied only as examples of features, never as the model to copy |
| **Type** | Final-year project → Startup MVP → Production SaaS |
| **Data policy** | Ships with public, open-source data only. No classified or non-public feeds. Analysts may upload their own data, which stays private to their workspace |
| **Target Path** | iDEX grant → Defence think tank pilots → SaaS |

---

## 1. The Problem

India's open-source threat monitoring is manual, fragmented, and slow.

A security analyst today must:
- Browse 50+ news sites every day in multiple languages
- Read Pakistani and Chinese media to catch what adversaries say first
- Cross-reference today's incident with articles from months ago — from memory
- Write a situation report by hand — hours of work per analyst per day

**What gets missed:** Escalation patterns that only become visible when you link 8 articles across 6 months. No human does this consistently.

**What Raksha AI does:** Automates the entire pipeline — collect, translate, analyze, thread events, score threats, deliver a clean morning brief — zero manual effort.

---

## 2. Vision & Positioning

### 2.1 Vision

> **Build for India what platforms like Palantir built for their governments: a single workspace where scattered information becomes a connected, searchable, explainable, continuously updated picture, but at the open-source layer, on public data, and open to extension.**

Raksha AI is an **analyst workbench**, not just a news dashboard. A dashboard shows headlines. A workbench lets an analyst ask *who is involved, what is connected, what changed, why does the system think so, and what should I watch next.*

### 2.2 Why Palantir is the reference

Palantir popularised a platform pattern for government and defence users:

1. **Integrate** data from many separate sources into one place.
2. **Model the world** as an *ontology*: real-world objects (people, organisations, places, events, equipment) with typed links between them.
3. **Explore** that model through link analysis, maps, timelines and search.
4. **Explain** every result with provenance: where it came from and how it was derived.
5. **Apply AI** on top of the model, with a human analyst approving what matters.
6. **Control and audit** who can see and do what.
7. **Deploy anywhere**, including secure environments, and expose APIs for other systems.

Raksha AI adopts these seven design principles. We apply them to open-source intelligence for India.

### 2.3 Positioning statement

> *Raksha AI is a Palantir-inspired open-source intelligence platform for India's defence and security context. It integrates public sources in multiple languages, organises them into a linked entity-and-event model, and gives analysts explainable, AI-assisted situational awareness with full provenance and audit.*

### 2.4 What Raksha AI is, and is not

| Raksha AI **is** | Raksha AI **is not** |
|---|---|
| An OSINT analyst platform built on public data | A system that connects to classified or government networks |
| A builder of **attributed profiles**: every fact shows its source and status | A system that decides on its own that a person is a "criminal" or "terrorist" |
| Open to analyst-supplied data, kept private to the analyst | A scraper of private individuals' personal data |
| A decision-support tool: it suggests, the analyst decides | An autonomous decision-maker or a replacement for analysts |
| Explainable: every claim traces to source articles | A black box that outputs scores without evidence |
| Deployable by a college lab, think tank or newsroom | A certified or accredited secure system |
| Honest about being **Palantir-inspired** | A claim to be equivalent to Palantir |

> **Rule for viva, pitch and iDEX:** say *"Palantir-inspired"*, never *"same as Palantir"*. Claim only what the demo can show.

### 2.5 Two signature features

**Entity Profiles (the "object view").** When the news names a person, organisation, group or place, the system builds a profile for it and keeps adding to it: aliases, roles, a timeline of reported activity, locations reported on a map, associates in a graph, and the source of every statement. A search for a name returns everything known about it, in one place. Profiles are built for people named in public reporting. Each statement is attributed to its source, and the system never assigns labels such as "terrorist" or "criminal" on its own. A label appears only as an attributed statement, for example *"designated by [authority], per [source]"*.

**Bring Your Own Data.** Analysts can upload their own data (CSV, plain text and PDF in the core build; Excel and Word as stretch). The upload passes through the same pipeline (translate, extract entities, classify, link) and appears in the analyst's private workspace marked "user-uploaded". It is not mixed into the shared public layer unless an analyst chooses to promote it.

### 2.6 Examples studied

Open-source projects such as World Monitor and SA-Monitor were studied for ideas (source-health tracking, spike detection, South Asia focus). They are examples of what a monitoring tool can include. They are **not** the model for Raksha AI, whose aim is a Palantir-like analyst platform. No code is copied; ideas are re-implemented and the projects are cited as related work.

---

## 3. Palantir-Inspired Capability Map

Every capability we copy in spirit, what it means, how Raksha AI implements it, when, and who owns it.
**Scope:** *Core* = must ship · *Stretch* = only if ahead of schedule · *Out* = deliberately not built.

| # | Capability | What it means | Raksha AI implementation | Stage | Owner | Scope |
|---|---|---|---|---|---|---|
| 1 | Multi-source data integration | Many feeds in one place | Scraper + connector framework: RSS, NewsAPI, GDELT; later social and satellite | MVP → Solid | Jaish | Core |
| 2 | Bring your own data | Analysts add their own data | Upload CSV, TXT, PDF (Excel, Word stretch); safe parsing; same NLP pipeline; private workspace | Solid | Jaish + Jay | CSV/TXT/PDF: Core · others: Stretch |
| 3 | Ontology (objects and links) | World modelled as linked objects | Entity and link tables; object types Event, Organisation, Location, Equipment, Person, Source | Mid | Ary + Jay | Core |
| 4 | Entity profiles (object views) | One page with everything known about an entity | Profile pages for people, organisations, groups, places: aliases, timeline, map, associates, attributed statements | Mid | Jay + Ary | Core |
| 5 | Entity resolution | Same entity under different spellings is one object; different people stay separate | Confidence-scored matching, review queue, analyst merge and split with undo | Mid | Ary | Core |
| 6 | Link analysis | Explore connections visually | Graph API and interactive graph view with filters and expand-neighbours | Mid | Jay | Core |
| 7 | Geospatial analysis | Map-based picture | Leaflet incident map, border and region layers, locations reported per profile | Mid | Jay | Core |
| 8 | Temporal analysis | How situations evolve | Event timelines, profile timelines, 30-day threat graph, 6-month event threading | Mid | Ary + Jay | Core |
| 9 | Unified search | Search across everything | Postgres full-text plus semantic (pgvector) search over articles, entities, profiles and events | Mid | Jay + Ary | Core |
| 10 | Provenance and lineage | Where did this come from | Every article, entity, link, score, profile fact and SitRep claim stores source IDs, method, model version, claim status and timestamp; lineage panel in the UI | MVP → Mid | Jay | Core |
| 11 | AI grounded in platform data | LLM answers from the data, with evidence | Grounded SitRep and profile summaries with per-claim citations; "Ask Raksha" question answering | Mid → Solid | Ary | Summaries: Core · Q&A: Stretch |
| 12 | Human-in-the-loop | AI suggests, analyst decides | Analyst approves SitReps, accepts or rejects suggested links and merges; feedback saved for evaluation | Mid → Solid | Ary + Jay | Core |
| 13 | Alerts and automation | Watch conditions, notify | Anomaly alerts, watchlists on regions, entities, profiles and keywords, scheduled jobs | Mid | Jay | Core |
| 14 | Collaboration and cases | Shared investigations | Case folders, notes, saved searches, sharing within roles | Solid | Jay | Core (basic) |
| 15 | Access control and audit | Who can see and do what | JWT roles (admin, analyst, viewer), workspace isolation and an audit log of key actions | Solid | Jay | Core |
| 16 | Data quality and health | Trust the data | Source health and freshness tracking, deduplication, labelled evaluation metrics | MVP → Solid | Jaish | Core |
| 17 | Safeguards and corrections | Responsible handling of data about people | Attribution rules, no system-assigned labels, correction and takedown workflow, retention limits | Mid → Solid | Jay | Core |
| 18 | APIs and integration | Other systems can plug in | FastAPI with auto-generated OpenAPI docs; PDF, CSV and JSON exports | MVP → Solid | Jay | Core |
| 19 | Deploy anywhere | Cloud or on-premise | Docker Compose one-command setup; cloud deployment; optional local LLM for offline use | Solid | Jay | Cloud: Core · Offline LLM: Stretch |
| 20 | Application builder | Build custom apps on the data | Fixed workspace only | n/a | n/a | **Out** |
| 21 | Classified and government data | Connect secret systems | Public data only (plus analyst uploads); no connection to government systems | n/a | n/a | **Out** |
| 22 | Security accreditation | Formal certification, air-gapped approval | Follow secure-coding hygiene; no certification | n/a | n/a | **Out** |
| 23 | Very large scale | Huge data volumes and user counts | Single-organisation pilot scale | n/a | n/a | **Out** |
| 24 | Embedded delivery teams | Engineers placed with customers | Documentation and demos instead | n/a | n/a | **Out** |

**Reading the table:** rows 1–19 are what we build. Rows 20–24 are listed on purpose so the team and examiners see exactly where the boundary is.

---

## 4. One-Line Per Stage

| Stage | What it is |
|---|---|
| **MVP** | Automated news collector + basic threat classifier + simple web dashboard, with **provenance** on every record and a **source-health** page |
| **Mid** | Event threading + **entity graph (ontology), link analysis and entity profiles with careful disambiguation** + regional threat scoring + **grounded** AI daily SitRep + search + watchlists |
| **Solid** | Full production system: multilingual, **bring-your-own-data upload, role-based access, audit log, cases, analyst approval, correction workflow**, deployable anywhere, scalable, monitored |

---

## 5. System Architecture

```
┌────────────────────────────────────────────────────────────┐
│ FLOOR 4 — ANALYST WORKSPACE                                │
│ Feed · Map · Graph · Timeline · SitRep · Search · Profiles │
│ Watchlists · Alerts · Cases · Notes · Data Upload          │
└────────────────────────────────────────────────────────────┘
                             │ REST API (FastAPI, OpenAPI docs)
                             ▼
┌────────────────────────────────────────────────────────────┐
│ FLOOR 3 — INTELLIGENCE & REPORT ENGINE                     │
│ Threat Scoring · Anomaly Detection · Alerts                │
│ Grounded LLM SitRep (with citations) · Search · Ask Raksha │
└────────────────────────────────────────────────────────────┘
                             │ DB reads
                             ▼
┌────────────────────────────────────────────────────────────┐
│ FLOOR 2 — NLP & ONTOLOGY ENGINE                            │
│ Translation · NER · Event Classification · Embeddings      │
│ Entity Resolution · Threading · Entity Graph · Profiles    │
└────────────────────────────────────────────────────────────┘
                             │ raw articles
                             ▼
┌────────────────────────────────────────────────────────────┐
│ FLOOR 1 — DATA COLLECTION                                  │
│ 96+ Sources · NewsAPI · GDELT · Connector Framework        │
│ APScheduler · PostgreSQL + pgvector · Source Health        │
│ User Data Upload (CSV · TXT · PDF) · Safe Parsing          │
└────────────────────────────────────────────────────────────┘

CROSS-CUTTING (every floor): Provenance · Attribution · Source Health · RBAC · Audit
```

**Data flow:**
```
Every 4h   → Scraper collects sources → dedup → PostgreSQL → source-health record updated
Every 4h   → NLP engine processes new articles → translate + NER + classify
Per article → Entity resolution → create/update entity nodes and links (ontology)
Per article → Event threading → pgvector cosine search → link to historical events
Per entity → Disambiguation: strong match auto-links · medium goes to review queue · weak stays separate → profile updated
On upload  → Validate + scan → sandboxed parse → same NLP pipeline → private workspace layer (promote to shared only by analyst)
Daily 6AM  → Report engine → threat scores + anomaly alerts + grounded LLM SitRep (with citations)
On demand  → FastAPI → serves workspace (map, graph, timeline, search, SitRep, cases)
Always     → Provenance stored on every derived fact; audit log records analyst actions
```

**Design principles (carried from Section 2):** integrate · model the world · explain · human in the loop · secure by design · deploy anywhere · open APIs.

---

## 6. Team & Ownership

```
JAY (Lead)                 ARY                       JAISH
─────────────────          ─────────────────         ─────────────────
Architecture               NLP Engine                Data Collection
Database + ontology schema Event Threading           Scraper pipeline
FastAPI backend            Embeddings + pgvector     NewsAPI + GDELT + connectors
DevOps + deployment        Entity resolution + graph Scheduler
Workspace UI (graph, map)  Disambiguation scoring    Source management + health
Profile pages + review UI  Grounded LLM SitRep       Upload parsers + validation
RBAC, audit, workspaces    Profile summaries         Official-list seed data
Provenance + lineage       Threat scoring model      Data quality + eval set
Safeguards + corrections   Translation pipeline      Testing + CI
Code reviews               Research + model eval     Exports + data checks
iDEX + pitch docs          Human-review feedback loop
```

**Rule:** Jay has final call on architecture and API contracts.
Each member owns their module end-to-end: design, build, test, document.

---

## 7. Source Coverage (96+)

| Ring | Focus | Count | Examples |
|------|-------|-------|---------|
| 1 — India | Domestic + official | 25 | The Hindu, ANI, PIB, DRDO, Army HQ |
| 2 — Adversaries | Pakistan + China | 18 | Dawn, Geo, ISPR, Global Times, Xinhua, PLA Daily |
| 3 — Regional | Neighbours | 12 | Tolo News, Kathmandu Post, Daily Star |
| 4 — Global | Defence + neutral | 25 | Reuters, Jane's, RAND, IDSA, CSIS |
| APIs | Structured intel | 6 | GDELT, ACLED, Sentinel Hub, FIRMS NASA |
| Social | Real-time | 10 | Twitter/X keywords, Telegram channels |

**MVP:** 15 RSS + NewsAPI
**Mid:** 40 sources + GDELT
**Solid:** All 96+ including social and satellite

---

## 8. Database & Ontology (10 core tables + extensions)

```
sources            → Master list of all monitored sources
articles           → Raw scraped articles (url_hash dedup)
article_analysis   → NLP output: event type, sentiment, threat level
entities           → Named entities per article (locations, orgs, weapons)
article_embeddings → 768-dim vectors for semantic similarity (pgvector)
events             → Ongoing situations ("Depsang Standoff 2024-25")
event_articles     → Article to Event links with confidence + method
threat_scores      → Regional threat scores with trend direction
sitreps            → Daily AI-generated situation reports
alerts             → Anomaly spike alerts
```

### 8.1 Ontology: the objects Raksha AI understands

| Object type | Examples | Key properties |
|---|---|---|
| **Event** | "Depsang Standoff 2024-25" | name, type, region, start and last-seen dates, status, threat level |
| **Organisation** | PLA, ISPR, Indian Army, DRDO | name, aliases, country, category |
| **Location** | Depsang, LAC, Kashmir | name, coordinates, region, country |
| **Equipment / Weapon** | missile types, platforms | name, category, aliases |
| **Person** | officials, commanders (public figures only) | name, role, organisation |
| **Source** | Dawn, Global Times, PIB | ring, country, language, reliability notes |
| **Article (evidence)** | any collected article | title, URL, date, language, summary |
| **Assessment** | threat score, SitRep | region, value, trend, citations |
| **Profile** (view of any object above) | profile page for a person, organisation, group or place | aliases, roles, timeline, locations, associates, attributed statements, status |
| **Upload** | user-provided file | owner, workspace, file type, scan result, parse status |

### 8.2 Link types (relationships between objects)

| Link | Meaning |
|---|---|
| `MENTIONS` | Article mentions an entity |
| `OCCURRED_IN` | Event happened in a location |
| `INVOLVES` | Event involves an organisation, person or equipment |
| `PART_OF_EVENT` | Article belongs to an event (with confidence and method) |
| `ESCALATES` / `FOLLOWS` | Event sequence over time |
| `CORROBORATED_BY` | Independent sources report the same thing |
| `CONTRADICTS` | Sources disagree (disinformation signal) |
| `REPORTED_BY` | Article published by a source |

### 8.3 Extension tables (added from Mid onwards)

```
entity_nodes     → One row per resolved entity (type, canonical name, aliases)
entity_links     → Typed links between nodes with confidence + evidence article IDs
source_health    → Per-source last fetched, last success, article count, staleness limit
watchlists       → Saved regions, entities and keywords an analyst is tracking
cases            → Investigation folders (Solid)
case_items       → Articles, events and notes attached to a case (Solid)
users            → Accounts with role: admin, analyst, viewer (Solid)
audit_log        → Who did what and when (Solid)
entity_aliases   → Alternative names and spellings per entity, with language
profile_facts    → One attributed statement each: text, source article, claim_status, confidence
merge_suggestions→ Candidate pairs of entities with match score, status, decided_by
workspaces       → Private analyst spaces (Solid)
uploads          → User files: owner, workspace, type, scan result, parse status (Solid)
correction_requests → Reports of wrong or harmful profile content and their outcome (Solid)
```

### 8.4 Provenance fields (on every derived record)

```
source_ids      → Which article(s) it came from
method          → rule | model name | human
model_version   → Version of the model or prompt that produced it
confidence      → 0–1 score where applicable
created_at      → Timestamp
reviewed_by     → Analyst who accepted or rejected it (Solid)
claim_status    → reported | official_designation | analyst_verified
source_type     → public | user_upload
```

### 8.5 Entity profile structure

```
Header      → canonical name, type, aliases, status (candidate / profile), last updated
Summary     → short LLM summary where every sentence cites its source article
Timeline    → dated reported activities, each with source and claim_status
Locations   → places the entity was reported in, shown on a map
Associates  → linked people, organisations, events (graph view)
Sources     → every article used, with ring and reliability note
Analyst     → notes, merges and splits (with history), watch switch
```

### 8.6 Disambiguation rules (who counts as the same entity)

| Evidence strength | Example | Action |
|---|---|---|
| **Strong** | Same name or known alias **and** shared context (organisation, location, role) **and** high embedding similarity | Link automatically; record evidence and score |
| **Medium** | Same name, partial context | Put in the **review queue**; an analyst accepts or rejects |
| **Weak** | Same name only | Keep as **separate** entities; never merge |

Principle: **precision over recall.** It is better to miss a link than to attach one person's activity to another. All merges can be split again, and every merge and split is logged.

---

## 9. Stage 1 — MVP

**Timeline:** Month 1–2
**Goal:** Working system that collects, classifies, and displays. Deployed.

### Module Ownership

| Module | Owner | What |
|---|---|---|
| RSS Scraper (15 sources) | Jaish | feedparser + dedup + langdetect |
| NewsAPI integration | Jaish | Defence keywords, free tier |
| APScheduler | Jaish | Runs every 4h, logs summary |
| PostgreSQL schema + Docker | Jay | All 10 tables, pgvector, indexes |
| common/ utilities | Jay | config, logger, db, constants |
| FastAPI backend (basic) | Jay | Articles, sources, stats endpoints |
| Basic NLP pipeline | Ary | Event classification + sentiment |
| Translation (basic) | Ary | Helsinki-NLP Urdu/Chinese to English |
| Simple dashboard | Jay + Ary | Next.js: article feed + source stats |
| Scraper tests | Jaish | 4 pytest tests passing |
| Source health record | Jaish | Last fetched, success/fail, article count per source |
| Provenance fields | Jay | source_ids, method, model_version on analysis records |
| Labelled evaluation set | All | Hand-labelled sample of articles for measuring accuracy |
| Source terms and robots check | Jaish | Checklist per source before it is enabled; rate limits and polite crawling |
| Copyright-safe storage | Jay | Store headline, summary and link; no republishing of full article text |
| Fixed embedding model | Ary | Choose one model early; vector column dimension must match it |

### API Endpoints (MVP)

```
GET  /api/articles        → paginated article list
GET  /api/articles/{id}   → article detail with analysis
GET  /api/sources         → all sources with last scraped time
GET  /api/stats           → article counts, per-source breakdown
```

### Dashboard Screens (MVP)

```
Screen 1: Article Feed
  Filter by ring, event type, date
  Card: title · source · date · event type · sentiment badge

Screen 2: Source Status
  Table: all 15 sources, last scraped, articles today, active/failing
```

### MVP Success Criteria

```
✓ Scraper runs on all 15 sources without errors
✓ Zero duplicate articles across multiple runs
✓ NLP classifies event type correctly on 70%+ of articles
✓ Dashboard loads with real data
✓ Deployed on Railway or Render (not just localhost)
✓ All 4 pytest tests pass
✓ Source Status screen shows real health data per source
✓ Every analysed article traces back to its source and model version
✓ Labelled evaluation set created and used to measure classification
```

---

## 10. Stage 2 — Mid Build

**Timeline:** Month 3–4
**Goal:** System becomes intelligent. Events threaded. Entities linked into a graph. Threats scored. AI writes a grounded brief.

### Module Ownership

| Module | Owner | What |
|---|---|---|
| NER extraction | Ary | spaCy: locations, orgs, weapons, persons |
| Vector embeddings | Ary | sentence-transformers to pgvector |
| Semantic similarity | Ary | Cosine search for related articles |
| Event threading engine | Ary | Links articles to events via 3 methods |
| Threat scoring model | Ary | Weighted regional score + trend calc |
| LLM SitRep generation | Ary | Groq Llama 3 + prompt template |
| Anomaly detection | Jay | Spike detection per source and region |
| Alerts API | Jay | DB + endpoints for alert feed |
| GDELT API integration | Jaish | 100+ language structured event data |
| 25 more RSS sources | Jaish | Ring 2 + Ring 4 expansion |
| Proxy support | Jaish | For geo-restricted Ring 2 sources |
| New FastAPI endpoints | Jay | Map, threats, events, SitRep, alerts |
| Leaflet.js Map | Jay | Incidents plotted on India border map |
| Recharts Threat Graph | Jay | 30-day threat timeline per region |
| Event Timeline view | Jay | Drill-down: event to full article history |
| SitRep viewer | Jay | Daily report card with PDF export |
| Ontology builder | Ary | Entity resolution, entity_nodes and entity_links from NER output |
| Explainable threading | Ary | Each link stores shared entities, similarity score and method |
| Grounded SitRep | Ary | Every claim cites source article IDs; unsupported sentences flagged |
| Graph API + graph view | Jay | Interactive entity graph (Cytoscape.js) with filters |
| Unified search | Jay + Ary | Full-text + semantic search across articles, entities, events |
| Watchlists | Jay | Track regions, entities and keywords; alerts on matches |
| Lineage panel | Jay | "Why is this here?" view showing sources and method |
| Entity resolution + disambiguation | Ary | Alias table, fuzzy and transliteration-aware name matching, context and embedding scoring, three-level rule (strong / medium / weak) |
| Candidate-to-profile rule | Ary | Entity becomes a full profile after mentions in at least 3 articles from at least 2 sources, or when an analyst promotes it |
| Entity profile pages | Jay | Header, grounded summary, timeline, map, associates graph, sources, notes |
| Profile summaries and facts | Ary | Attributed statements with claim_status; every sentence cites a source |
| Merge / split review queue | Jay + Ary | Analyst accepts, rejects, merges, splits and undoes; all actions logged |
| Official-list seed data | Jaish | Public authoritative lists and official press releases used as high-trust sources (availability to be checked) |
| Sensitive-attribute filter | Ary | System never infers or stores religion, caste, ethnicity, health or similar attributes for a person |

### New API Endpoints (Mid)

```
GET  /api/map              → geo-tagged incidents for Leaflet
GET  /api/threats          → threat scores per region + trend
GET  /api/threats/{region} → 30-day history for a region
GET  /api/events           → ongoing events list with article count
GET  /api/events/{id}      → event detail + full article timeline
GET  /api/sitrep/today     → today's AI-generated report
GET  /api/sitrep/{date}    → historical SitRep
GET  /api/alerts           → unread anomaly alerts
GET  /api/graph            → nodes + links for an entity or event neighbourhood
GET  /api/entities/{id}    → entity detail with linked events and articles
GET  /api/search?q=        → unified full-text + semantic search
GET  /api/watchlists       → analyst watchlists and recent matches
GET  /api/sources/health   → per-source freshness and status
GET  /api/profiles         → searchable list of profiles and candidates
GET  /api/profiles/{id}    → full profile: summary, facts, aliases, sources
GET  /api/profiles/{id}/timeline → dated activities with sources and claim_status
GET  /api/merge-suggestions → pairs awaiting analyst review
POST /api/profiles/{id}/merge  → merge two entities (logged, reversible)
POST /api/profiles/{id}/split  → undo or correct a merge (logged)
```

### Mid Success Criteria

```
✓ Event threading links related articles with >75% accuracy
✓ Threat scores update correctly after each scrape cycle
✓ SitRep generated and stored every morning at 6 AM
✓ Map shows real incidents plotted in correct locations
✓ Threat graph shows 30-day history per region
✓ Event timeline shows full history for any ongoing situation
✓ 40+ sources running without failures
✓ Entity graph shows linked events, organisations and locations
✓ Every graph link and SitRep claim shows its evidence
✓ Search returns relevant results across articles, entities and events
✓ Watchlist alerts fire when a tracked item appears
✓ Profiles show aliases, timeline, map and associates for named entities
✓ Every profile statement shows its source and claim status
✓ No profile carries a label that is not attributed to a source
✓ Automatic merges reach high precision on the labelled pair set (target ≥ 90%, to be validated)
✓ Weak matches are never merged; medium matches go to the review queue
```

---

## 11. Stage 3 — Solid (Deploy-Ready)

**Timeline:** Month 5–6
**Goal:** Production-grade. Monitored. Scalable. Ready for iDEX and investors.

### Module Ownership

| Module | Owner | What |
|---|---|---|
| Twitter/X monitoring | Jaish | Defence keyword tracking (**Stretch**: cut first if behind) |
| Telegram channels | Jaish | Public defence/news channels |
| Satellite API | Jaish | Sentinel Hub + NASA FIRMS (**Stretch**) |
| Full 96-source coverage | Jaish | All rings at full capacity |
| Hindi/Marathi NLP | Ary | IndicBERT for regional content |
| Deepfake detection v1 | Ary | Image/video forgery signals (**Stretch**) |
| Disinformation scoring | Ary | Cross-source contradiction detection |
| Model eval tracking | Ary | Accuracy metrics per model |
| Auth system (JWT) | Jay | Roles: admin, analyst, viewer |
| Redis caching | Jay | Cache map + threat endpoints |
| Async architecture | Jay | asyncio scraper + engine |
| Celery task queue | Jay | Background NLP jobs |
| Prometheus + Grafana | Jay | System health monitoring |
| Sentry integration | Jay | Error alerting |
| CI/CD (GitHub Actions) | Jay | Auto-deploy on merge to main |
| Production deployment | Jay | VPS + Nginx + SSL + domain |
| Full test suite | All | >80% coverage |
| API docs (Swagger) | Jay | Auto-generated |
| iDEX pitch deck | Jay | With live demo link |
| 3-min demo video | All | Product walkthrough |
| Audit log | Jay | Records analyst actions: views, approvals, exports |
| Cases and notes | Jay | Case folders, attached evidence, notes, saved searches |
| Human review loop | Ary + Jay | Analyst approves SitReps and accepts/rejects suggested links; feedback stored |
| Connector framework | Jaish | Plug-in interface so a new source needs one small file |
| Exports | Jaish | PDF, CSV and JSON export of reports and entity lists |
| Offline mode (**Stretch**) | Jay | Optional local LLM (Ollama) so the system runs without cloud APIs |
| On-premise packaging | Jay | One-command Docker Compose deployment for a college lab or think tank |
| Upload ingestion (core formats) | Jaish | CSV, TXT, PDF parsers; column-mapping step for CSV; same NLP pipeline |
| Upload formats (**Stretch**) | Jaish | Excel and Word text extraction |
| Upload safety | Jay + Jaish | Type check by content, size and page limits, sandboxed parsing with timeouts, optional antivirus scan, files stored outside the web root |
| Workspaces and trust labels | Jay | Private workspace per user or team; uploads marked source_type user_upload; promoted to shared only by analyst; excluded from threat scores unless analyst includes them |
| Correction and takedown workflow | Jay | Anyone can report wrong or harmful profile content; analyst reviews, corrects or removes; outcome logged |
| Retention and backups | Jay | Retention limits for profile data and uploads; scheduled database backups |

### Solid Success Criteria

```
✓ 24/7 uptime with <1% downtime
✓ All 96+ sources monitored automatically
✓ Multilingual: Urdu + Chinese + Hindi processing correctly
✓ Auth system with role-based access control
✓ <500ms API response time with Redis cache
✓ CI/CD auto-deploys on push to main
✓ Monitoring dashboard live
✓ Test coverage >80%
✓ iDEX application submitted with live demo
✓ At least 1 external demo completed
✓ Audit log records key analyst actions
✓ Analyst can open a case, attach evidence and add notes
✓ SitReps require analyst approval before being marked final
✓ New source can be added through the connector framework
✓ System runs from a single Docker Compose command
✓ CSV, TXT and PDF uploads are processed and appear only in the uploader's workspace
✓ Oversized, wrong-type or malformed files are rejected safely
✓ A reported profile error can be corrected or removed, with a log entry
```

---

## 12. Full Tech Stack by Stage

| Layer | MVP | Mid | Solid |
|---|---|---|---|
| Scraper | feedparser, httpx | + GDELT API | + Tweepy, Telethon, Sentinel |
| Scheduler | APScheduler | APScheduler | Celery + Redis |
| NLP | HuggingFace basics | + spaCy, sentence-transformers | + IndicBERT |
| LLM | — | Groq Llama 3 | Groq + fallback |
| Database | PostgreSQL + pgvector | Same | + Redis |
| Backend | FastAPI | + new routes | + Auth + rate limits |
| Frontend | Next.js basic | + Leaflet + Recharts | + Auth + monitoring UI |
| Deploy | Railway/Render | Same | VPS + Nginx + SSL |
| Monitoring | Logs only | Logs + alerts | Prometheus + Grafana + Sentry |
| Tests | pytest basic | pytest expanded | >80% coverage |
| Ontology / Graph | — | Postgres entity tables + Cytoscape.js | Same + graph caching |
| Search | — | PostgreSQL full-text + pgvector | Same + Redis cache |
| Provenance | Source and model version fields | + Lineage panel | + Reviewer tracking |
| Security | — | — | JWT roles + audit log |
| Offline LLM | — | — | Optional Ollama (stretch) |
| Entity resolution | — | rapidfuzz, unidecode, embeddings, rules | + analyst feedback |
| Profiles | — | Profile tables + Cytoscape.js + Leaflet | + corrections workflow |
| Upload parsing | — | — | pandas, pypdf, python-magic, optional ClamAV |

---

## 13. Git Workflow

```
main          → always deployable, protected branch
dev           → integration branch, merge here first
feat/jay/*    → Jay's features
feat/ary/*    → Ary's features
feat/jaish/*  → Jaish's features
```

**Rules:**
- Never push directly to main
- PR into dev → Jay reviews → merge
- dev to main only at stage milestone completion
- Commit format: feat: / fix: / refactor: / docs: / test:

---

## 14. Milestones

| # | Milestone | Owner | Target |
|---|---|---|---|
| M1 | Scraper live on 15 sources | Jaish | Week 2 |
| M2 | Basic NLP pipeline running | Ary | Week 4 |
| M3 | MVP dashboard deployed | Jay | Week 6 |
| ✅ | **MVP COMPLETE** | All | Month 2 |
| M4 | Event threading working | Ary | Month 3 |
| M5 | Threat scores + grounded SitRep live | Ary + Jay | Month 3.5 |
| M5b | Entity graph + search + watchlists | Ary + Jay | Month 3.75 |
| M5c | Entity profiles + disambiguation + review queue | Ary + Jay | Month 4 |
| M6 | Full dashboard with map | Jay | Month 4 |
| ✅ | **MID COMPLETE** | All | Month 4 |
| M7 | 96 sources + social | Jaish | Month 5 |
| M8 | Auth + cache + async | Jay | Month 5 |
| M9 | Multilingual + human review loop (deepfake = stretch) | Ary | Month 5.5 |
| M9b | Cases + audit log + connector framework | Jay + Jaish | Month 5.5 |
| M9c | Safe data upload + workspaces + correction workflow | Jay + Jaish | Month 5.75 |
| M10 | CI/CD + monitoring | Jay | Month 6 |
| M11 | iDEX application submitted | Jay | Month 6 |
| ✅ | **SOLID COMPLETE** | All | Month 6 |

---

## 15. Startup Path

```
Month 2 — MVP done
  Demo to 2-3 defence journalists and researchers
  Validate problem is real, collect feedback

Month 4 — Mid done
  Apply to iDEX Sprint (grants up to Rs 1.5Cr)
  Pitch to IDSA, ORF, Takshashila as pilot users

Month 6 — Solid done
  Live deployment with 1 paying or pilot customer
  Build case study from real usage
  Explore iDEX DISC, NDCI, T-Hub accelerators

Phase 1 customers:
  Defence think tanks (IDSA, ORF, Carnegie India)
  Private security consulting firms
  Defence journalism desks

Phase 2 customers (post-iDEX):
  Ministry of Defence
  State police intelligence wings
  BSF, CRPF via tender
```

---

## 16. Scope Guardrails

The Palantir-inspired features add ambition. These rules keep the project finishable.

### 16.1 Must-win priorities (never cut)

| # | Priority | Why |
|---|---|---|
| 1 | Hand-labelled evaluation set and measured accuracy | Turns claims into evidence; core of the viva and any paper |
| 2 | Explainable event threading and entity graph | Our main differentiator |
| 3 | Grounded SitRep with per-claim citations | Answers the LLM-hallucination question |
| 4 | Provenance on every derived fact | The "explain" principle |
| 5 | Source health and freshness page | Visible reliability |
| 6 | India and South Asia source ring with working Urdu and Chinese translation | The reason the project exists |
| 7 | Entity profiles with careful disambiguation and attributed facts | The signature feature, and the one with the highest risk if done carelessly |

### 16.2 Cut order if behind schedule (cut from the top)

1. Twitter/X, satellite and deepfake detection
2. Excel and Word upload formats; "Ask Raksha" question answering; offline local-LLM mode
3. Case folders beyond the basics
4. Extra source expansion beyond 40
5. Celery, Grafana and extra infrastructure polish

Never cut: provenance, attribution rules, the disambiguation review queue, the correction workflow and the evaluation set. These are what make the profile feature safe.

### 16.3 Honest limits (say these out loud)

- Ships with public data only: no classified or government integration. Data analysts upload is their responsibility and stays private to them.
- No security accreditation or air-gapped certification.
- Pilot scale for one organisation, not national scale.
- Outputs are indicators for analysts, not verified intelligence.
- The platform is **Palantir-inspired**, not a replacement for it.

---

## 17. Safeguards, Risks and Mitigations

Every caution raised during planning, with the solution built into the project. Review this table at each stage milestone.

| # | Risk | Mitigation built into the plan | Owner | When |
|---|---|---|---|---|
| 1 | Wrong person linked (name clashes, transliteration) | Three-level rule: only strong evidence auto-links; medium goes to analyst review; weak stays separate. Precision over recall. Merges are reversible and logged. Measure precision on a labelled pair set | Ary + Jay | Mid |
| 2 | System labels a person unfairly (e.g. 'terrorist', 'criminal') | No system-assigned labels. Statements are attributed to a source and carry claim_status (reported, official designation, analyst verified). UI wording rules enforce 'reported by' language | Jay + Ary | Mid |
| 3 | Thousands of junk profiles | Entities start as candidates; become profiles after at least 3 articles from at least 2 sources, or on analyst promotion | Ary | Mid |
| 4 | Privacy and law (DPDP Act 2023, defamation) when profiling people | Public reporting only; no scraping of private individuals' social media; no facial recognition; data minimisation; retention limits; correction and takedown workflow; disclaimer in UI; seek guidance from the guide or college | Jay | Mid–Solid |
| 5 | Inferring sensitive attributes (religion, caste, ethnicity, health) | Never inferred, never stored for a person; filter tested in evaluation | Ary | Mid |
| 6 | Bias and errors in NLP, especially Urdu and Chinese | Report precision, recall and F1 per language; error analysis; human review before reports become final | Ary | Mid |
| 7 | LLM hallucination in SitReps and profile summaries | Grounded generation with a citation for every sentence; unsupported sentences flagged; analyst approval | Ary | Mid |
| 8 | Misinformation in sources | Corroboration across independent sources; CONTRADICTS links; source ring and reliability notes shown | Ary | Mid |
| 9 | Overclaiming accuracy | Labelled evaluation set from month one; targets stated as targets until measured | All | MVP |
| 10 | Overclaiming against Palantir | Use 'Palantir-inspired'; state the limits (Section 16.3) | Jay | All |
| 11 | Malicious or oversized uploads | Allow-list of types checked by content, size and page limits, sandboxed parsing with timeouts, optional antivirus scan, storage outside the web root | Jay + Jaish | Solid |
| 12 | Uploaded data leaking into the shared layer | Private workspace by default; analyst must explicitly promote; all actions audited; user responsible for their data (notice shown) | Jay | Solid |
| 13 | 'Any format' is too broad | Core: CSV, TXT, PDF. Stretch: Excel, Word. Images, audio and video are future work | Jaish | Solid |
| 14 | Uploaded data less reliable than public sources | Marked source_type user_upload, shown with a trust label, excluded from threat scores unless the analyst includes it | Ary + Jay | Solid |
| 15 | Scraping terms of service and robots rules | Per-source terms check before enabling; respect robots rules; rate limits; use official feeds or APIs where available | Jaish | MVP |
| 16 | Copyright of collected articles | Store headline, summary and link; short excerpts only; no republishing of full text | Jay | MVP |
| 17 | Adversary-country sources block automated access | Retry with backoff; proxy support; failing sources shown on the health page; no dependence on any single source | Jaish | Mid |
| 18 | Source outages hidden from analysts | Per-source health records with distinct states: ok, stale, failed, empty | Jaish | MVP |
| 19 | Embedding model and database dimension mismatch | Fix one embedding model early; vector column size set to match; covered by a test | Ary | MVP |
| 20 | LLM provider or model name changes | Model name in configuration; fallback provider; optional local model | Ary | Mid |
| 21 | Scope too large for the timeline | Must-win list, stretch markers and cut order (Section 16); weekly scope review by the lead | Jay | All |
| 22 | Licence problems when studying other repositories | Study ideas, write our own code, cite the project as related work (some, such as World Monitor, use AGPL-3.0) | All | All |
| 23 | Security of the platform itself | JWT roles, audit log, secrets in environment variables, HTTPS, dependency updates | Jay | Solid |
| 24 | Data loss | Scheduled database backups and a documented restore step | Jay | Solid |
| 25 | iDEX eligibility and grant details unverified | Check the official iDEX site before applying; do not quote figures until verified | Jay | Solid |

---

## 18. How to Use This Document

| When | Read |
|---|---|
| Before starting any module | Stage section (9, 10, or 11) + ownership table (Section 6) |
| Writing a PR | Success criteria for current stage |
| Pitching to anyone | Sections 1, 2, 3, 4, 7, 15 |
| iDEX application | Sections 1, 2, 3, 5, 9, 10, 11, 15 |
| Lost on scope | Section 4 (one line per stage) and Section 16 (guardrails) |
| Conflict on ownership | Section 6 — ownership is final |
| Ethics, privacy or "what if it goes wrong" questions | Section 17 (risk register) and Section 8.6 (disambiguation) |

---

*Last updated: October 2026 | Team: Jay (lead) · Ary · Jaish*
