# Component Specification: Evaluation Harness (`evaluation/`)

**Owner:** Jaish  
**Role:** AI/ML Intelligence & Evaluation  
**Date:** October 2026  
**Stage:** 1 (MVP)

---

## 1. Overview

The **Raksha AI Evaluation Harness** is a shared testing and benchmarking framework that ensures all agent deliverables across all floors satisfy minimum accuracy, precision, recall, and grounding criteria prior to integration into `dev` or `main`.

---

## 2. Capabilities

1. **Classification Benchmarking:** Multi-class precision, recall, and F1 calculations with per-class and macro averages without external dependencies.
2. **Grounding Rate Verification:** Calculates the proportion of statements in generated Situation Reports supported by cited sources to eliminate hallucinations.
3. **Automated Markdown Output:** Emits ready-to-paste GitHub Markdown tables for Pull Request documentation.
4. **Dataset Support:** JSON and JSONL datasets with extensible target key mappings.

---

## 3. Benchmark Datasets Provided in Stage 1

- `evaluation/data/threat_level_eval.jsonl`: 15 labelled defence articles for threat classification triaging.
- `evaluation/data/entity_pairs_eval.jsonl`: 15 labelled entity pairs (acronyms, commands, transliterations, locations) for entity resolution testing.
- `evaluation/data/event_type_eval_sample.jsonl`: Sample 10-item dataset for event-type classification testing.
- `evaluation/templates/labelling_template.csv`: Standard annotator template for collaborative dataset expansion.
