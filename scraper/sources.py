"""
Single source of truth for all monitored news sources.
Used by database/seed.py and scraper/scheduler.py
Expanded to 40 monitored sources across 4 Security Rings for Stage 2 (Mid).
"""
from common.constants import (
    RING_INDIA, RING_ADVERSARY, RING_REGIONAL, RING_GLOBAL, NEWSAPI_KEYWORDS
)

RSS_SOURCES = [
    # -------------------------------------------------------------------------
    # Ring 1 — India (12 sources)
    # Ground truth from the Indian national and defence perspective
    # -------------------------------------------------------------------------
    {"name": "The Hindu",                "url": "https://www.thehindu.com",            "rss_url": "https://www.thehindu.com/news/national/feeder/default.rss",            "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "ANI News",                 "url": "https://www.aninews.in",              "rss_url": "https://www.aninews.in/rss/india.xml",                                 "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "The Print",                "url": "https://theprint.in",                 "rss_url": "https://theprint.in/feed/",                                            "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "PIB India",                "url": "https://pib.gov.in",                  "rss_url": "https://pib.gov.in/RssMain.aspx",                                      "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Indian Express",           "url": "https://indianexpress.com",           "rss_url": "https://indianexpress.com/section/india/feed/",                        "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Tribune India",            "url": "https://www.tribuneindia.com",        "rss_url": "https://www.tribuneindia.com/rss/feed.aspx?cat_id=7",                 "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Times of India Defence",   "url": "https://timesofindia.indiatimes.com", "rss_url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",        "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Hindustan Times",          "url": "https://www.hindustantimes.com",      "rss_url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",     "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Bharat Shakti",            "url": "https://bharatshakti.in",             "rss_url": "https://bharatshakti.in/feed/",                                        "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "MP-IDSA",                  "url": "https://www.idsa.in",                 "rss_url": "https://www.idsa.in/rss.xml",                                          "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Swarajya Defence",         "url": "https://swarajyamag.com",             "rss_url": "https://swarajyamag.com/feed",                                         "ring": RING_INDIA,     "country": "India",       "language": "en"},
    {"name": "Firstpost India",          "url": "https://www.firstpost.com",          "rss_url": "https://www.firstpost.com/rss/india.xml",                             "ring": RING_INDIA,     "country": "India",       "language": "en"},

    # -------------------------------------------------------------------------
    # Ring 2 — Adversaries (10 sources)
    # Pakistani and Chinese state and mainstream media narratives
    # -------------------------------------------------------------------------
    {"name": "Dawn Pakistan",            "url": "https://www.dawn.com",                "rss_url": "https://www.dawn.com/feed",                                            "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "Geo News",                 "url": "https://www.geo.tv",                  "rss_url": "https://www.geo.tv/rss/1",                                             "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "The Express Tribune",      "url": "https://tribune.com.pk",              "rss_url": "https://tribune.com.pk/feed/pakistan",                                 "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "The News International",   "url": "https://www.thenews.com.pk",          "rss_url": "https://www.thenews.com.pk/rss/1/1",                                   "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "Daily Times Pakistan",     "url": "https://dailytimes.com.pk",          "rss_url": "https://dailytimes.com.pk/feed/",                                      "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en"},
    {"name": "Global Times",             "url": "https://www.globaltimes.cn",          "rss_url": "https://www.globaltimes.cn/rss/outbrain.xml",                          "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "Xinhua",                   "url": "https://english.news.cn",             "rss_url": "http://www.xinhuanet.com/english/rss/chinalatestnews.xml",             "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "SCMP",                     "url": "https://www.scmp.com",                "rss_url": "https://www.scmp.com/rss/91/feed",                                     "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "China Daily",              "url": "https://www.chinadaily.com.cn",       "rss_url": "https://www.chinadaily.com.cn/rss/china_rss.xml",                     "ring": RING_ADVERSARY, "country": "China",       "language": "en"},
    {"name": "People's Daily",           "url": "http://en.people.cn",                 "rss_url": "http://en.people.cn/rss/90786.xml",                                    "ring": RING_ADVERSARY, "country": "China",       "language": "en"},

    # -------------------------------------------------------------------------
    # Ring 3 — Regional Neighbours (9 sources)
    # Neighbourhood developments across SAARC and South Asian borderlands
    # -------------------------------------------------------------------------
    {"name": "Tolo News",                "url": "https://tolonews.com",                "rss_url": "https://tolonews.com/rss.xml",                                         "ring": RING_REGIONAL,  "country": "Afghanistan", "language": "en"},
    {"name": "Kathmandu Post",           "url": "https://kathmandupost.com",           "rss_url": "https://kathmandupost.com/rss",                                        "ring": RING_REGIONAL,  "country": "Nepal",       "language": "en"},
    {"name": "Daily Star Bangladesh",    "url": "https://www.thedailystar.net",        "rss_url": "https://www.thedailystar.net/rss.xml",                                 "ring": RING_REGIONAL,  "country": "Bangladesh",  "language": "en"},
    {"name": "Dhaka Tribune",            "url": "https://www.dhakatribune.com",        "rss_url": "https://www.dhakatribune.com/feed",                                    "ring": RING_REGIONAL,  "country": "Bangladesh",  "language": "en"},
    {"name": "Colombo Gazette",          "url": "https://colombogazette.com",          "rss_url": "https://colombogazette.com/feed/",                                     "ring": RING_REGIONAL,  "country": "Sri Lanka",   "language": "en"},
    {"name": "Daily FT Sri Lanka",       "url": "https://www.ft.lk",                   "rss_url": "https://www.ft.lk/rss",                                                "ring": RING_REGIONAL,  "country": "Sri Lanka",   "language": "en"},
    {"name": "Kuensel Bhutan",           "url": "https://kuenselonline.com",           "rss_url": "https://kuenselonline.com/feed/",                                      "ring": RING_REGIONAL,  "country": "Bhutan",      "language": "en"},
    {"name": "The Irrawaddy Myanmar",    "url": "https://www.irrawaddy.com",           "rss_url": "https://www.irrawaddy.com/feed",                                       "ring": RING_REGIONAL,  "country": "Myanmar",     "language": "en"},
    {"name": "The Edition Maldives",     "url": "https://edition.mv",                  "rss_url": "https://edition.mv/rss",                                               "ring": RING_REGIONAL,  "country": "Maldives",    "language": "en"},

    # -------------------------------------------------------------------------
    # Ring 4 — Global & Strategic (9 sources)
    # Neutral corroboration, global news wires, and strategic defence journals
    # -------------------------------------------------------------------------
    {"name": "Reuters",                  "url": "https://www.reuters.com",             "rss_url": "https://feeds.reuters.com/reuters/INtopNews",                          "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "BBC Asia",                 "url": "https://www.bbc.com",                 "rss_url": "http://feeds.bbci.co.uk/news/world/asia/rss.xml",                      "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Al Jazeera",               "url": "https://www.aljazeera.com",           "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",                            "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Defense News",             "url": "https://www.defensenews.com",         "rss_url": "https://www.defensenews.com/arc/outboundfeeds/rss/",                   "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Defense One",              "url": "https://www.defenseone.com",          "rss_url": "https://www.defenseone.com/rss/all/",                                  "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Breaking Defense",         "url": "https://breakingdefense.com",         "rss_url": "https://breakingdefense.com/feed/",                                    "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Naval News",               "url": "https://www.navalnews.com",           "rss_url": "https://www.navalnews.com/feed/",                                      "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "Air Force Technology",     "url": "https://www.airforce-technology.com", "rss_url": "https://www.airforce-technology.com/feed/",                              "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
    {"name": "RUSI Commentary",          "url": "https://www.rusi.org",                "rss_url": "https://www.rusi.org/rss/all.xml",                                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en"},
]

KEYWORDS = NEWSAPI_KEYWORDS
