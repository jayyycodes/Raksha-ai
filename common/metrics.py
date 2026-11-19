"""
Prometheus Metrics Engine — Raksha AI Stage 3 Solid
Owner: Jay
Stage: 3 (M10: Observability & Hardening)
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    REGISTRY = None

    class _NoOpMetric:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass

    Counter = Histogram = Gauge = _NoOpMetric

    def generate_latest(registry=None):
        return b"# prometheus_client not installed\n"


# ── HTTP & Platform Metrics ──────────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "raksha_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "raksha_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── Ingestion & NLP Pipelines Metrics ─────────────────────────────────────────
INGESTION_ARTICLES_TOTAL = Counter(
    "raksha_ingestion_articles_total",
    "Total articles ingested into Raksha AI",
    ["source_name", "ring", "status"],
)

NLP_EXTRACTION_DURATION_SECONDS = Histogram(
    "raksha_nlp_extraction_duration_seconds",
    "Duration of NER and relationship extraction passes in seconds",
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)

# ── Cache Performance ────────────────────────────────────────────────────────
CACHE_HITS_TOTAL = Counter(
    "raksha_cache_hits_total",
    "Total cache hit count",
    ["cache_key_prefix"],
)

CACHE_MISSES_TOTAL = Counter(
    "raksha_cache_misses_total",
    "Total cache miss count",
    ["cache_key_prefix"],
)

# ── Intelligence State Gauges ────────────────────────────────────────────────
ACTIVE_CASES_GAUGE = Gauge(
    "raksha_active_cases_total",
    "Current total active investigation cases in platform",
)

THREAT_SCORE_GAUGE = Gauge(
    "raksha_theatre_threat_score",
    "Current weighted threat score per security ring or theatre",
    ["theatre_or_ring"],
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Measures latency and request outcomes for all incoming HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.time() - start_time
            normalized_path = _normalize_path(path)
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=normalized_path, status=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=normalized_path).observe(duration)

        return response


def _normalize_path(path: str) -> str:
    """Group resource IDs into parameterized patterns to preserve metric bucketing."""
    import re
    p = re.sub(r"/\d+", "/{id}", path)
    return p[:64]


def get_metrics_response() -> Response:
    """Generate Prometheus scrape endpoint payload."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
