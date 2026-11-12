"""
Evaluation Harness for Raksha AI Agents.
Owner: Jaish
Stage: 2 (Mid)

Provides CLI and programmatic runner to benchmark any agent against labelled sets.
Generates accuracy, precision, recall, F1, grounding rate, and markdown summaries for PRs.
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
    metrics["failures"] = failures[:5]
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
    """Benchmark ThreatClassifierV0."""
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


def run_corroboration_eval(dataset_path: str = "evaluation/data/corroboration_eval.jsonl") -> Dict[str, Any]:
    """Benchmark CorroborationAgent."""
    from agents.corroboration.corroboration_agent import CorroborationAgent
    agent = CorroborationAgent()
    dataset = load_dataset(dataset_path)

    def predict(item: Dict[str, Any]) -> str:
        out = agent.analyze_pair(
            source_article_id=item.get("id", 1),
            source_text=item.get("source_text", ""),
            source_ring=item.get("source_ring", 1),
            compare_article_id=item.get("id", 1) + 100,
            compare_text=item.get("compare_text", ""),
            compare_ring=item.get("compare_ring", 2),
        )
        return out.relation

    return evaluate_classifier(predict, dataset, target_key="target_relation", agent_name="CorroborationAgent")


def run_anomaly_eval(dataset_path: str = "evaluation/data/anomaly_eval.jsonl") -> Dict[str, Any]:
    """Benchmark AnomalyAgent."""
    from agents.scoring.anomaly_agent import AnomalyAgent
    agent = AnomalyAgent()
    dataset = load_dataset(dataset_path)

    def predict(item: Dict[str, Any]) -> str:
        # Construct synthetic articles matching item count and threat flags
        count = item.get("article_count", 0)
        highs = item.get("high_threat_count", 0)
        arts = []
        for i in range(count):
            arts.append({
                "id": i + 1,
                "threat_level": 9 if i < highs else 3,
                "sentiment": "alarming" if i < highs else "neutral",
            })
        out = agent.detect_region_anomaly(
            region=item.get("region", "LAC-Ladakh"),
            current_articles=arts,
            baseline_daily_average=item.get("baseline_daily", 2.0),
        )
        return str(out.is_anomaly).lower()

    # Normalize ground truth boolean to string
    normalized_dataset = []
    for d in dataset:
        copy_d = dict(d)
        copy_d["target_anomaly"] = str(d["is_anomaly"]).lower()
        normalized_dataset.append(copy_d)

    return evaluate_classifier(predict, normalized_dataset, target_key="target_anomaly", agent_name="AnomalyAgent")


def run_sitrep_grounding_eval(dataset_path: str = "evaluation/data/sitrep_grounding_eval.jsonl") -> Dict[str, Any]:
    """Evaluates SitRep sentence-level grounding rate and attribution accuracy."""
    from agents.report.sitrep_agent import GroundedSitRepAgent
    agent = GroundedSitRepAgent()
    dataset = load_dataset(dataset_path)

    correct_flag_count = 0
    total = len(dataset)
    supported_count = 0

    for item in dataset:
        cites, is_supported = agent._extract_citations(item["text"], set(item["valid_ids"]))
        if is_supported == item["expected_supported"]:
            correct_flag_count += 1
        if is_supported:
            supported_count += 1

    accuracy = round(correct_flag_count / total, 4) if total > 0 else 1.0
    grounding_rate = round(supported_count / total, 4) if total > 0 else 0.0

    return {
        "agent_name": "GroundedSitRepAgent",
        "total_sentences": total,
        "grounding_attribution_accuracy": accuracy,
        "sample_grounding_rate": grounding_rate,
        "unsupported_flagged_correctly": correct_flag_count,
    }


def run_entity_resolution_eval(dataset_path: str = "evaluation/data/entity_pairs_eval.jsonl") -> Dict[str, Any]:
    """Benchmark ResolutionAgent precision & recall against entity_pairs_eval.jsonl."""
    from agents.resolution.agent import ResolutionAgent

    agent = ResolutionAgent()
    dataset = load_dataset(dataset_path)

    correct = 0
    auto_merge_correct = 0
    auto_merge_total = 0

    for item in dataset:
        res_a = agent.resolve_entity(item["entity_a"])
        res_b = agent.resolve_entity(item["entity_b"])
        same_canonical = res_a["canonical_name"].strip().lower() == res_b["canonical_name"].strip().lower()
        both_strong = res_a["action"] == "auto_link" or res_b["action"] == "auto_link"

        predicted = "MATCH" if (same_canonical and both_strong) else (
            "REVIEW_NEEDED" if (res_a["action"] == "review_queue" or res_b["action"] == "review_queue") else "DISTINCT"
        )
        truth = item["label"]

        if predicted == "MATCH":
            auto_merge_total += 1
            if truth == "MATCH":
                auto_merge_correct += 1

        # Conservative precision rule: REVIEW_NEEDED not auto-merged is safe
        if predicted == truth or (truth == "REVIEW_NEEDED" and predicted != "MATCH"):
            correct += 1

    precision = round(auto_merge_correct / auto_merge_total, 4) if auto_merge_total > 0 else 1.0
    accuracy = round(correct / len(dataset), 4) if dataset else 1.0
    return {
        "agent_name": "ResolutionAgent",
        "total_pairs": len(dataset),
        "auto_merge_precision": precision,
        "overall_safety_accuracy": accuracy,
        "auto_merges_predicted": auto_merge_total,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raksha AI Evaluation Harness")
    parser.add_argument(
        "--agent",
        choices=["threat_v0", "corroboration", "anomaly", "sitrep_grounding", "entity_resolution", "all"],
        default="all",
    )
    args = parser.parse_args()

    if args.agent in ("threat_v0", "all"):
        res = run_threat_classifier_eval()
        print(format_markdown_table(res))
        print("\n" + "=" * 50 + "\n")

    if args.agent in ("corroboration", "all"):
        res = run_corroboration_eval()
        print(format_markdown_table(res))
        print("\n" + "=" * 50 + "\n")

    if args.agent in ("anomaly", "all"):
        res = run_anomaly_eval()
        print(format_markdown_table(res))
        print("\n" + "=" * 50 + "\n")

    if args.agent in ("sitrep_grounding", "all"):
        res = run_sitrep_grounding_eval()
        print(f"### SitRep Grounding Verification Report:")
        print(f"- Total Evaluated Sentences: {res['total_sentences']}")
        print(f"- Citation Grounding Accuracy: {res['grounding_attribution_accuracy']*100:.2f}%")
        print(f"- Sample Grounding Rate: {res['sample_grounding_rate']*100:.2f}%")
        print("\n" + "=" * 50 + "\n")

    if args.agent in ("entity_resolution", "all"):
        res = run_entity_resolution_eval()
        print(f"### Entity Resolution Precision Report:")
        print(f"- Total Evaluated Pairs: {res['total_pairs']}")
        print(f"- Auto-Merge Precision: {res['auto_merge_precision']*100:.2f}% ({res['auto_merges_predicted']} auto-merges)")
        print(f"- Conservative Safety Accuracy: {res['overall_safety_accuracy']*100:.2f}%")
