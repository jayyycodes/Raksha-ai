"""
Metrics computation module for Raksha AI Evaluation Harness.
Provides dependency-free calculations for Accuracy, Precision, Recall, F1, and Grounding Rate.
"""
from typing import Any, Dict, List, Set


def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
) -> Dict[str, Any]:
    """
    Computes accuracy, macro-averaged and per-class precision, recall, and F1.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} ground truth items vs {len(y_pred)} predictions")

    total = len(y_true)
    if total == 0:
        return {"accuracy": 0.0, "macro_f1": 0.0, "total": 0, "classes": {}}

    classes: Set[str] = set(y_true).union(set(y_pred))
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total

    class_metrics: Dict[str, Dict[str, float]] = {}
    f1_sum = 0.0
    precision_sum = 0.0
    recall_sum = 0.0

    for cls in sorted(classes):
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        class_metrics[cls] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": sum(1 for yt in y_true if yt == cls),
        }

        precision_sum += prec
        recall_sum += rec
        f1_sum += f1

    num_classes = len(classes)
    macro_precision = precision_sum / num_classes if num_classes > 0 else 0.0
    macro_recall = recall_sum / num_classes if num_classes > 0 else 0.0
    macro_f1 = f1_sum / num_classes if num_classes > 0 else 0.0

    return {
        "total_samples": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": class_metrics,
    }


def compute_grounding_rate(
    sentences: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes report grounding metrics:
    - total sentences
    - supported sentences (with >= 1 valid citation)
    - grounding rate (supported / total)
    """
    if not sentences:
        return {"total_sentences": 0, "supported_sentences": 0, "grounding_rate": 1.0}

    total = len(sentences)
    supported = sum(1 for s in sentences if s.get("is_supported", False) and len(s.get("citations", [])) > 0)
    rate = supported / total

    return {
        "total_sentences": total,
        "supported_sentences": supported,
        "grounding_rate": round(rate, 4),
        "hallucination_risk_rate": round(1.0 - rate, 4),
    }
