"""
Evaluation Harness for Raksha AI Agents.
Owner: Jaish
Stage: 1 (MVP)

Provides CLI and programmatic runner to benchmark any agent against labelled sets.
Generates accuracy, precision, recall, F1, and markdown evaluation summaries for PRs.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from evaluation.metrics import compute_classification_metrics, compute_grounding_rate


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Loads JSON or JSONL labelled dataset."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    records = []
    if path.suffix == ".jsonl":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    else:
        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)
    return records


def evaluate_classifier(
    predict_fn: Callable[[Dict[str, Any]], str],
    dataset: List[Dict[str, Any]],
    target_key: str = "target",
    agent_name: str = "agent",
) -> Dict[str, Any]:
    """
    Evaluates a classification function against a labelled dataset.
    """
    y_true: List[str] = []
    y_pred: List[str] = []
    failures: List[Dict[str, Any]] = []

    for item in dataset:
        true_label = str(item[target_key]).lower()
        try:
            pred_label = str(predict_fn(item)).lower()
        except Exception as e:
            pred_label = "ERROR"
            failures.append({"item": item, "error": str(e)})

        y_true.append(true_label)
        y_pred.append(pred_label)

    metrics = compute_classification_metrics(y_true, y_pred)
    metrics["agent_name"] = agent_name
    metrics["failures_count"] = len(failures)
    metrics["failures"] = failures[:5]  # first 5 failures for debugging
    return metrics


def format_markdown_table(metrics: Dict[str, Any]) -> str:
    """Formats metrics dictionary into a GitHub markdown table for PR descriptions."""
    lines = [
        f"### Model Evaluation Report: `{metrics.get('agent_name', 'Agent')}`",
        "",
        f"- **Total Samples:** {metrics.get('total_samples', 0)}",
        f"- **Overall Accuracy:** {metrics.get('accuracy', 0.0) * 100:.2f}%",
        f"- **Macro F1 Score:** {metrics.get('macro_f1', 0.0):.4f}",
        f"- **Macro Precision:** {metrics.get('macro_precision', 0.0):.4f}",
        f"- **Macro Recall:** {metrics.get('macro_recall', 0.0):.4f}",
        "",
        "| Class | Precision | Recall | F1 Score | Support |",
        "|---|---|---|---|---|",
    ]
    for cls, cm in metrics.get("per_class", {}).items():
        lines.append(
            f"| `{cls}` | {cm['precision']:.3f} | {cm['recall']:.3f} | {cm['f1']:.3f} | {cm['support']} |"
        )
    return "\n".join(lines)


def run_threat_classifier_eval(dataset_path: str = "evaluation/data/threat_level_eval.jsonl") -> Dict[str, Any]:
    """Helper to benchmark ThreatClassifierV0."""
    from agents.scoring.classifier_v0 import ThreatClassifierV0
    classifier = ThreatClassifierV0()

    dataset = load_dataset(dataset_path)

    def predict(item: Dict[str, Any]) -> str:
        out = classifier.classify(
            title=item.get("title", ""),
            content=item.get("content", ""),
            event_type=item.get("event_type", "general"),
            ring=item.get("ring", 1),
        )
        return out.category.value

    return evaluate_classifier(predict, dataset, target_key="threat_category", agent_name="ThreatClassifierV0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raksha AI Evaluation Harness")
    parser.add_argument("--agent", choices=["threat_v0"], default="threat_v0")
    parser.add_argument("--dataset", type=str, default="evaluation/data/threat_level_eval.jsonl")
    args = parser.parse_args()

    if args.agent == "threat_v0":
        results = run_threat_classifier_eval(args.dataset)
        print(format_markdown_table(results))
