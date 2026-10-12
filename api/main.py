"""
FastAPI Application — main entry point.
Owner: Jay
Stage: 3 (basic routes in MVP)

Run: uvicorn api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Raksha AI",
    description="OSINT Intelligence Platform API for Indian Defence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "raksha-ai"}


@app.get("/api/health", tags=["Health"])
def health_check():
    """Detailed health check with DB status."""
    from common.db import check_connection
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }


# TODO (Jay): Import and include route modules as they're built
# from api.routes import articles, sources, stats, map, threats, events, sitrep, alerts
# app.include_router(articles.router, prefix="/api")
# app.include_router(sources.router, prefix="/api")
# app.include_router(stats.router, prefix="/api")
