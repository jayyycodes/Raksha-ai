"""
Tests for Celery Async Task Execution
"""
from pipeline.tasks import (
    task_recalculate_threat_scores,
    task_ingest_feed_source,
    task_process_article_nlp,
)


def test_task_recalculate_threat_scores():
    res = task_recalculate_threat_scores.apply()
    assert res.status == "SUCCESS"
    val = res.get()
    assert val["status"] == "success"
    assert "Global-Strategic" in val["scores"]


def test_task_ingest_feed_source_missing():
    res = task_ingest_feed_source.apply(args=[999999])
    assert res.status == "SUCCESS"
    val = res.get()
    assert val["status"] == "skipped"


def test_task_process_article_nlp_missing():
    res = task_process_article_nlp.apply(args=[999999])
    assert res.status == "SUCCESS"
    val = res.get()
    assert val["status"] == "skipped"
