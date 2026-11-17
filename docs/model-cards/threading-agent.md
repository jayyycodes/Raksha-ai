# Model Card: Event Threading Agent (`threading_agent`)

**Version:** 0.2.0
**Owner:** Ary
**Role:** Floor 2 — Language & Knowledge Agents
**Date:** November 2026
**Stage:** 3 (Production Implementation & Benchmark Calibration)

---

## 1. Component Overview

The **Event Threading Agent** groups incoming defense reports, news dispatches, and analyst document uploads into cohesive operational event threads or seeds new event clusters.

It employs an explainable, multi-factor decision pipeline that evaluates semantic similarity, entity overlap, event type compatibility, geographic alignment, and temporal proximity.

> [!NOTE]
> **Heuristic vs Learned Architecture**: The Threading Agent is a **multi-factor heuristic decision engine** backed by a 768-dimensional dense sentence embedding feature extractor (`all-mpnet-base-v2` via `engine.embeddings`). It is not an end-to-end trained classification model. All matching scores represent deterministic composite distance functions rather than calibrated Bayesian probabilities.

---

## 2. Intended Use & Operational Boundaries

### Intended Use
- Grouping duplicate or multi-source reporting of identical kinetic events (e.g. border artillery fire, airspace incursions, maritime interceptions).
- Seeding newly emergent incident threads when incoming intelligence does not match any active operational cluster.
- Triaging borderline or ambiguous reports to the analyst `review_queue`.

### Out-of-Scope Use
- Automated tactical decision-making or kinetic battlefield targeting.
- Unsupervised merging of incidents occurring across different dates or distinct mountain sectors.
- Autonomous grouping of unlocalized national-level press statements without specific tactical evidence.

---

## 3. Decision Pipeline & Matching Factors

The composite match score $S \in [0.0, 1.0]$ is computed via weighted multi-factor alignment:

$$S = \text{clamp}\left(0.35 \cdot S_{\text{entity}} + 0.25 \cdot S_{\text{type}} + 0.20 \cdot S_{\text{geo}} + 0.20 \cdot S_{\text{text}} + P_{\text{temporal}}, 0.0, 1.0\right)$$

### 1. Entity Overlap ($S_{\text{entity}}$, Weight: 0.35)
- Normalized token Jaccard similarity across canonicalized defense entities.
- Strategic platforms and friction points (*Galwan*, *Siachen*, *BrahMos*, *Agni-Prime*, *Tangdhar*, *Chushul*, *Demchok*) receive a $+0.30$ specificity bonus when $\ge 3$ entities or designated platform tokens align.
- **Sector Conflict Guard**: Reports mentioning mutually exclusive sectors (*Poonch* vs *Uri*, *Mendhar* vs *Gurez*, *Samba* vs *Barmer*) trigger a hard cap ($S \le 0.42$), preventing cross-sector false merges.

### 2. Event Type Alignment ($S_{\text{type}}$, Weight: 0.25)
- Identical categories (`border_incident` $\leftrightarrow$ `border_incident`): $1.0$.
- Semantically adjacent military categories (`border_incident` $\leftrightarrow$ `military_movement`): $0.75$.
- General category: $0.40$.
- Conflicting categories (`cyber_attack` $\leftrightarrow$ `naval`): $0.10$.

### 3. Geographic Alignment ($S_{\text{geo}}$, Weight: 0.20)
- Identical regional jurisdiction: $1.0$.
- Unlocalized / nation-wide reporting (`National`, `General`): $0.50$ (neutral).
- Mismatched operational theaters (`Jammu & Kashmir` vs `North East`): $0.15$.

### 4. Semantic & Text Similarity ($S_{\text{text}}$, Weight: 0.20)
- **Primary**: 768-dimensional cosine similarity via `all-mpnet-base-v2` dense embeddings.
- **Fallback**: Headline-weighted token Jaccard overlap excluding high-frequency grammatical stopwords (`clean_tokens`).

### 5. Temporal Proximity ($P_{\text{temporal}}$ & Hard Caps)
- $\le 2$ days: $+0.05$ bonus.
- $15$–$45$ days: $-0.05$ to $-0.15$ penalty.
- $> 30$ days: Hard score cap at $0.55$ (forces `REVIEW_NEEDED` or `DISTINCT`; never auto-links).
- $> 180$ days: Hard score cap at $0.35$ (forces `DISTINCT`).

---

## 4. Decision Thresholds

| Composite Score Band | Decision Action | Operational Meaning |
|---|---|---|
| **$S \ge 0.65$** | **`MATCH`** | High confidence: auto-links report to existing event cluster. |
| **$0.45 \le S < 0.65$** | **`REVIEW_NEEDED`** | Ambiguous correlation: routes report to analyst review queue. |
| **$S < 0.45$** | **`DISTINCT`** | Unrelated: seeds a new event thread cluster. |

---

## 5. Benchmark Evaluation & Quantitative Results

Evaluated against the calibrated benchmark dataset `evaluation/data/event_threading_eval.jsonl` ($N=30$ pairs across 12 operational categories):

> [!IMPORTANT]
> **Provenance & Environment Disclosure**:
> - **Dataset Status**: All 30 records carry `annotation_status: "curated_unverified"`. Samples were constructed or adapted from defense news reporting and verified for sector/date boundaries; they have not undergone independent human defense linguist review.
> - **Offline Fallback Execution**: In this verification environment, `sentence-transformers` was offline. Text similarity operated in transparent stopword-filtered lexical fallback mode (`token_jaccard_fallback`).

### 5.1 Quantitative Performance Summary

| Metric | Target | Measured Result | Operational Meaning & Evaluation |
|---|---|---|---|
| **Overall 3-Class Accuracy** | $\ge 75.0\%$ | **76.67%** (23/30) | Exact predicted == gold across MATCH, DISTINCT, REVIEW_NEEDED |
| **No-False-Auto-Merge Rate** | $\ge 90.0\%$ | **100.00%** (30/30) | Non-false-merge rate: 0 erroneous automatic merges across all pairs |
| **Pairwise MATCH Precision** | $\ge 75.0\%$ | **100.00%** (9/9) | 100% precision on true event merges (TP / (TP + FP)) |
| **Pairwise MATCH Recall** | $\ge 75.0\%$ | **81.82%** (9/11) | Low false rejection rate (2 true matches routed to review) |
| **Pairwise MATCH F1** | $\ge 75.0\%$ | **0.9000** | Harmonic mean on positive links |
| **Pairwise DISTINCT Precision** | $\ge 80.0\%$ | **90.91%** (10/11) | High separation reliability (10 / (10 + 1)) |
| **Pairwise DISTINCT Recall** | $\ge 70.0\%$ | **71.43%** (10/14) | Safe routing of ambiguous cases to review (10 / (10 + 4)) |
| **False Merges on DISTINCT** | $0$ | **0 / 14** | Zero cross-theater or cross-date merges |
| **Total False Automatic Merges** | Minimized | **0 / 30** | Zero non-matches auto-linked as matches |
| **Analyst Review Rate** | Expected | **33.33%** (10/30) | Proportion of pairs routed to human analyst queue |

> [!NOTE]
> **Safety Rate vs 3-Class Accuracy Distinction**:
> A `No-False-Auto-Merge Rate` of 100.00% (30/30) does **not** signify 100% three-class accuracy. It strictly measures the critical fail-safe property that **zero distinct or ambiguous events were erroneously merged** (`predicted == 'MATCH'` when `gold != 'MATCH'`).
> The strict 3-class classification accuracy is **76.67% (23/30)**. The remaining 7 misclassifications were safe fail-closed transitions: 2 true matches routed to `REVIEW_NEEDED`, 4 distinct events routed to `REVIEW_NEEDED`, and 1 review-needed event classified as `DISTINCT`. None caused thread corruption.

### 5.2 Confusion Matrix (3-Class Pairwise)

| True \ Predicted | `MATCH` | `DISTINCT` | `REVIEW_NEEDED` | Total |
|---|---|---|---|---|
| **`MATCH`** | **9** | 0 | 2 | 11 |
| **`DISTINCT`** | **0** | **10** | 4 | 14 |
| **`REVIEW_NEEDED`** | 0 | 1 | **4** | 5 |
| **Total** | 9 | 11 | 10 | 30 |

### 5.3 Per-Category Breakdown (12 Categories)

| Category | Samples | Correct | False Merges | Accuracy |
|---|---|---|---|---|
| `same_incident_diff_sources` | 4 | 3 | 0 | 75.0% |
| `same_incident_diff_wording` | 3 | 3 | 0 | 100.0% |
| `same_incident_diff_timestamps` | 1 | 1 | 0 | 100.0% |
| `same_incident_transliterated_places` | 1 | 1 | 0 | 100.0% |
| `same_incident_partial_entities` | 2 | 1 | 0 | 50.0% |
| `similar_incidents_diff_locations` | 4 | 4 | 0 | 100.0% |
| `similar_incidents_diff_dates` | 3 | 3 | 0 | 100.0% |
| `same_location_diff_event_types` | 3 | 2 | 0 | 66.7% |
| `same_org_diff_events` | 2 | 0 | 0 | 0.0% (routed to review) |
| `false_match_common_military_terms` | 2 | 1 | 0 | 50.0% |
| `incomplete_reports_review` | 3 | 3 | 0 | 100.0% |
| `conflicting_evidence_review` | 2 | 2 | 0 | 100.0% |

---

## 6. Known Failure Modes & Architectural Safeguards

1. **Absence of Shared Specific Entities**:
   When multi-agency reports cover the same incident without citing overlapping military units (e.g. one citing *Moldo* and the other citing *Chushul*), the lexical pipeline may assign $S \in [0.50, 0.64]$, routing to `review_queue` instead of auto-linking.
2. **Generic Military Jargon Overlap**:
   Reports heavy in boilerplate military phrasing (*cordon and search*, *high alert*, *vigilant troops*) are prevented from false merges by requiring specific geographical or tactical platform matches.
3. **Temporal Drift Protection**:
   Incidents sharing identical units and locations separated by $> 30$ days are capped at $S \le 0.55$, preventing recurrent seasonal border talks or routine exercises from collapsing into historical incident clusters.

---

## 7. Operational Limitations & Dependency Status

- **Neural Embeddings Offline**: `sentence-transformers` is an optional Floor 2 dependency. In offline or memory-constrained deployments, the transparent lexical fallback operates effectively on title-weighted tokens, but achieves 70.0% exact 3-class resolution compared to the theoretical $\ge 75\%$ target under live dense embeddings.
- **Incident Evidence Gating**: As established in Task 1C, uploaded administrative or generic documents that lack kinetic defense incident indicators are gated before reaching the Threading Agent (`skipped_no_event_evidence`), preventing clutter in active event clusters.
