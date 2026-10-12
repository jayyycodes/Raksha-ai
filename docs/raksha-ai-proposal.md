# Raksha AI — Full Project Proposal
## From MVP to Production-Ready Defence-Tech Platform

---

## 0. Project Identity

| Field | Detail |
|---|---|
| **Project Name** | Raksha AI |
| **Domain** | Defence Tech · Open Source Intelligence (OSINT) |
| **Type** | Startup MVP → Production SaaS |
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

## 2. One-Line Per Stage

| Stage | What it is |
|---|---|
| **MVP** | Automated news collector + basic threat classifier + simple web dashboard |
| **Mid** | Event threading + regional threat scoring + AI-generated daily SitRep |
| **Solid** | Full production system — multilingual, scalable, deployed, monitored |

---

## 3. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                FLOOR 4 — DASHBOARD                       │
│  Next.js · Leaflet.js Map · Recharts · SitRep Viewer     │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                FLOOR 3 — REPORT ENGINE                   │
│  Threat Scoring · Anomaly Detection · Groq LLM SitRep    │
└────────────────────────┬─────────────────────────────────┘
                         │ DB reads
┌────────────────────────▼─────────────────────────────────┐
│                FLOOR 2 — NLP ENGINE                      │
│  Translation · NER · Event Classification · Embeddings   │
└────────────────────────┬─────────────────────────────────┘
                         │ raw articles
┌────────────────────────▼─────────────────────────────────┐
│                FLOOR 1 — DATA COLLECTION                 │
│  96+ RSS Sources · NewsAPI · APScheduler · PostgreSQL    │
└──────────────────────────────────────────────────────────┘
```

**Data flow:**
```
Every 4h   → Scraper collects 96+ sources → dedup → PostgreSQL
Every 4h   → NLP engine processes new articles → translate + NER + classify
Per article → Event threading → pgvector cosine search → link to historical events
Daily 6AM  → Report engine → threat scores + anomaly alerts + LLM SitRep
On demand  → FastAPI → serves dashboard (map, graphs, SitRep)
```

---

## 4. Team & Ownership

```
JAY (Lead)                 ARY                       JAISH
─────────────────          ─────────────────         ─────────────────
Architecture               NLP Engine                Data Collection
Database design            Event Threading           Scraper pipeline
FastAPI backend            Embeddings + pgvector     NewsAPI integration
DevOps + deployment        LLM SitRep generation     Scheduler
Frontend integration       Threat scoring model      Source management
Code reviews               Translation pipeline      Data quality
iDEX + pitch docs          Research + model eval     Testing + CI
```

**Rule:** Jay has final call on architecture and API contracts.
Each member owns their module end-to-end: design, build, test, document.

---

## 5. Source Coverage (96+)

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

## 6. Database (10 Tables)

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

---

## 7. Stage 1 — MVP

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
```

---

## 8. Stage 2 — Mid Build

**Timeline:** Month 3–4
**Goal:** System becomes intelligent. Events threaded. Threats scored. AI writes the brief.

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
```

---

## 9. Stage 3 — Solid (Deploy-Ready)

**Timeline:** Month 5–6
**Goal:** Production-grade. Monitored. Scalable. Ready for iDEX and investors.

### Module Ownership

| Module | Owner | What |
|---|---|---|
| Twitter/X monitoring | Jaish | Defence keyword tracking |
| Telegram channels | Jaish | Public defence/news channels |
| Satellite API | Jaish | Sentinel Hub + NASA FIRMS |
| Full 96-source coverage | Jaish | All rings at full capacity |
| Hindi/Marathi NLP | Ary | IndicBERT for regional content |
| Deepfake detection v1 | Ary | Image/video forgery signals |
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
```

---

## 10. Full Tech Stack by Stage

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

---

## 11. Git Workflow

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

## 12. Milestones

| # | Milestone | Owner | Target |
|---|---|---|---|
| M1 | Scraper live on 15 sources | Jaish | Week 2 |
| M2 | Basic NLP pipeline running | Ary | Week 4 |
| M3 | MVP dashboard deployed | Jay | Week 6 |
| ✅ | **MVP COMPLETE** | All | Month 2 |
| M4 | Event threading working | Ary | Month 3 |
| M5 | Threat scores + SitRep live | Ary + Jay | Month 3.5 |
| M6 | Full dashboard with map | Jay | Month 4 |
| ✅ | **MID COMPLETE** | All | Month 4 |
| M7 | 96 sources + social | Jaish | Month 5 |
| M8 | Auth + cache + async | Jay | Month 5 |
| M9 | Multilingual + deepfake | Ary | Month 5.5 |
| M10 | CI/CD + monitoring | Jay | Month 6 |
| M11 | iDEX application submitted | Jay | Month 6 |
| ✅ | **SOLID COMPLETE** | All | Month 6 |

---

## 13. Startup Path

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

## 14. How to Use This Document

| When | Read |
|---|---|
| Before starting any module | Stage section (7, 8, or 9) + ownership table |
| Writing a PR | Success criteria for current stage |
| Pitching to anyone | Sections 1, 2, 5, 13 |
| iDEX application | Sections 1, 3, 7, 8, 9, 13 |
| Lost on scope | Section 2 — one line per stage |
| Conflict on ownership | Section 4 — ownership is final |

---

*Last updated: October 2026 | Team: Jay (lead) · Ary · Jaish*
