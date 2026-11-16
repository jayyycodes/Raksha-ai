# Connector Framework & 96+ Source Coverage (Milestone M7)

**Owner:** Jaish (Data Expansion, Intelligence & Grounding)  
**Stage:** 3 (Solid)  
**Version:** 1.0.0  

---

## 1. Overview & Purpose
The Raksha AI Connector Framework decouples source ingestion from the scheduler core, allowing new data sources to be integrated as single lightweight plug-in classes (`BaseConnector`). It scales coverage from the 40 core RSS feeds of Stage 2 to **96+ sources** spanning:
- **Ring 1 (India - 25 sources):** Domestic news, defense press releases, regional border outlets.
- **Ring 2 (Adversaries - 18 sources):** State and mainstream publications from Pakistan and China.
- **Ring 3 (Regional - 12 sources):** SAARC and South Asian neighborhood feeds (Nepal, Bangladesh, Sri Lanka, Myanmar, Maldives, Afghanistan, Bhutan).
- **Ring 4 (Global - 25 sources):** Global wires, specialized defense publications, think tanks (RUSI, CSIS, Janes, RAND, USNI).
- **Structured Intel APIs (6 sources):** GDELT 2.0 Doc API, NASA FIRMS Thermal Satellite Watch, ACLED South Asia Conflict Watch, ReliefWeb, UN OCHA, SIPRI.
- **Social / Telegram Channels (10 sources):** Public defense channels scraped via open web previews (`https://t.me/s/<channel>`) without credentials.

---

## 2. Architecture & Contracts
- **Base Interface (`connectors.base.BaseConnector`):**
  - `fetch_articles(since: Optional[datetime]) -> list[dict]`
  - `health_check() -> dict`
- **Plug-In Discovery (`connectors.registry.ConnectorRegistry`):**
  - Dynamically registers built-in APIs, RSS adapters, Telegram channels, and local 1-file modules in `connectors/sources/`.
- **Safe Scraping Bounds:**
  - Content length clamped to $\le 500$ chars (summaries) / $\le 5000$ chars (raw text).
  - SHA-256 URL hash deduplication.
  - Zero private credentials required for public Telegram feeds.
