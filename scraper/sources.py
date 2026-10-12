"""
Single source of truth for all monitored news sources.
Used by database/seed.py and scraper/scheduler.py
"""
from common.constants import (
    RING_INDIA, RING_ADVERSARY, RING_REGIONAL, RING_GLOBAL, NEWSAPI_KEYWORDS
)

RSS_SOURCES = [
    # Ring 1 — India
    {"name": "The Hindu",      "url": "https://www.thehindu.com",    "rss_url": "https://www.thehindu.com/news/national/feeder/default.rss", "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "ANI News",       "url": "https://www.aninews.in",      "rss_url": "https://www.aninews.in/rss/india.xml",                      "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "The Print",      "url": "https://theprint.in",         "rss_url": "https://theprint.in/feed/",                                 "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "PIB India",      "url": "https://pib.gov.in",          "rss_url": "https://pib.gov.in/RssMain.aspx",                           "ring": RING_INDIA,     "country": "India",       "language": "en"},
    # Ring 2 — Adversaries (Critical)
    {"name": "Dawn Pakistan",  "url": "https://www.dawn.com",        "rss_url": "https://www.dawn.com/feed",                                 "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "Geo News",       "url": "https://www.geo.tv",          "rss_url": "https://www.geo.tv/rss/1",                                  "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "Global Times",   "url": "https://www.globaltimes.cn",  "rss_url": "https://www.globaltimes.cn/rss/outbrain.xml",               "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "Xinhua",         "url": "https://english.news.cn",     "rss_url": "http://www.xinhuanet.com/english/rss/chinalatestnews.xml",  "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "SCMP",           "url": "https://www.scmp.com",        "rss_url": "https://www.scmp.com/rss/91/feed",                          "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    # Ring 3 — Regional
    {"name": "Tolo News",      "url": "https://tolonews.com",        "rss_url": "https://tolonews.com/rss.xml",                              "ring": RING_REGIONAL,  "country": "Afghanistan", "language": "en"},
    {"name": "Kathmandu Post", "url": "https://kathmandupost.com",   "rss_url": "https://kathmandupost.com/rss",                             "ring": RING_REGIONAL,  "country": "Nepal",       "language": "en"},
    # Ring 4 — Global
    {"name": "Reuters",        "url": "https://www.reuters.com",     "rss_url": "https://feeds.reuters.com/reuters/INtopNews",               "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "BBC Asia",       "url": "https://www.bbc.com",         "rss_url": "http://feeds.bbci.co.uk/news/world/asia/rss.xml",           "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Al Jazeera",     "url": "https://www.aljazeera.com",   "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",                 "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Defense News",   "url": "https://www.defensenews.com", "rss_url": "https://www.defensenews.com/arc/outboundfeeds/rss/",        "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
]

KEYWORDS = NEWSAPI_KEYWORDS
