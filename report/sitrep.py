"""
SitRep Generator — produces daily AI-generated Situation Reports.
Owner: Ary
Stage: 3

Uses Groq API (Llama 3 70B) to generate a structured morning brief at 6 AM daily.

SitRep structure:
    1. Executive Summary (3-4 sentences)
    2. Top Threats (ranked by score)
    3. Anomaly Alerts (if any)
    4. Ongoing Event Summaries
    5. 24-Hour Watch List

Stored in the sitreps table.

Usage:
    from report.sitrep import generate_sitrep
    report = generate_sitrep()  # generates for today
"""
from common.logger import get_logger

logger = get_logger(__name__)

SITREP_PROMPT_TEMPLATE = '''
You are a defence intelligence analyst producing a daily Situation Report (SitRep)
for India's national security leadership.

Based on the following data from the last 24 hours:

## THREAT SCORES
{threat_scores}

## ANOMALY ALERTS
{anomalies}

## KEY ARTICLES (top 20 by threat relevance)
{articles}

## ONGOING EVENTS
{events}

Generate a structured SitRep with:
1. **EXECUTIVE SUMMARY** — 3-4 sentence overview of the security landscape
2. **TOP THREATS** — ranked list with region, score, trend, and brief explanation
3. **ANOMALY ALERTS** — any unusual spikes or patterns detected
4. **ONGOING SITUATIONS** — status update on tracked events
5. **24-HOUR WATCH LIST** — what to monitor in the next cycle

Use factual, concise military intelligence language. No speculation.
'''


def generate_sitrep(date: str | None = None) -> dict:
    """
    Generate a daily SitRep using LLM.

    Args:
        date: Date string (YYYY-MM-DD). Defaults to today.

    Returns:
        {"report_date": str, "content": str, "top_threats": list, "article_count": int}

    TODO (Ary):
        1. Gather last 24h data: threat scores, anomalies, top articles, events
        2. Format into prompt template
        3. Call Groq API (Llama 3 70B)
        4. Parse and validate response
        5. Store in sitreps table
        6. Handle API failures with retry + fallback
    """
    raise NotImplementedError("SitRep generation not yet implemented — Stage 3")
