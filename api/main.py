"""
FastAPI Application — Raksha AI API
Owner: Jay
Stage: 1 MVP

Run: uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Raksha AI",
    description="Palantir-inspired OSINT Intelligence Platform for India's Defence Context",
    version="0.1.0-mvp",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ──────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "raksha-ai", "stage": "mvp"}


@app.get("/api/health", tags=["Health"])
def health_check():
    from common.db import check_connection
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


# ── MVP Routers ─────────────────────────────────────────────────
from api.routes.articles import router as articles_router
from api.routes.sources import router as sources_router
from api.routes.stats import router as stats_router

app.include_router(articles_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
