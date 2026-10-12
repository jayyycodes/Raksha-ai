"""
Shared constants used across all modules.
"""

# Geopolitical Rings
RING_INDIA     = 1
RING_ADVERSARY = 2
RING_REGIONAL  = 3
RING_GLOBAL    = 4

# Event Types
EVENT_TYPES = [
    "border_incident", "cyber_attack", "terror_activity",
    "diplomatic", "disinformation", "military_movement",
    "naval", "aerial", "nuclear", "general",
]

# Sentiment
SENTIMENT_NEUTRAL    = "neutral"
SENTIMENT_AGGRESSIVE = "aggressive"
SENTIMENT_ALARMING   = "alarming"

# Alert Severity
SEVERITY_LOW      = "low"
SEVERITY_MEDIUM   = "medium"
SEVERITY_HIGH     = "high"
SEVERITY_CRITICAL = "critical"

# Event Status
STATUS_ONGOING  = "ongoing"
STATUS_RESOLVED = "resolved"
STATUS_WATCHING = "watching"

# NewsAPI Keywords
NEWSAPI_KEYWORDS = [
    "Indian Army",
    "Indian Air Force",
    "Indian Navy",
    "LAC border",
    "Line of Control",
    "Pakistan India border",
    "China India border",
    "DRDO",
    "Kashmir conflict",
    "Ladakh",
    "Arunachal Pradesh border",
]

# HTTP
USER_AGENT = "Mozilla/5.0 (compatible; RakshaAI/1.0; +https://github.com/jayyycodes/raksha-ai)"

# Scraper
REQUEST_DELAY_SECONDS  = 1.5
MAX_CONTENT_LENGTH     = 50000
MIN_TITLE_LENGTH       = 5
LANG_DETECT_MIN_CHARS  = 20
