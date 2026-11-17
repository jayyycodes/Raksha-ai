# Model Card: Multilingual Indic NLP (`indic_nlp_agent`)

**Version:** 0.2.0
**Owner:** Ary
**Role:** Floor 2 — Language & Knowledge Agents
**Date:** November 2026
**Stage:** 3 (Production Implementation & Benchmark Calibration)

---

## 1. Model Overview

The **Multilingual Indic NLP Agent** provides robust, defense-domain language processing for South Asian defense OSINT and analyst document uploads. It processes native-script dispatches (Devanagari, Perso-Arabic, Gurmukhi, Eastern Nagari) and Romanized Indic (Hinglish/Urdish) communications.

Rather than conflating Romanized or vernacular text under English passthrough, the pipeline decouples processing into four specialized stages:
1. **Script & Language Identification (`pipeline/upload_nlp.py`)**: Multi-script character block analysis with short-text fallbacks and mixed-language detection.
2. **Selective Machine Translation (`engine/translator.py` & `agents/translation/agent.py`)**: Helsinki-NLP MarianMT models with proper-noun preservation dictionaries for supported languages (`hi`, `ur`, `zh`), and guaranteed byte-level passthrough for unsupported vernaculars.
3. **Cross-Script Defense NER (`engine/ner.py`)**: Span-level entity extraction with exact Python character offsets, defense gazetteers, and structured military rank parsing.
4. **Contextual Entity Resolution & Transliteration (`agents/resolution/agent.py`)**: Vetted phonetic normalization, composite name connector standardization, conservative person disambiguation, and workspace-isolated human review feedback.

---

## 2. Intended Use & Operational Boundaries

### Intended Use
- Automated ingestion and entity extraction of vernacular South Asian open-source intelligence (PIB releases, ISPR briefings, vernacular defense reporting).
- Safe cross-script normalization of strategic locations (*Siachen / Syachen*, *Kupwara / Kupwada*, *Akhnoor / Akhnur*, *Rawalpindi / Ravalpindi*) and militant/terror organizations (*Jaish-e-Mohammed* variants).
- Structured extraction of military commanders and decorated personnel, preserving rank while guarding against uncorroborated merging.

### Out-of-Scope Use
- Automated targeting, tactical fire direction, or kinetic battlefield command decisions.
- Forensic dialect attribution or psychological profiling of authors.
- Unassisted automated merging of single-token surnames (*"General Singh"*, *"Brigadier Khan"*).

---

## 3. Supported Languages & Capability Matrix

| Language / Script | ISO 639-1 | Detection Support | Translation Engine | Entity Extraction | Transliteration / Romanization |
|---|---|---|---|---|---|
| **Hindi (Devanagari)** | `hi` | **Yes** ($\ge 99\%$) | **Yes** (`opus-mt-hi-en`) | **Yes** (Devanagari defense patterns) | Native Script to Canonical |
| **Urdu (Perso-Arabic)** | `ur` | **Yes** ($\ge 99\%$) | **Yes** (`opus-mt-ur-en`) | **Yes** (Perso-Arabic defense patterns)| Native Script to Canonical |
| **Chinese (Simplified)** | `zh` | **Yes** ($\ge 99\%$) | **Yes** (`opus-mt-zh-en`) | **Yes** (PLA/CMC patterns) | Standard Pinyin to Canonical |
| **Romanized Indic (Latin)**| `en` / `indic`| **Yes** (Latin script) | *Passthrough* (English text) | **Yes** (Hinglish/Urdish defense terms) | **Yes** (Vetted phonetic rules) |
| **Punjabi (Gurmukhi)** | `pa` | **Yes** ($\ge 99\%$) | *No Translation* (Preserved) | **Yes** (Gurmukhi frontier patterns) | Extraction & Resolution Only |
| **Bengali (Eastern Nagari)**| `bn` | **Yes** ($\ge 99\%$) | *No Translation* (Preserved) | **Yes** (Eastern Command patterns) | Extraction & Resolution Only |

> [!NOTE]
> Unsupported languages (`pa`, `bn`) pass through the ingestion pipeline with 100% text fidelity and an explicit warning recorded in `analysis.warnings`. The system never fabricates translation capabilities or treats foreign vernacular text as English.

---

## 4. Benchmark Evaluation & Quantitative Results

Evaluated on the calibrated regression dataset `evaluation/data/indic_nlp_eval.jsonl` ($N=36$ balanced samples across 5 linguistic categories):

> [!IMPORTANT]
> **Evaluation Scope & Provenance Notice**:
> - **Initial Regression Benchmark**: This 36-sample dataset serves as an initial regression benchmark to verify architectural contracts, exact character offsets, and resolution safety. It does not constitute proof of production-grade coverage across all regional dialects.
> - **Annotation Provenance (`curated_unverified`)**: All 36 samples carry `annotation_status: "curated_unverified"`. The dataset was synthetically constructed or adapted from open-source reporting and algorithmically verified for offset integrity; it has **not** undergone verified review by an independent human defense linguist.
> - **Offline Proper-Noun Evaluation**: The proper-noun preservation benchmark was evaluated using the rule-based token protection and restoration pipeline (`protect_indic_proper_nouns` / `restore_indic_proper_nouns` with fallback translation processing). Because Helsinki-NLP MarianMT weights (`opus-mt-hi-en`, `opus-mt-ur-en`) were unavailable locally during this audit, **this metric measures the fidelity of token masking and placeholder protection mechanisms, not real-world neural machine translation performance**.

### 4.1 Quantitative Performance Summary

| Metric | Target | Achieved | Operational Status |
|---|---|---|---|
| **Language Detection Accuracy** | $\ge 95.0\%$ | **100.00%** | Passed (36/36 correct, zero cross-script confusion) |
| **Span-Level Micro F1** | $\ge 90.0\%$ | **0.9429** | Passed (Prec: 0.9296, Rec: 0.9565; TP=66, FP=5, FN=3) |
| **Canonical Resolution F1** | $\ge 90.0\%$ | **0.9429** | Passed (Prec: 0.9296, Rec: 0.9565; TP=66, FP=5, FN=3) |
| **Proper-Noun Preservation Rate** | $\ge 95.0\%$ | **98.00%** | Passed (49/50 preserved via offline token masking pipeline; *not* live MarianMT) |
| **Transliteration Precision** | $\ge 95.0\%$ | **100.00%** | Passed (5/5 correct canonical targets, 0 false-positive merges)|
| **Transliteration Attempt Coverage**| $\ge 90.0\%$ | **100.00%** | Passed (5/5 phonetic variants triggered rules) |
| **False-Positive Merges** | $0$ | **0** | Passed (English words & ambiguous names guarded)|
| **Unsupported Passthrough Fidelity**| $100.0\%$ | **100.00%** | Passed (10/10 preserved verbatim, warnings logged) |

### 4.2 Per-Category Breakdown

| Linguistic Category | Sample Count | Lang Detect Acc | Span Precision | Span Recall | Span F1 |
|---|---|---|---|---|---|
| `hindi_native` | 8 | 100.0% | 1.000 | 1.000 | 1.000 |
| `urdu_native` | 8 | 100.0% | 1.000 | 0.929 | 0.963 |
| `romanized_indic` | 10 | 100.0% | 0.833 | 0.882 | 0.857 |
| `punjabi_native` | 5 | 100.0% | 1.000 | 1.000 | 1.000 |
| `bengali_native` | 5 | 100.0% | 0.846 | 1.000 | 0.917 |

---

## 5. Architectural Safeguards & Provenance

1. **Exact Python Unicode Offsets**:
   All entity annotations and extracted spans adhere strictly to Python Unicode indexing (`text[start_char:end_char] == entity_value`).
2. **Safe Military Rank & Person Normalization**:
   Mentions bearing ranks (*General*, *Lt Gen*, *Subedar Major*) are parsed into structured components. Ambiguous single-token surnames (*"General Singh"*) are never auto-merged; they route safely to `review_queue` (`REVIEW_NEEDED`).
3. **Common English Word Immunity**:
   High-frequency English vocabulary (*west*, *punch*, *wood*, *wing*, *forces*) cannot be mutated by transliteration or phonetic fold rules.
4. **Task 1B Workspace Isolation Preservation**:
   Custom feedback aliases and negative constraints remain strictly isolated within the caller's trusted `workspace_id`.

---

## 6. Known Limitations & Ongoing Work

- **Informal Social OSINT Dialects**: Informal Romanized Hindi/Urdu with extensive phonetic non-standard spelling or regional slang may have degraded extraction recall.
- **Offline Machine Translation Verification**: Live MarianMT model weights (`opus-mt-hi-en`, `opus-mt-ur-en`) were absent in the verification environment; real-world neural translation preservation must be re-evaluated under live inference once model weights are staged in production.
- **Low-Resource Machine Translation**: Expanding translation coverage to Punjabi (`pa`) and Bengali (`bn`) requires evaluating dedicated model weights (e.g. IndicTrans2) in coordination with shared dependency configurations.
