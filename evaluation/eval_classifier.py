"""
Evaluation Runner for Raksha AI Event Classifier (Stage 1 MVP).

Evaluates `classify_event` on the benchmark evaluation dataset:
- Sourced from 40 examples across 10 canonical defense event categories.
- Tracks exact provenance breakdown:
  * 0 verbatim published headlines
  * 35 structured paraphrases of real, verifiable defense events
  * 4 synthetic domain archetypes (EV-18, EV-19, EV-23, EV-30)
  * 1 unverified example (EV-17)
- Reports overall accuracy, macro precision, macro recall, and macro F1-score.
- Reports separate metrics for the verified real-event subset.
- Reports per-class metrics (precision, recall, f1-score, support) and a 10x10 confusion matrix.

Dataset Limitation Notice:
    A 40-example evaluation dataset (4 examples per class across 10 canonical categories)
    is small for ten-class evaluation. It establishes an initial Stage 1 baseline
    benchmark rather than a definitive large-scale corpus evaluation. Achieving 92.5%
    accuracy on this small benchmark does NOT guarantee real-world generalization.

Confidence Terminology Notice:
    The baseline model's reported confidence scores represent predicted class
    probabilities produced by MultinomialNB.predict_proba(), not calibrated posterior
    probabilities.

Usage:
    python evaluation/eval_classifier.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.constants import EVENT_TYPES
from engine.classifier import CANONICAL_EVENT_TYPES, classify_event


def load_evaluation_dataset(dataset_path: str | Path | None = None) -> list[dict]:
    """Load the 40-example evaluation dataset with provenance metadata."""
    if dataset_path is None:
        root_dir = Path(__file__).resolve().parent.parent
        dataset_path = root_dir / "data" / "event_classification_dataset.json"

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Invalid evaluation dataset at {dataset_path}")

    return data


def _calculate_metrics(
    y_true: list[str], y_pred: list[str], labels: list[str]
) -> dict:
    """Calculate accuracy, macro averages, per-class metrics, and confusion matrix."""
    total_count = len(y_true)
    if total_count == 0:
        return {
            "total_examples": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "per_class": {},
            "confusion_matrix": [],
        }

    correct_count = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct_count / total_count

    per_class: dict[str, dict[str, float]] = {}
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []

    for label in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp == label)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != label and yp == label)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == label and yp != label)
        support = sum(1 for yt in y_true if yt == label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "support": support,
        }

    macro_precision = sum(precisions) / len(labels) if labels else 0.0
    macro_recall = sum(recalls) / len(labels) if labels else 0.0
    macro_f1 = sum(f1s) / len(labels) if labels else 0.0

    # 10x10 Confusion matrix (Rows: True, Columns: Predicted)
    matrix: list[list[int]] = []
    for true_lbl in labels:
        row: list[int] = []
        for pred_lbl in labels:
            count = sum(1 for yt, yp in zip(y_true, y_pred) if yt == true_lbl and yp == pred_lbl)
            row.append(count)
        matrix.append(row)

    return {
        "total_examples": total_count,
        "correct_predictions": correct_count,
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": matrix,
    }


def run_evaluation(dataset: list[dict] | None = None) -> dict:
    """
    Execute classification on evaluation dataset and compute accuracy,
    macro metrics, verified-subset metrics, per-class metrics, and confusion matrix.
    """
    if dataset is None:
        dataset = load_evaluation_dataset()

    labels = CANONICAL_EVENT_TYPES
    y_true: list[str] = []
    y_pred: list[str] = []
    y_true_verified: list[str] = []
    y_pred_verified: list[str] = []
    results: list[dict] = []

    provenance_counts: Counter = Counter()

    for item in dataset:
        true_label = item["label"]
        text = item["text"]
        p_type = item.get("provenance_type", "unverified")
        provenance_counts[p_type] += 1

        pred = classify_event(text)
        pred_label = pred["event_type"]
        confidence = pred["confidence"]

        y_true.append(true_label)
        y_pred.append(pred_label)

        if p_type == "paraphrase_of_real_event":
            y_true_verified.append(true_label)
            y_pred_verified.append(pred_label)

        results.append({
            "id": item.get("id"),
            "text": text,
            "true_label": true_label,
            "pred_label": pred_label,
            "confidence": confidence,
            "correct": true_label == pred_label,
            "provenance_type": p_type,
            "publisher": item.get("publisher"),
            "article_url": item.get("article_url"),
            "publication_date": item.get("publication_date"),
        })

    # Overall dataset metrics
    overall_metrics = _calculate_metrics(y_true, y_pred, labels)

    # Verified subset metrics (paraphrases of real events)
    verified_metrics = _calculate_metrics(y_true_verified, y_pred_verified, labels)

    return {
        "accuracy": overall_metrics["accuracy"],
        "macro_precision": overall_metrics["macro_precision"],
        "macro_recall": overall_metrics["macro_recall"],
        "macro_f1": overall_metrics["macro_f1"],
        "total_examples": overall_metrics["total_examples"],
        "correct_predictions": overall_metrics["correct_predictions"],
        "provenance_summary": {
            "verbatim_published_headline": provenance_counts.get("verbatim_published_headline", 0),
            "paraphrase_of_real_event": provenance_counts.get("paraphrase_of_real_event", 0),
            "synthetic": provenance_counts.get("synthetic", 0),
            "unverified": provenance_counts.get("unverified", 0),
        },
        "verified_subset": {
            "total_examples": verified_metrics["total_examples"],
            "correct_predictions": verified_metrics["correct_predictions"],
            "accuracy": verified_metrics["accuracy"],
            "macro_precision": verified_metrics["macro_precision"],
            "macro_recall": verified_metrics["macro_recall"],
            "macro_f1": verified_metrics["macro_f1"],
        },
        "labels": labels,
        "per_class": overall_metrics["per_class"],
        "confusion_matrix": overall_metrics["confusion_matrix"],
        "detailed_results": results,
    }


def print_evaluation_report(eval_output: dict) -> None:
    """Print formatted evaluation metrics, provenance breakdown, and confusion matrix."""
    print("=" * 82)
    print("RAKSHA AI - EVENT CLASSIFIER EVALUATION & QUALITY AUDIT REPORT (STAGE 1 MVP)")
    print("=" * 82)

    ps = eval_output["provenance_summary"]
    print("DATASET PROVENANCE BREAKDOWN:")
    print(f"  Verifiable Published Headlines / Snippets:  {ps['verbatim_published_headline']}")
    print(f"  Paraphrases Based on Real Events:           {ps['paraphrase_of_real_event']} (all with publisher/URL/date)")
    print(f"  Synthetic Domain Archetypes:                {ps['synthetic']} (EV-18, EV-19, EV-23, EV-30)")
    print(f"  Unverified Examples:                        {ps['unverified']}")
    print(f"  Total Evaluation Examples:                  {eval_output['total_examples']}")
    print("-" * 82)

    print("OVERALL PERFORMANCE (40 EXAMPLES):")
    print(f"  Correct Predictions:   {eval_output['correct_predictions']} / {eval_output['total_examples']}")
    print(f"  Overall Accuracy:      {eval_output['accuracy'] * 100:.2f}%")
    print(f"  Macro Precision:       {eval_output['macro_precision'] * 100:.2f}%")
    print(f"  Macro Recall:          {eval_output['macro_recall'] * 100:.2f}%")
    print(f"  Macro F1-Score:        {eval_output['macro_f1'] * 100:.2f}%")
    print("-" * 82)

    vs = eval_output["verified_subset"]
    print(f"VERIFIED SUBSET PERFORMANCE ({vs['total_examples']} REAL-EVENT PARAPHRASES):")
    print(f"  Correct Predictions:   {vs['correct_predictions']} / {vs['total_examples']}")
    print(f"  Accuracy:              {vs['accuracy'] * 100:.2f}%")
    print(f"  Macro Precision:       {vs['macro_precision'] * 100:.2f}%")
    print(f"  Macro Recall:          {vs['macro_recall'] * 100:.2f}%")
    print(f"  Macro F1-Score:        {vs['macro_f1'] * 100:.2f}%")
    print("-" * 82)

    print("LIMITATION & GENERALIZATION NOTICE:")
    print("  * Dataset size is 4 examples per category across 10 canonical categories (40 total).")
    print("  * A sample of 4 examples per category cannot establish real-world generalization.")
    print("  * The 92.5% accuracy achieved is a baseline benchmark on this curated test set;")
    print("    it does not predict real-world accuracy on unstructured open-web intelligence feeds.")
    print("  * Model confidence scores represent predicted class probabilities (MultinomialNB),")
    print("    not calibrated Bayesian posterior probabilities.")
    print("-" * 82)

    print(f"{'Category':<20} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 72)
    for cat, metrics in eval_output["per_class"].items():
        print(
            f"{cat:<20} | {metrics['precision']:<10.4f} | {metrics['recall']:<10.4f} | "
            f"{metrics['f1_score']:<10.4f} | {metrics['support']:<8}"
        )
    print("-" * 72)

    # Confusion Matrix
    print("\nCONFUSION MATRIX (Rows: True Label, Columns: Predicted Label):")
    labels = eval_output["labels"]
    short_labels = [f"[{i}]" for i in range(len(labels))]

    print(f"{'':<22}" + "".join(f"{lbl:>6}" for lbl in short_labels))
    for i, (label, row) in enumerate(zip(labels, eval_output["confusion_matrix"])):
        label_key = f"{short_labels[i]} {label}"
        row_str = "".join(f"{val:>6}" for val in row)
        print(f"{label_key:<22}{row_str}")

    print("=" * 82)


if __name__ == "__main__":
    eval_result = run_evaluation()
    print_evaluation_report(eval_result)
