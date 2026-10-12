# Raksha AI — Architecture

## 4-Floor Pipeline

```
Floor 4 → Dashboard     (frontend/)   — Next.js, Leaflet.js, Recharts
Floor 3 → Report Engine (report/)     — Threat scoring, anomaly detection, LLM SitRep
Floor 2 → NLP Engine    (engine/)     — Translation, NER, classification, embeddings
Floor 1 → Data Layer    (scraper/)    — RSS, NewsAPI, APScheduler, PostgreSQL
```

## Data Flow

```
Every 4h   Scraper → 96+ sources → dedup via url_hash → PostgreSQL (articles)
Every 4h   NLP Engine → SELECT WHERE is_processed=FALSE → translate + NER + classify
Per art.   Event threading → pgvector cosine search + entity match → events table
Daily 6AM  Report Engine → last 24h data → threat scores → anomaly detect → LLM SitRep
On demand  FastAPI → serves Dashboard (map + graphs + SitRep)
```

## Ring Model

| Ring | Coverage       | Priority |
|------|----------------|----------|
| 1    | India          | High     |
| 2    | Pakistan+China | Critical |
| 3    | Regional       | Medium   |
| 4    | Global         | High     |

## Team Ownership

| Module    | Owner |
|-----------|-------|
| scraper/  | Jaish |
| engine/   | Ary   |
| report/   | Ary + Jay |
| api/      | Jay   |
| frontend/ | Jay   |
| database/ | Jay   |
| common/   | Jay   |
