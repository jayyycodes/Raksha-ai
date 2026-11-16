# Disinformation Scoring Agent v1 (Milestone M9)

**Owner:** Jaish (Data Expansion, Intelligence & Grounding)  
**Stage:** 3 (Solid)  
**Version:** 1.0.0  

---

## 1. Overview & Purpose
Quantifies information warfare, narrative friction, and disinformation risks across multi-source reporting clusters. Evaluates cross-ring alignment by pitting adversary claims against domestic and neutral global reporting:
- Contradiction-to-corroboration ratios across reporting pairs.
- Adversary narrative isolation (Ring 2 making claims unsupported by Rings 1 and 4).
- Neutral global validation rate (Ring 4 corroboration).

---

## 2. Risk Levels & Scoring Formula
The score $S \in [0.0, 1.0]$ is computed as:
$$S = (0.45 \times R_{\text{contradiction}}) + (0.40 \times I_{\text{adversary\_isolated}}) + (0.15 \times (1 - R_{\text{neutral\_corroboration}}))$$

| Score Range | Risk Level | Description |
|---|---|---|
| $0.00 - 0.29$ | **LOW** | Factual consistency across domestic, regional, and global wires. |
| $0.30 - 0.49$ | **MEDIUM** | Moderate variance in casualty numbers or tactical framing. |
| $0.50 - 0.74$ | **HIGH** | Sharp denial-vs-assertion disputes across counter-party sources. |
| $0.75 - 1.00$ | **CRITICAL** | Heavy weaponized denial surge from adversary outlets without neutral validation. |

---

## 3. Endpoints & Schemas
- `GET /api/articles/{article_id}/disinformation`
- Schema: `DisinformationScoreOut` (score, risk level, primary reason, component metrics, ring breakdown, flagged contradictions).
