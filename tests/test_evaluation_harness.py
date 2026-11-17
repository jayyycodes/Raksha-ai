"""
Unit tests for the Evaluation Harness and Metrics (Jaish).
"""
import pytest
from evaluation.metrics import compute_classification_metrics, compute_grounding_rate
from evaluation.harness import (
    classify_entity_pair,
    evaluate_classifier,
    load_dataset,
    run_entity_resolution_eval,
)


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


# ── Entity Resolution Pair Classification Regression Tests (Stage 3 Task 1) ──


def test_classify_entity_pair_both_auto_link_same_canonical():
    """Both entities auto-link to the exact same canonical entity -> MATCH."""
    res_a = {"canonical_name": "Indian Air Force", "action": "auto_link"}
    res_b = {"canonical_name": "Indian Air Force", "action": "auto_link"}
    assert classify_entity_pair(res_a, res_b) == "MATCH"


def test_classify_entity_pair_only_one_auto_links():
    """Only one entity auto-links; if same canonical -> REVIEW_NEEDED; if different -> DISTINCT."""
    # Same canonical name, but one is separate
    res_a = {"canonical_name": "HAL Tejas", "action": "auto_link"}
    res_b = {"canonical_name": "HAL Tejas", "action": "separate"}
    assert classify_entity_pair(res_a, res_b) == "REVIEW_NEEDED"

    # Different canonical names, only one auto-links
    res_c = {"canonical_name": "Indian Army", "action": "auto_link"}
    res_d = {"canonical_name": "Western Command", "action": "separate"}
    assert classify_entity_pair(res_c, res_d) == "DISTINCT"


def test_classify_entity_pair_either_in_review_queue():
    """Either entity in review_queue must NEVER auto-merge -> REVIEW_NEEDED."""
    # Case A: res_a in review_queue, res_b in auto_link (e.g. Tejas Mk1A vs LCA Tejas)
    res_a = {"canonical_name": "HAL Tejas", "action": "review_queue"}
    res_b = {"canonical_name": "HAL Tejas", "action": "auto_link"}
    assert classify_entity_pair(res_a, res_b) == "REVIEW_NEEDED"

    # Case B: res_a in auto_link, res_b in review_queue
    res_c = {"canonical_name": "HAL Tejas", "action": "auto_link"}
    res_d = {"canonical_name": "HAL Tejas", "action": "review_queue"}
    assert classify_entity_pair(res_c, res_d) == "REVIEW_NEEDED"

    # Case C: Both in review_queue
    res_e = {"canonical_name": "Depsang Plains", "action": "review_queue"}
    res_f = {"canonical_name": "Depsang Standoff", "action": "review_queue"}
    assert classify_entity_pair(res_e, res_f) == "REVIEW_NEEDED"


def test_classify_entity_pair_both_auto_link_different_canonical():
    """Both entities auto-link but to different canonical entities -> DISTINCT."""
    res_a = {"canonical_name": "Indian Air Force", "action": "auto_link"}
    res_b = {"canonical_name": "People's Liberation Army", "action": "auto_link"}
    assert classify_entity_pair(res_a, res_b) == "DISTINCT"


def test_classify_entity_pair_empty_or_missing_canonical():
    """Empty or missing canonical names must never auto-merge."""
    res_empty_a = {"canonical_name": "", "action": "auto_link"}
    res_empty_b = {"canonical_name": "", "action": "auto_link"}
    assert classify_entity_pair(res_empty_a, res_empty_b) == "DISTINCT"

    res_none_a = {"canonical_name": None, "action": "auto_link"}
    res_valid_b = {"canonical_name": "DRDO", "action": "auto_link"}
    assert classify_entity_pair(res_none_a, res_valid_b) == "DISTINCT"


def test_classify_entity_pair_both_separate():
    """Both entities return separate -> DISTINCT."""
    res_a = {"canonical_name": "Western Air Command", "action": "separate"}
    res_b = {"canonical_name": "Eastern Air Command", "action": "separate"}
    assert classify_entity_pair(res_a, res_b) == "DISTINCT"


def test_run_entity_resolution_eval_multiclass_and_conservative_safety_metrics():
    """
    Verify ResolutionAgent evaluation metrics on the 15-pair benchmark set:
    1. Automatic MATCH Precision: 100% (8/8 auto-merges correct, 0 false merges).
    2. Strict Multiclass Accuracy: 13/15 (86.67% exact match across MATCH, DISTINCT, REVIEW_NEEDED).
    3. Conservative Safety Metric: 100% (15/15 safe; no unverified pairs auto-merged).
    """
    results = run_entity_resolution_eval()
    assert results["total_pairs"] == 15
    assert results["auto_merges_predicted"] == 8
    assert results["auto_merge_precision"] == 1.0  # 8/8 = 100.0% clean auto-merges
    assert results["three_class_accuracy"] == 0.8667  # 13/15 = 86.67% exact 3-class matches
    assert results["overall_safety_accuracy"] == 1.0  # 15/15 = 100.0% operationally safe
