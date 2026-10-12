"""
NLP Pipeline — orchestrates the full analysis flow for each article.
Owner: Ary
Stage: 2

Processes unprocessed articles through:
    1. Translation (if non-English)
    2. NER extraction
    3. Event classification
    4. Sentiment analysis
    5. Embedding generation (Stage 2.5)

Then marks articles as is_processed=TRUE.

Usage:
    from engine.pipeline import process_new_articles
    process_new_articles()  # processes all WHERE is_processed=FALSE
"""
from common.logger import get_logger

logger = get_logger(__name__)


def process_article(article_id: int) -> dict:
    """
    Run the full NLP pipeline on a single article.

    Args:
        article_id: ID from the articles table

    Returns:
        {
            "article_id": int,
            "translated_text": str | None,
            "event_type": str,
            "sentiment": str,
            "threat_level": int,
            "entities": list[dict],
            "confidence": float,
        }

    TODO (Ary):
        1. Fetch article from DB
        2. Translate if language != 'en'
        3. Run NER → store in entities table
        4. Classify event type
        5. Analyze sentiment
        6. Calculate threat_level (1-10) from event_type + sentiment + source ring
        7. Store results in article_analysis table
        8. Set articles.is_processed = TRUE
    """
    raise NotImplementedError("NLP pipeline not yet implemented — Stage 2")


def process_new_articles() -> int:
    """
    Fetch all unprocessed articles and run the pipeline.

    Returns:
        Number of articles processed

    TODO (Ary):
        1. SELECT * FROM articles WHERE is_processed = FALSE
        2. For each article, call process_article()
        3. Log summary: processed count, failures, time elapsed
    """
    raise NotImplementedError("Batch processing not yet implemented — Stage 2")
