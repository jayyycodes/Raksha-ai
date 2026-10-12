"""
Sentiment Analyzer — classifies article sentiment in defence context.
Owner: Ary
Stage: 2

Maps to sentiment values from common/constants.py:
    neutral, aggressive, alarming

Usage:
    from engine.sentiment import analyze_sentiment
    result = analyze_sentiment("Pakistan test-fires nuclear-capable missile")
    # {"sentiment": "alarming", "confidence": 0.91}
"""
from common.constants import SENTIMENT_NEUTRAL, SENTIMENT_AGGRESSIVE, SENTIMENT_ALARMING
from common.logger import get_logger

logger = get_logger(__name__)

SENTIMENT_LABELS = [SENTIMENT_NEUTRAL, SENTIMENT_AGGRESSIVE, SENTIMENT_ALARMING]


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of article text in a defence/geopolitical context.

    This is NOT standard positive/negative sentiment. It measures:
        - neutral:    factual reporting, routine events
        - aggressive: hostile rhetoric, provocative actions
        - alarming:   escalation signals, threat indicators

    Args:
        text: Article text (English)

    Returns:
        {"sentiment": str, "confidence": float}

    TODO (Ary):
        1. Use a fine-tuned or zero-shot classifier
        2. Defence-specific sentiment differs from general sentiment
           (a "positive" military test is "alarming" in our context)
        3. Weight adversary source sentiment more heavily
    """
    raise NotImplementedError("Sentiment analyzer not yet implemented — Stage 2")
