"""
FastAPI Application — Raksha AI API
Owner: Jay
Stage: 1 MVP

Run: uvicorn api.main:app --reload --port 8000
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Raksha AI",
    description="Palantir-inspired OSINT Intelligence Platform for India's Defence Context",
    version="0.2.0-mid",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow local dev + configured deployed frontend origins
_allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if os.getenv("FRONTEND_URL"):
    _allowed_origins.append(os.getenv("FRONTEND_URL").rstrip("/"))
if os.getenv("CORS_ORIGINS"):
    _allowed_origins.extend(
        [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS").split(",") if o.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "raksha-ai", "stage": "stage2-mid"}


@app.get("/api/health", tags=["Health"])
def health_check():
    from common.db import check_connection
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


# ── Stage 1 MVP Routers ──────────────────────────────────────────
from api.routes.articles import router as articles_router
from api.routes.sources import router as sources_router
from api.routes.stats import router as stats_router

# ── Stage 2 Mid Routers (Ontology, Graph, Geospatial, Threats, Events, Alerts, Watchlists, Review)
from api.routes.graph import router as graph_router
from api.routes.map import router as map_router
from api.routes.profiles import router as profiles_router, entities_router
from api.routes.review import router as review_router, merge_suggestions_router
from api.routes.sitrep import router as sitrep_router, singular_router as sitrep_singular_router
from api.routes.search import router as search_router
from api.routes.events import router as events_router
from api.routes.threats import router as threats_router
from api.routes.alerts import router as alerts_router
from api.routes.watchlists import router as watchlists_router

app.include_router(articles_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(map_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")
app.include_router(entities_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(merge_suggestions_router, prefix="/api")
app.include_router(sitrep_router, prefix="/api")
app.include_router(sitrep_singular_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(threats_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(watchlists_router, prefix="/api")
