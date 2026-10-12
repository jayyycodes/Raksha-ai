# Setup Guide

## Prerequisites
- Python 3.11+
- Docker + Docker Compose
- Free NewsAPI key: https://newsapi.org/register

## Local Setup (with Docker DB)

```bash
# 1. Clone and configure
git clone https://github.com/jayyycodes/raksha-ai.git
cd raksha-ai
cp .env.example .env        # fill in NEWS_API_KEY

# 2. Start PostgreSQL with pgvector
docker-compose up -d db
docker-compose ps           # wait until rakshaai_db shows "healthy"

# 3. Python environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Init database
docker exec -i rakshaai_db psql -U raksha -d rakshaai < database/schema.sql
python -m database.seed

# 5. Run scraper
python -m scraper.scheduler
```

## Full Docker Setup

```bash
cp .env.example .env        # fill in NEWS_API_KEY
docker-compose up -d
docker-compose logs -f scraper
```

## Verify After First Run

```sql
-- Check articles per source
SELECT s.name, COUNT(a.id) AS articles, MAX(a.scraped_at) AS last_scraped
FROM sources s
LEFT JOIN articles a ON s.id = a.source_id
GROUP BY s.name
ORDER BY articles DESC;
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| DB connection fails | Check DATABASE_URL in .env matches docker-compose creds |
| pgvector missing | Use `pgvector/pgvector:pg15` image (already in docker-compose.yml) |
| NewsAPI returns empty | Free tier only returns articles up to 1 month old |
| Chinese sources blocked | Set PROXY_URL in .env |
| langdetect crashes | Short text (<20 chars) — falls back to source default language |
