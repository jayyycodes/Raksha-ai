# Model Card & Architecture: Entity Resolution & Feedback (`resolution_agent`)

**Version:** 0.2.0
**Owner:** Ary
**Role:** Floor 2 — Language & Knowledge Agents
**Date:** November 2026
**Stage:** 3 (Production Implementation & Benchmark Calibration)

---

## 1. Component Overview

The **Entity Resolution Agent** resolves extracted mentions from OSINT articles and analyst document uploads against an authoritative canonical defense ontology (`CANONICAL_DEFENSE_ENTITIES`).

It differentiates:
- **Strong Matches (`auto_link`)**: High-confidence canonical linkage without human intervention.
- **Ambiguous Matches (`review_queue`)**: Routed to human analysts for verification.
- **Unlinked Entities (`separate`)**: Kept as distinct operational entities.

---

## 2. Decision Pipeline & Priority Flow

Every mention passes sequentially through five defensive filters:

```
Mention + Context + Workspace_ID + Type_Hint
                │
                ▼
1. Safety Guards & Immunity
   ├── Common English word guard ("west", "strike", "forces" -> separate)
   ├── Ambiguous single-token surname guard ("Singh", "Khan" -> separate/review)
   └── Conflicting rank guard ("General Singh" vs "Colonel Singh" -> review_queue)
                │
                ▼
2. Positive Feedback Overlay (ResolutionFeedbackStore)
   ├── Matches accepted feedback alias in caller's workspace
   ├── Validates target against canonical defense registry
   ├── Validates entity type compatibility
   └── Checks absence of negative dispute -> auto_link (ANALYST_VERIFIED)
                │
                ▼
3. Authoritative Defense Alias & Transliteration Match
   ├── Normalized case/punctuation lookup -> auto_link (0.98)
   └── Vetted Romanized Indic transliteration fold -> auto_link (0.92 - 0.96)
                │
                ▼
4. Negative Feedback Constraints
   └── Blocked by analyst rejection in workspace -> separate (DISPUTED, 0.40)
                │
                ▼
5. Fuzzy String Matching with Dense Contextual Embedding
   ├── Best sequence similarity against canonical aliases
   ├── Context cosine bonus (+0.08 if >= 0.70) or penalty (-0.15 if < 0.35)
   ├── Adjusted score >= auto_link_threshold (0.88) -> auto_link
   ├── Adjusted score >= review_queue_threshold (0.65) -> review_queue
   └── Adjusted score < review_queue_threshold -> separate
```

---

## 3. Scoped Workspace Isolation

Human-review feedback decisions are strictly partitioned by `workspace_id`:
- A feedback record accepted or rejected in `workspace_id=101` has **zero effect** on queries evaluated in `workspace_id=102` or default workspaces.
- Document text cannot tamper with workspace context; caller-supplied workspace metadata is strictly enforced.
- Unattributed feedback records operate strictly within their assigned workspace.

---

## 4. Confidence-Score Interpretation

> [!CAUTION]
> **Heuristic Scores, Not Probabilities**: Confidence values (e.g. `0.98`, `0.92`, `0.65`, `0.40`) are **heuristic ordinal scores** designed for deterministic routing thresholds. They must **not** be interpreted as calibrated Bayesian probabilities. A confidence of 0.98 signifies an exact alias match in the static defense ontology or an accepted analyst decision, not a 98% likelihood under a statistical model.

---

## 5. Benchmark Evaluation & Retained Policy Threshold

Evaluated against `evaluation/data/resolution_feedback_eval.jsonl` ($N=30$ safety and edge-case pairs):

> [!IMPORTANT]
> **Dataset Status & Calibration Boundary**:
> - All 30 records carry `annotation_status: "curated_unverified"`.
> - **Sample Size Limitation**: $N=30$ curated_unverified examples are **statistically insufficient for empirical probability calibration**.
> - **Threshold Nature**: The value `0.88` is a **conservative retained policy threshold** originally established in Stage 2 as an operational fail-safe, not a statistically calibrated or Bayesian probability parameter.

### 5.1 Measured Performance Summary (at Retained Policy Threshold 0.88)

| Metric | Target | Measured Result | Operational Meaning |
|---|---|---|---|
| **Auto-Merge Precision** | $\ge 95.0\%$ | **100.00%** (6/6) | True auto-merges / total auto-links ($\text{TP} / (\text{TP} + \text{FP})$) |
| **Auto-Merge Recall** | $\ge 60.0\%$ | **66.67%** (6/9) | High safety on ambiguous matches (3 true pairs held in review) |
| **Distinct Entity Precision** | $\ge 75.0\%$ | **77.78%** (14/18) | Correct separations / total separations |
| **Distinct Entity Recall** | $\ge 80.0\%$ | **82.35%** (14/17) | Correct separations / total true distinct entities |
| **False Auto-Merges** | $0$ | **0** | **Passed** (0 non-matches auto-linked across all 30 pairs) |
| **Review-Required Auto-Linked** | $0$ | **0** | **Passed** (Ambiguous pairs never auto-merged) |
| **No-False-Auto-Merge Rate** | $100.0\%$ | **100.00%** (30/30) | Non-false-merge rate: zero corrupting auto-links |
| **Analyst Review Rate** | Expected | **20.00%** (6/30) | Proportion of pairs safely routed to human review |

> [!NOTE]
> **Safety Rate vs Classification Accuracy**:
> The `No-False-Auto-Merge Rate` of 100.00% (30/30) measures the critical absence of false automatic merges (i.e. zero unverified graph corruptions). It does **not** assert 100% 3-class classification accuracy: 3 true matches with minor syntactic divergence were held in `review_queue`, and 3 distinct entities were routed to `review_queue` as fail-closed actions. Exact 3-class classification accuracy is **80.00%** (24/30).

### 5.2 Threshold Sensitivity Sweep

| `auto_link_threshold` | Auto-Link Precision | Auto-Link Recall | Review Rate | False Merges | Distinct Recall |
|---|---|---|---|---|---|
| `0.75` | 100.0% | 77.78% | 13.33% | 0 | 88.24% |
| `0.80` | 100.0% | 77.78% | 13.33% | 0 | 88.24% |
| `0.85` | 100.0% | 66.67% | 16.67% | 0 | 88.24% |
| **`0.88` (Retained Policy)** | **100.0%** | **66.67%** | **20.00%** | **0** | **82.35%** |
| `0.90` | 100.0% | 66.67% | 20.00% | 0 | 82.35% |
| `0.95` | 100.0% | 66.67% | 20.00% | 0 | 82.35% |

**Retained Policy Justification:**
The sole difference between thresholds $\tau \in [0.75, 0.80]$ and $\tau \ge 0.85$ across the 30-sample benchmark isolates to a single item (`rf_eval_014`, `"Ravalpindi GHQ"` vs `"Rawalpindi"`, string similarity $0.8333$). Retaining the pre-existing conservative policy threshold of `0.88` avoids overfitting to this single sample, ensuring multi-token organization modifiers (such as distinct command headquarters or program sub-variants) in the range $[0.80, 0.87]$ route safely to analyst review (`REVIEW_NEEDED`) rather than creating unverified automatic graph links.

---

## 6. Known Limitations & Production Integration Status

1. **In-Memory Store Architecture**:
   The current `ResolutionFeedbackStore` resides in-memory per agent instance. Database persistence (PostgreSQL tables `resolution_feedback` / migration scripts) is an infrastructure concern owned by Floor 1 (Jay). Floor 2 maintains the schema and ingestion contracts ready for persistence binding.
2. **Provenance Provenance Tracking**:
   Reused decision IDs with conflicting attributes (analyst, entity type, notes) raise immediate `ValueError` exceptions to protect provenance audit integrity.
3. **Equal-Timestamp Conflict Semantics**:
   When two conflicting analyst feedback decisions share the exact same UTC timestamp, the system fails closed to `review_queue` / `separate` and refuses to auto-link.
