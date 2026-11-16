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

# Sentry Error Tracking Initialization (if configured)
if os.getenv("SENTRY_DSN"):
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("ENVIRONMENT", "production"),
            traces_sample_rate=0.2,
        )
        logger.info("Sentry error tracking initialized")
    except Exception as exc:
        logger.warning(f"Could not initialize Sentry: {exc}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from common.metrics import PrometheusMetricsMiddleware, get_metrics_response
app.add_middleware(PrometheusMetricsMiddleware)


# ── Health & Observability ──────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "raksha-ai", "stage": "stage3-solid"}


@app.get("/metrics", tags=["Observability"], response_class=get_metrics_response.__annotations__.get("return"))
def prometheus_metrics():
    """Prometheus metrics scrape endpoint."""
    return get_metrics_response()


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

# ── Stage 3 Solid Routers (Auth, RBAC, Workspaces, Immutable Audit, Cases, BYOD Uploads, Corrections, Exports)
from api.routes.auth import router as auth_router
from api.routes.audit import router as audit_router
from api.routes.cases import router as cases_router
from api.routes.uploads import router as uploads_router
from api.routes.corrections import router as corrections_router
from api.routes.exports import router as exports_router

app.include_router(articles_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(uploads_router)
app.include_router(corrections_router)
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
app.include_router(exports_router, prefix="/api")
