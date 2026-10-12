"""
Event Threading — links articles to ongoing events.
Owner: Ary
Stage: 2.5

Three linking methods:
    1. ENTITY_MATCH:  Same location + org + event_type → same event
    2. SEMANTIC:      pgvector cosine similarity > 0.75 with seed article
    3. PATTERN:       Same event_type + same region within 6-month window

Results stored in event_articles table with link_method and confidence.

Usage:
    from report.threading import thread_article
    event = thread_article(article_id=42)
    # Links article 42 to an existing event or creates a new one
"""
from common.logger import get_logger

logger = get_logger(__name__)


def thread_article(article_id: int) -> dict | None:
    """
    Attempt to link an article to an existing event, or create a new event.

    Args:
        article_id: ID of the article to thread

    Returns:
        {"event_id": int, "link_method": str, "confidence": float, "is_new": bool}
        or None if no event match found and article doesn't warrant a new event

    TODO (Ary):
        1. Fetch article + its entities + its embedding
        2. Try ENTITY_MATCH: find events with overlapping entities
        3. Try SEMANTIC: cosine search against event seed articles
        4. Try PATTERN: same event_type + region within 6 months
        5. If match found: insert into event_articles, update event.article_count
        6. If no match but high threat_level: create new event with this as seed
    """
    raise NotImplementedError("Event threading not yet implemented — Stage 2.5")


def rethread_all() -> int:
    """
    Re-run threading on all articles. Useful after model improvements.

    Returns:
        Number of articles re-threaded

    TODO (Ary):
        1. Clear event_articles table
        2. Process articles chronologically
        3. Log summary
    """
    raise NotImplementedError("Batch re-threading not yet implemented — Stage 2.5")
