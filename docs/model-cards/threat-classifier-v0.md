# Model Card: Threat Classifier v0 (`threat_classifier_v0`)

**Version:** 0.1.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** October 2026  
**Stage:** 1 (MVP)

---

## 1. Model Overview

The **Threat Classifier v0** is an explainable, deterministic threat evaluation agent tailored for defence news intelligence. It maps raw articles to a threat category (`LOW`, `MEDIUM`, `HIGH`) and a corresponding database threat level (1 to 10).

The assessment is computed from three transparent signals:
1. **Event Type Base Risk:** Inherent severity derived from classified event types (e.g. `nuclear` = 9.0, `terror_activity` = 8.0, `border_incident` = 7.5, down to `general` = 2.5).
2. **Domain Keywords:** High-risk indicators (`artillery`, `infiltration`, `firing`, `casualties`, `clash`, `nuclear`) and medium-risk indicators (`patrol`, `troop deployment`, `surveillance`, `procurement`).
3. **Source Ring Weighting:** Multiplier adjusting for geopolitical source origin (Adversary media Ring 2 multiplier = 1.15, Regional Ring 3 = 1.05, Indian Ring 1 = 1.0).

---

## 2. Intended Use

- Immediate triaging of scraped or analyst-uploaded articles.
- Highlighting critical border and escalation signals for the Analyst Feed.
- Providing baseline threat scores for the regional threat index.

### Out-of-Scope Use
- Not intended for automated tactical battlefield decisions or offensive targeting.
- Not a substitute for human intelligence verification.

---

## 3. Benchmark Metrics (Stage 1 MVP)

Tested on the hand-labelled dataset `evaluation/data/threat_level_eval.jsonl` (15 defence articles across all rings):

| Metric | Target | Achieved | Status |
|---|---|---|---|
| **Overall Accuracy** | >= 70.0% | **73.33%** | Passed |
| **High Threat Precision** | - | **83.33%** | High precision on critical alerts |
| **High Threat Recall** | - | **83.33%** | Low false negative rate |
| **Macro Precision** | - | **80.16%** | - |
| **Macro F1 Score** | - | **0.7222** | - |

---

## 4. Explainability & Provenance

Every classification output emits a full `Provenance` payload:
- `method`: `rule_keyword_event_v0`
- `model_version`: `threat_classifier_v0:0.1.0`
- `confidence`: 0.70 – 0.85
- `reasoning`: Detailed breakdown of triggered event types, detected keywords, and ring multiplier.
- `claim_status`: `reported`

---

## 5. Limitations & Next Steps (Stage 2)

- **v0 Baseline:** Relies on lexical keyword and event-type lookups; does not resolve complex sarcasm or negation (e.g. "rumours of clash were denied").
- **Stage 2 Transition:** In Stage 2, Jaish will introduce regional rolling 30-day baselines, anomaly detection, and transformer/LLM-assisted threat escalation scoring.
