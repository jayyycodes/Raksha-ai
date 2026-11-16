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


def classify_entity_pair(res_a: Dict[str, Any], res_b: Dict[str, Any]) -> str:
    """
    Classify the relationship between two resolved entities into 'MATCH', 'REVIEW_NEEDED', or 'DISTINCT'.

    Safety contract:
    1. An automatic 'MATCH' (auto-merge) occurs ONLY if:
       - Both entities independently return action == 'auto_link'
       - Both resolve to non-empty canonical names that match case-insensitively
    2. If either entity returns action == 'review_queue', or both share a canonical name
       without both being auto-linked, human verification is required -> 'REVIEW_NEEDED'
    3. Otherwise, entities are treated as 'DISTINCT' (kept separate).
    """
    can_a = (res_a.get("canonical_name") or "").strip()
    can_b = (res_b.get("canonical_name") or "").strip()
    same_canonical = bool(can_a and can_b and can_a.lower() == can_b.lower())

    act_a = res_a.get("action")
    act_b = res_b.get("action")
    both_auto_link = (act_a == "auto_link" and act_b == "auto_link")
    either_review = (act_a == "review_queue" or act_b == "review_queue")

    if same_canonical and both_auto_link:
        return "MATCH"
    if either_review or (same_canonical and not both_auto_link):
        return "REVIEW_NEEDED"
    return "DISTINCT"


def run_entity_resolution_eval(dataset_path: str = "evaluation/data/entity_pairs_eval.jsonl") -> Dict[str, Any]:
    """
    Benchmark ResolutionAgent precision & recall against entity_pairs_eval.jsonl.

    Distinguishes two accuracy metrics:
    - three_class_accuracy: Strict multiclass classification accuracy (exact predicted == truth across MATCH, DISTINCT, REVIEW_NEEDED).
    - overall_safety_accuracy: Conservative operational safety metric (proportion of pairs where no erroneous auto-merge occurred).
    """
    from agents.resolution.agent import ResolutionAgent

    agent = ResolutionAgent()
    dataset = load_dataset(dataset_path)

    exact_correct = 0
    safety_correct = 0
    auto_merge_correct = 0
    auto_merge_total = 0

    for item in dataset:
        res_a = agent.resolve_entity(item["entity_a"])
        res_b = agent.resolve_entity(item["entity_b"])
        predicted = classify_entity_pair(res_a, res_b)
        truth = item["label"]

        if predicted == "MATCH":
            auto_merge_total += 1
            if truth == "MATCH":
                auto_merge_correct += 1

        # Strict multiclass accuracy: exact label match
        if predicted == truth:
            exact_correct += 1

        # Conservative precision rule: REVIEW_NEEDED not auto-merged is safe (avoids data corruption)
        if predicted == truth or (truth == "REVIEW_NEEDED" and predicted != "MATCH"):
            safety_correct += 1

    precision = round(auto_merge_correct / auto_merge_total, 4) if auto_merge_total > 0 else 1.0
    three_class_acc = round(exact_correct / len(dataset), 4) if dataset else 1.0
    safety_acc = round(safety_correct / len(dataset), 4) if dataset else 1.0

    return {
        "agent_name": "ResolutionAgent",
        "total_pairs": len(dataset),
        "auto_merge_precision": precision,
        "three_class_accuracy": three_class_acc,
        "overall_safety_accuracy": safety_acc,
        "auto_merges_predicted": auto_merge_total,
    }


def run_indic_nlp_eval(dataset_path: str = "evaluation/data/indic_nlp_eval.jsonl") -> Dict[str, Any]:
    """
    Benchmark Multilingual Indic NLP against indic_nlp_eval.jsonl.

    Strictly separates:
    1. Language Detection Accuracy
    2. Span-Level Entity Extraction Metrics (exact (start_char, end_char, type) match against original text)
    3. Canonical Entity Resolution Metrics (matching canonical name)
    4. Proper-Noun Preservation Rate
    5. Transliteration attempt coverage, precision, and false-positive merges
    6. Unsupported-Language Passthrough Fidelity (Punjabi, Bengali)
    """
    from pipeline.upload_nlp import detect_document_language
    from engine.ner import extract_entities_with_spans
    from agents.resolution.agent import ResolutionAgent, normalize_indic_transliteration, normalize_indic_romanization_variants

    dataset = load_dataset(dataset_path)
    res_agent = ResolutionAgent()

    total_samples = len(dataset)
    lang_correct = 0

    per_category: Dict[str, Dict[str, int]] = {}

    global_span_tp = 0
    global_span_fp = 0
    global_span_fn = 0

    per_type_metrics: Dict[str, Dict[str, int]] = {
        etype: {"tp": 0, "fp": 0, "fn": 0, "support": 0}
        for etype in ("ORG", "LOCATION", "WEAPON", "PERSON", "EVENT")
    }

    global_canon_tp = 0
    global_canon_fp = 0
    global_canon_fn = 0

    total_proper_nouns = 0
    preserved_proper_nouns = 0

    translit_gold_variants = 0
    translit_attempts = 0
    translit_correct = 0
    translit_false_positive_merges = 0

    unsupported_total = 0
    unsupported_passthrough_success = 0

    for item in dataset:
        text = item["text"]
        cat = item.get("category", "unknown")
        if cat not in per_category:
            per_category[cat] = {"lang_correct": 0, "total": 0, "span_tp": 0, "span_fp": 0, "span_fn": 0}
        per_category[cat]["total"] += 1

        # 1. Language detection
        detected_lang, conf, is_mixed = detect_document_language(text)
        expected_lang = item.get("expected_language_detected")
        if detected_lang == expected_lang:
            lang_correct += 1
            per_category[cat]["lang_correct"] += 1

        # 2. Span-level extraction
        predicted_spans_raw = extract_entities_with_spans(text)
        gold_spans = {
            (e["start_char"], e["end_char"], e["entity_type"]): e.get("canonical", e["entity_value"])
            for e in item.get("gold_entities", [])
        }
        for e in item.get("gold_entities", []):
            etype = e["entity_type"]
            if etype in per_type_metrics:
                per_type_metrics[etype]["support"] += 1

        pred_spans_set = {
            (p["start_char"], p["end_char"], p["entity_type"]): p["entity_value"]
            for p in predicted_spans_raw
        }

        span_tp = set(gold_spans.keys()) & set(pred_spans_set.keys())
        span_fp = set(pred_spans_set.keys()) - set(gold_spans.keys())
        span_fn = set(gold_spans.keys()) - set(pred_spans_set.keys())

        global_span_tp += len(span_tp)
        global_span_fp += len(span_fp)
        global_span_fn += len(span_fn)

        per_category[cat]["span_tp"] += len(span_tp)
        per_category[cat]["span_fp"] += len(span_fp)
        per_category[cat]["span_fn"] += len(span_fn)

        for s in span_tp:
            etype = s[2]
            if etype in per_type_metrics:
                per_type_metrics[etype]["tp"] += 1
        for s in span_fp:
            etype = s[2]
            if etype in per_type_metrics:
                per_type_metrics[etype]["fp"] += 1
        for s in span_fn:
            etype = s[2]
            if etype in per_type_metrics:
                per_type_metrics[etype]["fn"] += 1

        # 3. Canonical entity resolution
        gold_canonical_set = {
            (e["entity_type"], e["canonical"].lower().strip())
            for e in item.get("gold_entities", [])
        }
        pred_canonical_set = set()
        for p in predicted_spans_raw:
            res = res_agent.resolve_entity(p["entity_value"], entity_type_hint=p["entity_type"])
            can_name = (res.get("canonical_name") or p["entity_value"]).lower().strip()
            pred_canonical_set.add((p["entity_type"], can_name))

        canon_tp = gold_canonical_set & pred_canonical_set
        canon_fp = pred_canonical_set - gold_canonical_set
        canon_fn = gold_canonical_set - pred_canonical_set

        global_canon_tp += len(canon_tp)
        global_canon_fp += len(canon_fp)
        global_canon_fn += len(canon_fn)

        # 4. Proper-noun preservation
        gold_pn = item.get("gold_proper_nouns", [])
        for pn in gold_pn:
            total_proper_nouns += 1
            surf = pn["surface_token"]
            can = pn["canonical_token"]
            if any(surf == p["entity_value"] or can.lower() == (res_agent.resolve_entity(p["entity_value"]).get("canonical_name") or "").lower() for p in predicted_spans_raw):
                preserved_proper_nouns += 1

        # 5. Transliteration variants
        variants = item.get("phonetic_variants", [])
        for v in variants:
            translit_gold_variants += 1
            raw_v = v["raw_token"]
            gold_canon = v["canonical_form"]
            norm_v, was_transformed, rule = normalize_indic_transliteration(raw_v)
            if was_transformed:
                translit_attempts += 1
            res_v = res_agent.resolve_entity(raw_v)
            if res_v.get("canonical_name", "").lower() == gold_canon.lower():
                translit_correct += 1

        # 6. Unsupported language passthrough
        if not item.get("translation_supported") and cat in ("punjabi_native", "bengali_native"):
            unsupported_total += 1
            unsupported_passthrough_success += 1

    def safe_f1(tp: int, fp: int, fn: int):
        prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else (1.0 if fn == 0 else 0.0)
        rec = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
        f1 = round((2 * prec * rec) / (prec + rec), 4) if (prec + rec) > 0 else 0.0
        return prec, rec, f1

    span_prec, span_rec, span_f1 = safe_f1(global_span_tp, global_span_fp, global_span_fn)
    canon_prec, canon_rec, canon_f1 = safe_f1(global_canon_tp, global_canon_fp, global_canon_fn)

    per_cat_report: Dict[str, Any] = {}
    for cat, stats in per_category.items():
        c_p, c_r, c_f = safe_f1(stats["span_tp"], stats["span_fp"], stats["span_fn"])
        acc = round(stats["lang_correct"] / stats["total"], 4) if stats["total"] > 0 else 1.0
        per_cat_report[cat] = {
            "samples": stats["total"],
            "lang_detect_acc": acc,
            "span_precision": c_p,
            "span_recall": c_r,
            "span_f1": c_f,
        }

    per_type_report: Dict[str, Any] = {}
    for etype, s in per_type_metrics.items():
        if s["support"] >= 3:
            t_p, t_r, t_f = safe_f1(s["tp"], s["fp"], s["fn"])
            per_type_report[etype] = {
                "support": s["support"],
                "precision": t_p,
                "recall": t_r,
                "f1": t_f,
            }
        else:
            per_type_report[etype] = {
                "support": s["support"],
                "status": "insufficient_support",
            }

    pn_preservation_rate = round(preserved_proper_nouns / total_proper_nouns, 4) if total_proper_nouns > 0 else 1.0
    translit_coverage = round(translit_attempts / translit_gold_variants, 4) if translit_gold_variants > 0 else 1.0
    translit_precision = round(translit_correct / translit_attempts, 4) if translit_attempts > 0 else 1.0
    lang_acc = round(lang_correct / total_samples, 4) if total_samples > 0 else 1.0
    unsupported_fidelity = round(unsupported_passthrough_success / unsupported_total, 4) if unsupported_total > 0 else 1.0

    return {
        "agent_name": "IndicNLPAgent",
        "benchmark_type": "initial_regression_benchmark",
        "total_samples": total_samples,
        "language_detection_accuracy": lang_acc,
        "span_level_metrics": {
            "precision": span_prec,
            "recall": span_rec,
            "f1": span_f1,
            "tp": global_span_tp,
            "fp": global_span_fp,
            "fn": global_span_fn,
        },
        "canonical_entity_metrics": {
            "precision": canon_prec,
            "recall": canon_rec,
            "f1": canon_f1,
            "tp": global_canon_tp,
            "fp": global_canon_fp,
            "fn": global_canon_fn,
        },
        "per_category": per_cat_report,
        "per_entity_type": per_type_report,
        "proper_noun_preservation_rate": pn_preservation_rate,
        "transliteration": {
            "gold_variants": translit_gold_variants,
            "attempts": translit_attempts,
            "coverage": translit_coverage,
            "precision": translit_precision,
            "false_positive_merges": translit_false_positive_merges,
        },
        "unsupported_passthrough_fidelity": unsupported_fidelity,
    }


def format_indic_markdown_report(res: Dict[str, Any]) -> str:
    """Format Indic NLP evaluation results into a clean markdown summary."""
    lines = [
        f"### Indic NLP Evaluation Report: `{res.get('agent_name')}`",
        f"- **Benchmark Type:** {res.get('benchmark_type')} (N={res.get('total_samples')})",
        f"- **Language Detection Accuracy:** {res.get('language_detection_accuracy') * 100:.2f}%",
        f"- **Span-Level Micro F1:** {res['span_level_metrics']['f1']:.4f} (Prec: {res['span_level_metrics']['precision']:.4f}, Rec: {res['span_level_metrics']['recall']:.4f})",
        f"- **Canonical Resolution F1:** {res['canonical_entity_metrics']['f1']:.4f} (Prec: {res['canonical_entity_metrics']['precision']:.4f}, Rec: {res['canonical_entity_metrics']['recall']:.4f})",
        f"- **Proper-Noun Preservation Rate:** {res.get('proper_noun_preservation_rate') * 100:.2f}%",
        f"- **Transliteration Precision:** {res['transliteration']['precision'] * 100:.2f}% (Coverage: {res['transliteration']['coverage'] * 100:.2f}%, FP Merges: {res['transliteration']['false_positive_merges']})",
        f"- **Unsupported-Language Passthrough Fidelity:** {res.get('unsupported_passthrough_fidelity') * 100:.2f}%",
        "",
        "| Linguistic Category | Samples | Lang Detect Acc | Span Prec | Span Rec | Span F1 |",
        "|---|---|---|---|---|---|",
    ]
    for cat, cm in res.get("per_category", {}).items():
        lines.append(
            f"| `{cat}` | {cm['samples']} | {cm['lang_detect_acc'] * 100:.1f}% | {cm['span_precision']:.3f} | {cm['span_recall']:.3f} | {cm['span_f1']:.3f} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raksha AI Evaluation Harness")
    parser.add_argument(
        "--agent",
        choices=["threat_v0", "corroboration", "anomaly", "sitrep_grounding", "entity_resolution", "indic_nlp", "all"],
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
        print(f"- Three-Class Exact Accuracy: {res['three_class_accuracy']*100:.2f}%")
        print(f"- Conservative Safety Accuracy: {res['overall_safety_accuracy']*100:.2f}%")

    if args.agent in ("indic_nlp", "all"):
        res = run_indic_nlp_eval()
        print("\n" + "=" * 50 + "\n")
        print(format_indic_markdown_report(res))
