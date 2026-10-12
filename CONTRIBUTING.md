# Contributing to Raksha AI

## Team

| Member | Role | Modules |
|--------|------|---------|
| **Jay** | Lead | `api/`, `frontend/`, `database/`, `common/`, DevOps |
| **Ary** | AI/ML | `engine/`, `report/scorer.py`, `report/sitrep.py`, `report/threading.py` |
| **Jaish** | Dev | `scraper/`, `tests/`, NewsAPI, source management |

## Quick Start

```bash
# 1. Clone & branch
git clone https://github.com/jayyycodes/raksha-ai.git
cd raksha-ai
git checkout dev
git checkout -b feat/<your-name>/<feature>

# 2. Setup
cp .env.example .env          # add your NEWS_API_KEY
docker-compose up -d db       # start PostgreSQL
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# 3. Init DB
docker exec -i rakshaai_db psql -U raksha -d rakshaai < database/schema.sql
python -m database.seed

# 4. Run scraper
python -m scraper.scheduler

# 5. Run API server (when working on api/)
# pip install fastapi uvicorn
# uvicorn api.main:app --reload --port 8000
```

## Git Workflow

```
main         → always deployable, protected
dev          → integration branch
feat/jay/*   → Jay's features
feat/ary/*   → Ary's features
feat/jaish/* → Jaish's features
```

### Rules
1. **Never push directly to `main`**
2. Create feature branches from `dev`
3. PR into `dev` → Jay reviews → merge
4. `dev` → `main` only at stage milestones

### Commit Format
```
feat: add NER extraction pipeline
fix: handle empty RSS feeds gracefully
refactor: move scoring logic to report/scorer.py
docs: update setup guide for Windows
test: add classifier accuracy tests
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=scraper --cov=common
```

## Module Ownership

Each member owns their modules end-to-end: **design → build → test → document**.

- Before working on a module, check the skeleton file — it has TODOs and specs
- Write tests for your module in `tests/test_<module>.py`
- Update docstrings when you implement a function
- Don't modify another member's module without discussing first

## Code Style

- Python 3.11+ type hints everywhere
- Docstrings on all public functions
- Use `common.logger.get_logger(__name__)` for logging
- Use `common.db.get_db()` context manager for DB access
- Constants go in `common/constants.py`
- Config goes in `.env` → `common/config.py`

## Current Stage: 1 (Data Collection)

See [docs/raksha-ai-proposal.md](docs/raksha-ai-proposal.md) for the full roadmap.
