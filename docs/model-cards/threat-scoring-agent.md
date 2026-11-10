# Model Card: Regional Threat Scoring Agent (`threat_scoring_agent`)

**Version:** 0.2.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** November 2026  
**Stage:** 2 (Mid)

---

## 1. Overview & Purpose

The **Regional Threat Scoring Agent** continuously monitors and computes threat scores on a 1.0 to 10.0 scale with trend trajectory (`rising`, `stable`, `falling`) across all 9 Indian strategic defence sectors:
- `LAC-Ladakh`, `LAC-Arunachal`, `LoC-Kashmir`, `Western-Border`, `Indian-Ocean`, `Northeast`, `Internal-Security`, `Cyber`, `Global-Strategic`.

---

## 2. Algorithm & Methodology

The score is a composite index integrating:
1. **Article Threat Levels:** Base threat level extracted or classified per article.
2. **Geopolitical Ring Weights:** Ring 2 (adversary media e.g. Dawn, Global Times, Xinhua) carries a 1.25x weighting factor.
3. **Volume Surge Factor:** $\min(2.5, \log_{10}(N + 1) \times 1.5)$, penalizing abnormal density of reporting.
4. **Event Severity & Sentiment:** Escalation bonus for critical event types (`nuclear`, `border_incident`, `terror_activity`) and alarming sentiment.
5. **Trend Direction:** Compares the rolling window score against the previous cycle ($\Delta \ge 0.4 \implies \text{rising}$, $\Delta \le -0.4 \implies \text{falling}$, otherwise $\text{stable}$).

---

## 3. Explainability & Provenance

Every regional score emitted stores:
- `method`: `weighted_regional_threat_v2`
- `model_version`: `threat_scoring_agent:0.2.0`
- `article_count`: Number of articles contributing to the assessment.
- `top_events`: Leading event types driving the score.
