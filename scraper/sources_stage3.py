"""
Full 96+ Source Coverage for Raksha AI (Stage 3 Solid - Milestone M7).
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Aligned with `docs/raksha-ai-proposal.md` Section 7:
- Ring 1 (India): 25 sources (Domestic + official)
- Ring 2 (Adversaries): 18 sources (Pakistan + China state & mainstream)
- Ring 3 (Regional): 12 sources (Neighbourhood & SAARC)
- Ring 4 (Global): 25 sources (Global defence wires & think-tanks)
- APIs: 6 sources (GDELT, NASA FIRMS, ACLED, ReliefWeb, etc.)
- Social: 10 sources (Public Telegram defence/OSINT channels)
Total: 96 sources
"""
from common.constants import (
    RING_INDIA, RING_ADVERSARY, RING_REGIONAL, RING_GLOBAL,
)

STAGE3_SOURCES_96: list[dict] = [
    # =========================================================================
    # Ring 1 — India (25 sources)
    # Domestic & official defense, national security, policy & regional press
    # =========================================================================
    {"name": "The Hindu",                "url": "https://www.thehindu.com",            "rss_url": "https://www.thehindu.com/news/national/feeder/default.rss",            "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "ANI News",                 "url": "https://www.aninews.in",              "rss_url": "https://www.aninews.in/rss/india.xml",                                 "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "The Print",                "url": "https://theprint.in",                 "rss_url": "https://theprint.in/feed/",                                            "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "PIB India",                "url": "https://pib.gov.in",                  "rss_url": "https://pib.gov.in/RssMain.aspx",                                      "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Indian Express",           "url": "https://indianexpress.com",           "rss_url": "https://indianexpress.com/section/india/feed/",                        "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Tribune India",            "url": "https://www.tribuneindia.com",        "rss_url": "https://www.tribuneindia.com/rss/feed.aspx?cat_id=7",                 "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Times of India Defence",   "url": "https://timesofindia.indiatimes.com", "rss_url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",        "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Hindustan Times",          "url": "https://www.hindustantimes.com",      "rss_url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",     "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Bharat Shakti",            "url": "https://bharatshakti.in",             "rss_url": "https://bharatshakti.in/feed/",                                        "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "MP-IDSA",                  "url": "https://www.idsa.in",                 "rss_url": "https://www.idsa.in/rss.xml",                                          "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Swarajya Defence",         "url": "https://swarajyamag.com",             "rss_url": "https://swarajyamag.com/feed",                                         "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Firstpost India",          "url": "https://www.firstpost.com",          "rss_url": "https://www.firstpost.com/rss/india.xml",                             "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "DD News",                  "url": "https://ddnews.gov.in",               "rss_url": "https://ddnews.gov.in/feed/",                                          "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "NDTV National",            "url": "https://www.ndtv.com",                "rss_url": "https://feeds.feedburner.com/ndtvnews-india-news",                    "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Economic Times Defence",   "url": "https://economictimes.indiatimes.com","rss_url": "https://economictimes.indiatimes.com/news/defence/rssfeeds/41416411.cms", "ring": RING_INDIA, "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Livemint Defence",         "url": "https://www.livemint.com",            "rss_url": "https://www.livemint.com/rss/news",                                    "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Deccan Herald",            "url": "https://www.deccanherald.com",        "rss_url": "https://www.deccanherald.com/rss/national.rss",                       "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Outlook India",            "url": "https://www.outlookindia.com",        "rss_url": "https://www.outlookindia.com/rss/national.xml",                       "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "The Telegraph India",      "url": "https://www.telegraphindia.com",      "rss_url": "https://www.telegraphindia.com/rss/india.xml",                         "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Daily Excelsior J&K",      "url": "https://www.dailyexcelsior.com",      "rss_url": "https://www.dailyexcelsior.com/feed/",                                 "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Kashmir Reader",           "url": "https://kashmirreader.com",           "rss_url": "https://kashmirreader.com/feed/",                                      "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Assam Tribune",            "url": "https://assamtribune.com",            "rss_url": "https://assamtribune.com/rss/assam",                                   "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Defence Aviation Post",    "url": "https://defenceaviationpost.com",     "rss_url": "https://defenceaviationpost.com/feed/",                                "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "Indian Defence Review",    "url": "http://www.indiandefencereview.com",  "rss_url": "http://www.indiandefencereview.com/feed/",                             "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},
    {"name": "StratNews Global",         "url": "https://stratnewsglobal.com",         "rss_url": "https://stratnewsglobal.com/feed/",                                    "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "rss"},

    # =========================================================================
    # Ring 2 — Adversaries (18 sources)
    # Pakistani and Chinese state and mainstream media narratives
    # =========================================================================
    {"name": "Dawn Pakistan",            "url": "https://www.dawn.com",                "rss_url": "https://www.dawn.com/feed",                                            "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Geo News",                 "url": "https://www.geo.tv",                  "rss_url": "https://www.geo.tv/rss/1",                                             "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "The Express Tribune",      "url": "https://tribune.com.pk",              "rss_url": "https://tribune.com.pk/feed/pakistan",                                 "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "The News International",   "url": "https://www.thenews.com.pk",          "rss_url": "https://www.thenews.com.pk/rss/1/1",                                   "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Daily Times Pakistan",     "url": "https://dailytimes.com.pk",          "rss_url": "https://dailytimes.com.pk/feed/",                                      "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "The Nation Pakistan",      "url": "https://nation.com.pk",               "rss_url": "https://nation.com.pk/feed",                                           "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Dunya News Pakistan",      "url": "https://dunyanews.tv",                "rss_url": "https://dunyanews.tv/rss/pakistan.xml",                                "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Daily Pakistan Global",    "url": "https://en.dailypakistan.com.pk",     "rss_url": "https://en.dailypakistan.com.pk/feed",                                 "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Pakistan Today",           "url": "https://profit.pakistantoday.com.pk", "rss_url": "https://profit.pakistantoday.com.pk/feed/",                           "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "rss"},
    {"name": "Global Times",             "url": "https://www.globaltimes.cn",          "rss_url": "https://www.globaltimes.cn/rss/outbrain.xml",                          "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "Xinhua",                   "url": "https://english.news.cn",             "rss_url": "http://www.xinhuanet.com/english/rss/chinalatestnews.xml",             "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "SCMP",                     "url": "https://www.scmp.com",                "rss_url": "https://www.scmp.com/rss/91/feed",                                     "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "China Daily",              "url": "https://www.chinadaily.com.cn",       "rss_url": "https://www.chinadaily.com.cn/rss/china_rss.xml",                     "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "People's Daily",           "url": "http://en.people.cn",                 "rss_url": "http://en.people.cn/rss/90786.xml",                                    "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "CGTN News",                "url": "https://news.cgtn.com",               "rss_url": "https://news.cgtn.com/rss/news.rss",                                   "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "China Military Online",    "url": "http://eng.chinamil.com.cn",          "rss_url": "http://eng.chinamil.com.cn/rss.xml",                                   "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "CCTV English",             "url": "https://english.cctv.com",            "rss_url": "https://english.cctv.com/rss/index.xml",                               "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "rss"},
    {"name": "Guancha News",             "url": "https://www.guancha.cn",              "rss_url": "https://www.guancha.cn/rss.xml",                                       "ring": RING_ADVERSARY, "country": "China",       "language": "zh", "source_type": "rss"},

    # =========================================================================
    # Ring 3 — Regional Neighbours (12 sources)
    # Neighbourhood developments across SAARC and South Asian borderlands
    # =========================================================================
    {"name": "Tolo News",                "url": "https://tolonews.com",                "rss_url": "https://tolonews.com/rss.xml",                                         "ring": RING_REGIONAL,  "country": "Afghanistan", "language": "en", "source_type": "rss"},
    {"name": "Kathmandu Post",           "url": "https://kathmandupost.com",           "rss_url": "https://kathmandupost.com/rss",                                        "ring": RING_REGIONAL,  "country": "Nepal",       "language": "en", "source_type": "rss"},
    {"name": "Daily Star Bangladesh",    "url": "https://www.thedailystar.net",        "rss_url": "https://www.thedailystar.net/rss.xml",                                 "ring": RING_REGIONAL,  "country": "Bangladesh",  "language": "en", "source_type": "rss"},
    {"name": "Dhaka Tribune",            "url": "https://www.dhakatribune.com",        "rss_url": "https://www.dhakatribune.com/feed",                                    "ring": RING_REGIONAL,  "country": "Bangladesh",  "language": "en", "source_type": "rss"},
    {"name": "Colombo Gazette",          "url": "https://colombogazette.com",          "rss_url": "https://colombogazette.com/feed/",                                     "ring": RING_REGIONAL,  "country": "Sri Lanka",   "language": "en", "source_type": "rss"},
    {"name": "Daily FT Sri Lanka",       "url": "https://www.ft.lk",                   "rss_url": "https://www.ft.lk/rss",                                                "ring": RING_REGIONAL,  "country": "Sri Lanka",   "language": "en", "source_type": "rss"},
    {"name": "Kuensel Bhutan",           "url": "https://kuenselonline.com",           "rss_url": "https://kuenselonline.com/feed/",                                      "ring": RING_REGIONAL,  "country": "Bhutan",      "language": "en", "source_type": "rss"},
    {"name": "The Irrawaddy Myanmar",    "url": "https://www.irrawaddy.com",           "rss_url": "https://www.irrawaddy.com/feed",                                       "ring": RING_REGIONAL,  "country": "Myanmar",     "language": "en", "source_type": "rss"},
    {"name": "The Edition Maldives",     "url": "https://edition.mv",                  "rss_url": "https://edition.mv/rss",                                               "ring": RING_REGIONAL,  "country": "Maldives",    "language": "en", "source_type": "rss"},
    {"name": "Kabul Times",              "url": "https://thekabultimes.com",           "rss_url": "https://thekabultimes.com/feed/",                                      "ring": RING_REGIONAL,  "country": "Afghanistan", "language": "en", "source_type": "rss"},
    {"name": "The Himalayan Times",      "url": "https://thehimalayantimes.com",       "rss_url": "https://thehimalayantimes.com/feed",                                   "ring": RING_REGIONAL,  "country": "Nepal",       "language": "en", "source_type": "rss"},
    {"name": "Sun Online Maldives",      "url": "https://en.sun.mv",                   "rss_url": "https://en.sun.mv/rss",                                                "ring": RING_REGIONAL,  "country": "Maldives",    "language": "en", "source_type": "rss"},

    # =========================================================================
    # Ring 4 — Global & Strategic (25 sources)
    # Neutral corroboration, global news wires, and strategic defence journals
    # =========================================================================
    {"name": "Reuters",                  "url": "https://www.reuters.com",             "rss_url": "https://feeds.reuters.com/reuters/INtopNews",                          "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "BBC Asia",                 "url": "https://www.bbc.com",                 "rss_url": "https://feeds.bbci.co.uk/news/world/asia/rss.xml",                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Al Jazeera",               "url": "https://www.aljazeera.com",           "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",                            "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Defense News",             "url": "https://www.defensenews.com",         "rss_url": "https://www.defensenews.com/arc/outboundfeeds/rss/",                   "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Defense One",              "url": "https://www.defenseone.com",          "rss_url": "https://www.defenseone.com/rss/all/",                                  "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Breaking Defense",         "url": "https://breakingdefense.com",         "rss_url": "https://breakingdefense.com/feed/",                                    "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Naval News",               "url": "https://www.navalnews.com",           "rss_url": "https://www.navalnews.com/feed/",                                      "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Air Force Technology",     "url": "https://www.airforce-technology.com", "rss_url": "https://www.airforce-technology.com/feed/",                              "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "RUSI Commentary",          "url": "https://www.rusi.org",                "rss_url": "https://www.rusi.org/rss/all.xml",                                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Janes Defence",            "url": "https://www.janes.com",               "rss_url": "https://www.janes.com/defence-news/rss",                               "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "CSIS Strategic Watch",     "url": "https://www.csis.org",                "rss_url": "https://www.csis.org/rss.xml",                                         "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "USNI News Naval",          "url": "https://news.usni.org",               "rss_url": "https://news.usni.org/feed",                                           "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "The Diplomat Asia",        "url": "https://thediplomat.com",             "rss_url": "https://thediplomat.com/feed/",                                        "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "War on the Rocks",         "url": "https://warontherocks.com",           "rss_url": "https://warontherocks.com/feed/",                                      "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "RAND National Security",   "url": "https://www.rand.org",                "rss_url": "https://www.rand.org/news.xml",                                        "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "The Defense Post",         "url": "https://www.thedefensepost.com",      "rss_url": "https://www.thedefensepost.com/feed/",                                 "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Shephard Media",           "url": "https://www.shephardmedia.com",       "rss_url": "https://www.shephardmedia.com/rss/news/",                              "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Eurasian Times",           "url": "https://www.eurasiantimes.com",       "rss_url": "https://www.eurasiantimes.com/feed/",                                  "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "IISS Strategic Dossier",   "url": "https://www.iiss.org",                "rss_url": "https://www.iiss.org/rss/all",                                         "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "SIPRI Arms & Conflict",    "url": "https://www.sipri.org",               "rss_url": "https://www.sipri.org/rss.xml",                                        "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Army Technology",          "url": "https://www.army-technology.com",     "rss_url": "https://www.army-technology.com/feed/",                                "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Naval Technology",         "url": "https://www.naval-technology.com",    "rss_url": "https://www.naval-technology.com/feed/",                               "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Defense Industry Daily",   "url": "https://www.defenseindustrydaily.com","rss_url": "https://www.defenseindustrydaily.com/feed/",                           "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "National Defense Mag",     "url": "https://www.nationaldefensemagazine.org", "rss_url": "https://www.nationaldefensemagazine.org/rss",                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},
    {"name": "Overt Defense",            "url": "https://www.overtdefense.com",        "rss_url": "https://www.overtdefense.com/feed/",                                   "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "rss"},

    # =========================================================================
    # Structured Intel APIs (6 sources)
    # Global conflict events, satellite thermal watch, humanitarian reports
    # =========================================================================
    {"name": "GDELT Global Events",      "url": "https://www.gdeltproject.org",        "api_endpoint": "https://api.gdeltproject.org/api/v2/doc/doc",                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "api"},
    {"name": "NASA FIRMS Satellite Thermal", "url": "https://firms.modaps.eosdis.nasa.gov", "api_endpoint": "https://firms.modaps.eosdis.nasa.gov/api",                   "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "satellite"},
    {"name": "ACLED South Asia Conflict Watch", "url": "https://acleddata.com",        "api_endpoint": "https://api.acleddata.com/acled/read",                             "ring": RING_GLOBAL,    "country": "Regional",    "language": "en", "source_type": "api"},
    {"name": "ReliefWeb Humanitarian",   "url": "https://reliefweb.int",               "api_endpoint": "https://api.reliefweb.int/v1/reports",                            "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "api"},
    {"name": "UN OCHA Incident Feed",    "url": "https://www.unocha.org",              "api_endpoint": "https://reports.unocha.org/api/v1",                                "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "api"},
    {"name": "SIPRI Military Transfers", "url": "https://www.sipri.org/databases/armstransfers", "api_endpoint": "https://api.sipri.org/transfers",                      "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "api"},

    # =========================================================================
    # Social / Public Telegram Channels (10 sources)
    # Open real-time OSINT defense intelligence channels
    # =========================================================================
    {"name": "Indian Defence Updates",   "url": "https://t.me/s/indiandefenceupdates", "channel": "indiandefenceupdates",                                                  "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "telegram"},
    {"name": "Northern Command OSINT",   "url": "https://t.me/s/northernfrontosint",   "channel": "northernfrontosint",                                                    "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "telegram"},
    {"name": "Indian Military Review TG","url": "https://t.me/s/indianmilitaryreview", "channel": "indianmilitaryreview",                                                 "ring": RING_INDIA,     "country": "India",       "language": "en", "source_type": "telegram"},
    {"name": "PLA Watcher Channel",     "url": "https://t.me/s/plawatcher",           "channel": "plawatcher",                                                            "ring": RING_ADVERSARY, "country": "China",       "language": "en", "source_type": "telegram"},
    {"name": "Pak Strategic Watch",     "url": "https://t.me/s/pakstrategic",         "channel": "pakstrategic",                                                          "ring": RING_ADVERSARY, "country": "Pakistan",    "language": "en", "source_type": "telegram"},
    {"name": "South Asia Conflict Monitor","url": "https://t.me/s/southasiaconflict",  "channel": "southasiaconflict",                                                     "ring": RING_REGIONAL,  "country": "Regional",    "language": "en", "source_type": "telegram"},
    {"name": "Tibet Borders OSINT",      "url": "https://t.me/s/tibetborderwatch",     "channel": "tibetborderwatch",                                                      "ring": RING_REGIONAL,  "country": "Regional",    "language": "en", "source_type": "telegram"},
    {"name": "Global Defence OSINT Feed","url": "https://t.me/s/globaldefenceosint",   "channel": "globaldefenceosint",                                                    "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "telegram"},
    {"name": "Naval Warfare Intel",     "url": "https://t.me/s/navalwarfareintel",    "channel": "navalwarfareintel",                                                     "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "telegram"},
    {"name": "Air Combat OSINT",         "url": "https://t.me/s/aircombatreview",      "channel": "aircombatreview",                                                       "ring": RING_GLOBAL,    "country": "Global",      "language": "en", "source_type": "telegram"},
]
