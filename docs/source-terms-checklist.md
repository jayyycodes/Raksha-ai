# Raksha AI — Source Terms & Robots Compliance Checklist

This document details the compliance, terms of service, and scraping policies for the 15 initial sources monitored in Stage 1 (MVP).

## 1. Compliance Principles
1. **Public Syndication Feeds Only**: Scrapes standard publicly published RSS/Atom XML feeds and authorized API endpoints.
2. **Copyright-Safe Storage**: Raksha AI never stores or republishes full article text. Only headline, URL, canonical publication timestamp, and a short summary excerpt (<=500 characters) are stored.
3. **Polite Crawling & Rate Limiting**: Feeds are polled at intervals no more frequent than once every 4 hours (`SCRAPE_INTERVAL_HOURS=4`).
4. **Standard User-Agent**: HTTP requests identify as `RakshaAI-OSINT/1.0 (+https://github.com/jayyycodes/raksha-ai)`.

---

## 2. Source Checklist (15 Initial MVP Sources)

| # | Source Name | Ring | Feed Type | Robots.txt & Feed Path | Polling Interval | Compliance Approach |
|---|---|---|---|---|---|---|
| 1 | **The Hindu** | 1 (India) | RSS | `https://www.thehindu.com/news/national/feeder/default.rss` | 4 hours | Public RSS feed; title + link attribution only. |
| 2 | **ANI News** | 1 (India) | RSS | `https://www.aninews.in/rss/india.xml` | 4 hours | Standard syndication feed; snippet excerpting. |
| 3 | **The Print** | 1 (India) | RSS | `https://theprint.in/feed/` | 4 hours | Standard WordPress public RSS; non-commercial research use. |
| 4 | **PIB India** | 1 (India) | RSS | `https://pib.gov.in/RssMain.aspx` | 4 hours | Official Government of India press releases (Open Public Data). |
| 5 | **Dawn Pakistan** | 2 (Adversary) | RSS | `https://www.dawn.com/feed` | 4 hours | Public syndication channel; no deep-scraping beyond XML description. |
| 6 | **Geo News** | 2 (Adversary) | RSS | `https://www.geo.tv/rss/1` | 4 hours | Syndicated RSS headlines. |
| 7 | **Global Times** | 2 (Adversary) | RSS | `https://www.globaltimes.cn/rss/outbrain.xml` | 4 hours | Public English-language syndication feed. |
| 8 | **Xinhua** | 2 (Adversary) | RSS | `http://www.xinhuanet.com/english/rss/chinalatestnews.xml` | 4 hours | Public official RSS service. |
| 9 | **SCMP** | 2 (Adversary) | RSS | `https://www.scmp.com/rss/91/feed` | 4 hours | Public RSS feed; respects paywall boundaries (snippet only). |
| 10 | **Tolo News** | 3 (Regional) | RSS | `https://tolonews.com/rss.xml` | 4 hours | Standard regional news syndicate. |
| 11 | **Kathmandu Post** | 3 (Regional) | RSS | `https://kathmandupost.com/rss` | 4 hours | Public editorial RSS feed. |
| 12 | **Reuters** | 4 (Global) | RSS | `https://feeds.reuters.com/reuters/INtopNews` | 4 hours | Global wire RSS headline feed. |
| 13 | **BBC Asia** | 4 (Global) | RSS | `http://feeds.bbci.co.uk/news/world/asia/rss.xml` | 4 hours | BBC public news syndicate. |
| 14 | **Al Jazeera** | 4 (Global) | RSS | `https://www.aljazeera.com/xml/rss/all.xml` | 4 hours | Public English-language feed. |
| 15 | **Defense News** | 4 (Global) | RSS | `https://www.defensenews.com/arc/outboundfeeds/rss/` | 4 hours | Defense-specific industry RSS. |

---

## 3. NewsAPI Compliance
- **Authentication**: Access via authorized API key (`NEWS_API_KEY`).
- **Endpoint**: Developer tier `https://newsapi.org/v2/everything`.
- **Query Filter**: Restrict to defense keywords and India security topics.
- **Data Policy**: NewsAPI developer terms allow headline and metadata display with direct canonical referral links.

