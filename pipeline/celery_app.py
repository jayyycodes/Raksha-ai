"""
Celery Application Configuration — Raksha AI Stage 3 Solid
Owner: Jay
Stage: 3 (M10: Async Task Pipelines)
"""
import os
from celery import Celery
from common.config import settings

broker_url = os.getenv("CELERY_BROKER_URL", getattr(settings, "REDIS_URL", "redis://localhost:6379/0"))
result_backend = os.getenv("CELERY_RESULT_BACKEND", getattr(settings, "REDIS_URL", "redis://localhost:6379/0"))

celery_app = Celery(
    "raksha_worker",
    broker=broker_url,
    backend=result_backend,
    include=["pipeline.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min hard limit per task
    task_soft_time_limit=240,  # 4 min soft warning
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
