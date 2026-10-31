"""
Unit tests for the Evaluation Harness and Metrics (Jaish).
"""
import pytest
from evaluation.metrics import compute_classification_metrics, compute_grounding_rate
from evaluation.harness import evaluate_classifier, load_dataset


def test_compute_classification_metrics_perfect():
    y_true = ["high", "medium", "low", "high"]
    y_pred = ["high", "medium", "low", "high"]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["total_samples"] == 4


def test_compute_classification_metrics_imperfect():
    y_true = ["high", "medium", "low", "high"]
    y_pred = ["high", "low", "low", "medium"]
    metrics = compute_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 0.5
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert "high" in metrics["per_class"]


def test_compute_grounding_rate():
    sentences = [
        {"text": "Sentence 1", "citations": [101], "is_supported": True},
        {"text": "Sentence 2", "citations": [102], "is_supported": True},
        {"text": "Sentence 3", "citations": [], "is_supported": False},
        {"text": "Sentence 4", "citations": [103], "is_supported": True},
    ]
    grounding = compute_grounding_rate(sentences)
    assert grounding["total_sentences"] == 4
    assert grounding["supported_sentences"] == 3
    assert grounding["grounding_rate"] == 0.75
    assert grounding["hallucination_risk_rate"] == 0.25


def test_load_dataset_jsonl():
    dataset = load_dataset("evaluation/data/threat_level_eval.jsonl")
    assert len(dataset) >= 10
    first = dataset[0]
    assert "title" in first
    assert "threat_category" in first


def test_entity_pairs_eval_set_loading():
    dataset = load_dataset("evaluation/data/entity_pairs_eval.jsonl")
    assert len(dataset) >= 10
    first = dataset[0]
    assert "entity_a" in first
    assert "entity_b" in first
    assert first["label"] in ("MATCH", "DISTINCT", "REVIEW_NEEDED")
