# Raksha AI — Evaluation Harness & Benchmark Suite

**Owner:** Jaish  
**Role:** AI/ML Intelligence & Evaluation

---

## Overview

The evaluation suite ensures all Raksha AI models and agents are backed by measurable benchmarks against labelled ground truth datasets. **No agent code is merged into `dev` without evaluation metrics in the PR.**

---

## Directory Structure

```
evaluation/
├── harness.py                # Main CLI and evaluation runner
├── metrics.py                # Precision, Recall, F1, Accuracy, Grounding Rate
├── data/
│   ├── threat_level_eval.jsonl      # Jaish: Threat level benchmark dataset
│   ├── entity_pairs_eval.jsonl      # Jaish: Entity pair resolution benchmark
│   └── event_type_eval_sample.jsonl # Ary: Event type classification sample
└── templates/
    └── labelling_template.csv       # Standard format for team data annotations
```

---

## Running Benchmarks

### 1. Threat Classifier v0 Benchmark
```bash
python -m evaluation.harness --agent threat_v0 --dataset evaluation/data/threat_level_eval.jsonl
```

### 2. Programmatic Usage in Tests & CI
```python
from evaluation.harness import evaluate_classifier, load_dataset
from agents.scoring.classifier_v0 import ThreatClassifierV0

classifier = ThreatClassifierV0()
dataset = load_dataset("evaluation/data/threat_level_eval.jsonl")

def predict(item):
    res = classifier.classify(item["title"], item.get("content", ""), item.get("event_type", "general"), item.get("ring", 1))
    return res.category.value

metrics = evaluate_classifier(predict, dataset, target_key="threat_category")
assert metrics["accuracy"] >= 0.70  # Minimum 70% accuracy requirement
```

---

## Guidelines for Labelling Data

1. **Entity Pairs:**
   - `MATCH`: Canonical variations, acronyms, or transliteration variants referring to the exact same entity.
   - `DISTINCT`: Different entities (e.g. separate geographic locations or different military branches).
   - `REVIEW_NEEDED`: Relationship between entity and event or appointment title that should not be automatically merged without human signoff.

2. **Grounding Rate:**
   - Every sentence in generated SitReps must link to >= 1 valid article source ID.
   - Unsupported sentences must be flagged with `is_supported=False`.
