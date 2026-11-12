"""
NLP Pipeline — orchestrates the full analysis flow for each article.
Owner: Ary / Jay (Lead)
Stage: 2 (Mid)

Bridges callers of `engine.pipeline` into the full Stage 2 pipeline in `pipeline.runner`:
    1. Translation (if non-English)
    2. NER extraction & Ontology Disambiguation
    3. Event classification & Sentiment analysis
    4. 768-dim Embedding generation
    5. Event threading & Regional threat scoring
"""
from common.logger import get_logger
from pipeline.runner import (
    process_new_articles as _runner_process_new_articles,
    process_single_article as _runner_process_single_article,
)

logger = get_logger(__name__)


def process_article(article_id: int) -> dict:
    """Run the full Stage 2 NLP & ontology pipeline on a single article."""
    return _runner_process_single_article(article_id)


def process_new_articles() -> int:
    """Fetch all unprocessed articles and run the complete Stage 2 pipeline."""
    return _runner_process_new_articles(run_batch_intelligence=True)
