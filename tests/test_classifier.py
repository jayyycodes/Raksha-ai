"""
Automated unit tests for engine/classifier.py (Stage 1 Event Classification MVP).

Tests:
1. Input validation (empty, whitespace, None, non-string, invalid model_name)
2. Output contract (exact keys {"event_type", "confidence"}, types, and confidence bounds [0.0, 1.0])
3. Canonical category restriction (strictly one of EVENT_TYPES)
4. Model lazy loading and thread-safe caching across repeated calls
5. Model load failure handling (ModelLoadError)
6. Inference failure handling (InferenceError)
7. Non-canonical category rejection
8. Evaluation runner integration and benchmark metric structure

All tests are deterministic and use mocked or baseline components without downloading external weights.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from common.constants import EVENT_TYPES
from engine.classifier import (
    CANONICAL_EVENT_TYPES,
    DEFAULT_MODEL,
    InferenceError,
    ModelLoadError,
    classify_event,
    clear_classifier_cache,
    get_cached_models,
)
from evaluation.eval_classifier import load_evaluation_dataset, run_evaluation


class TestClassifierInputValidation(unittest.TestCase):
    """Test validation of empty, whitespace, None, and non-string inputs."""

    def setUp(self):
        clear_classifier_cache()

    def test_empty_string_raises_value_error(self):
        """Empty string input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            classify_event("")
        self.assertIn("non-empty string", str(ctx.exception))

    def test_whitespace_only_string_raises_value_error(self):
        """Whitespace-only string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            classify_event("   \t\n  ")
        self.assertIn("non-empty string", str(ctx.exception))

    def test_none_input_raises_value_error(self):
        """None input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            classify_event(None)
        self.assertIn("non-empty string", str(ctx.exception))

    def test_non_string_input_raises_value_error(self):
        """Non-string inputs (e.g. integer, dict, list) raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            classify_event(12345)
        self.assertIn("non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            classify_event(["Indian Navy"])
        self.assertIn("non-empty string", str(ctx.exception))

    def test_invalid_model_name_raises_value_error(self):
        """Empty, None, or non-string model_name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            classify_event("Valid article text", model_name="")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            classify_event("Valid article text", model_name="   ")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            classify_event("Valid article text", model_name=None)
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))


class TestClassifierOutputContractAndCategories(unittest.TestCase):
    """Test output dictionary contract, valid canonical types, and confidence scores."""

    def setUp(self):
        clear_classifier_cache()

    def test_output_contract_exact_keys_and_types(self):
        """classify_event returns exactly {"event_type": str, "confidence": float}."""
        res = classify_event("Indian Navy deploys guided missile destroyer in Arabian Sea")

        self.assertIsInstance(res, dict)
        self.assertEqual(set(res.keys()), {"event_type", "confidence"})
        self.assertIsInstance(res["event_type"], str)
        self.assertIsInstance(res["confidence"], float)

    def test_event_type_is_canonical(self):
        """Returned event_type must strictly be in CANONICAL_EVENT_TYPES."""
        test_samples = [
            "Cross-border shelling reported along Line of Control",
            "Ransomware attack corrupts government servers",
            "Counter-terror encounter neutralises militants",
            "Foreign ministers hold bilateral summit",
            "Deepfake video circulates as propaganda",
            "Armored brigade deployed to forward base",
            "Warship conducts maritime anti-piracy patrol",
            "Fighter jet intercepts unidentified aerial target",
            "Strategic forces conduct ballistic missile test",
            "Defense ministry announces annual budget increase",
        ]

        for text in test_samples:
            res = classify_event(text)
            self.assertIn(
                res["event_type"],
                CANONICAL_EVENT_TYPES,
                f"Prediction '{res['event_type']}' not in canonical event types",
            )

    def test_confidence_bounds(self):
        """Confidence score must be bounded within [0.0, 1.0]."""
        res = classify_event("Fighter jets scrambled to intercept suspicious drone")
        self.assertGreaterEqual(res["confidence"], 0.0)
        self.assertLessEqual(res["confidence"], 1.0)

    def test_mocked_prediction_output(self):
        """Verify output contract with a deterministic mock model."""
        mock_model = MagicMock()
        # Mock 10-class probability distribution
        probs = np.array([[0.05, 0.85, 0.02, 0.01, 0.01, 0.02, 0.01, 0.01, 0.01, 0.01]])
        mock_model.predict_proba.return_value = probs
        mock_model.classes_ = np.array(CANONICAL_EVENT_TYPES)

        with patch("engine.classifier._load_model", return_value=mock_model):
            result = classify_event("Cyber breach targeting defense network")

        self.assertEqual(result["event_type"], "cyber_attack")
        self.assertAlmostEqual(result["confidence"], 0.85, places=4)


class TestClassifierLazyLoadingAndCaching(unittest.TestCase):
    """Test model lazy loading, caching across calls, and cache clearance."""

    def setUp(self):
        clear_classifier_cache()

    def test_model_is_lazily_loaded_on_first_call(self):
        """Model is not loaded until classify_event is called."""
        self.assertEqual(len(get_cached_models()), 0)

        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.9] + [0.01] * 9])
        mock_model.classes_ = np.array(CANONICAL_EVENT_TYPES)

        with patch("engine.classifier._load_model", return_value=mock_model) as loader:
            res = classify_event("Border clash reported")
            self.assertEqual(loader.call_count, 1)
            loader.assert_called_once_with(DEFAULT_MODEL)
            self.assertIn(DEFAULT_MODEL, get_cached_models())
            self.assertIn("event_type", res)

    def test_model_is_cached_across_repeated_calls(self):
        """Repeated classify_event calls reuse cached model without reloading."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.9] + [0.01] * 9])
        mock_model.classes_ = np.array(CANONICAL_EVENT_TYPES)

        with patch("engine.classifier._load_model", return_value=mock_model) as loader:
            res1 = classify_event("Headline one")
            res2 = classify_event("Headline two")
            res3 = classify_event("Headline three")

            self.assertEqual(loader.call_count, 1)

    def test_clear_classifier_cache_evicts_models(self):
        """clear_classifier_cache() purges cached models from memory."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.9] + [0.01] * 9])
        mock_model.classes_ = np.array(CANONICAL_EVENT_TYPES)

        with patch("engine.classifier._load_model", return_value=mock_model):
            classify_event("Sample headline")
            self.assertEqual(len(get_cached_models()), 1)

            clear_classifier_cache()
            self.assertEqual(len(get_cached_models()), 0)


class TestClassifierFailureModes(unittest.TestCase):
    """Test error handling for model load, inference, and non-canonical category errors."""

    def setUp(self):
        clear_classifier_cache()

    def test_model_load_failure_raises_model_load_error(self):
        """When model loading fails, ModelLoadError is raised."""
        with patch(
            "engine.classifier._load_model",
            side_effect=ModelLoadError("Corrupted model weights file"),
        ):
            with self.assertRaises(ModelLoadError) as ctx:
                classify_event("Sample headline")
            self.assertIn("Corrupted model weights", str(ctx.exception))

    def test_inference_failure_raises_inference_error(self):
        """When model prediction raises an exception, InferenceError is raised."""
        mock_model = MagicMock()
        mock_model.predict_proba.side_effect = RuntimeError("Prediction computation error")

        with patch("engine.classifier._load_model", return_value=mock_model):
            with self.assertRaises(InferenceError) as ctx:
                classify_event("Sample headline")
            self.assertIn("Failed to classify event text", str(ctx.exception))

    def test_non_canonical_predicted_class_raises_value_error(self):
        """If model produces an unknown category outside EVENT_TYPES, raise ValueError."""
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[1.0]])
        mock_model.classes_ = np.array(["unsupported_alien_invasion"])

        with patch("engine.classifier._load_model", return_value=mock_model):
            with self.assertRaises(ValueError) as ctx:
                classify_event("Sample headline")
            self.assertIn("non-canonical category", str(ctx.exception))


class TestClassifierEvaluationIntegration(unittest.TestCase):
    """Test dataset loading and evaluation runner integrity."""

    def test_evaluation_dataset_structure(self):
        """Evaluation dataset contains 40 curated examples covering all 10 classes with provenance."""
        dataset = load_evaluation_dataset()
        self.assertEqual(len(dataset), 40)

        classes_in_dataset = {item["label"] for item in dataset}
        self.assertEqual(classes_in_dataset, set(EVENT_TYPES))

        valid_provenance_types = {
            "verbatim_published_headline",
            "paraphrase_of_real_event",
            "synthetic",
            "unverified",
        }

        for item in dataset:
            self.assertIn("id", item)
            self.assertIn("text", item)
            self.assertIn("label", item)
            self.assertIn("provenance_type", item)
            self.assertIn(item["provenance_type"], valid_provenance_types)
            self.assertTrue(len(item["text"].strip()) > 10)

    def test_evaluation_runner_output_structure(self):
        """Evaluation runner executes deterministically and returns complete metric contract."""
        eval_result = run_evaluation()
        self.assertIsInstance(eval_result, dict)
        self.assertEqual(eval_result["total_examples"], 40)
        self.assertIsInstance(eval_result["accuracy"], float)
        self.assertGreaterEqual(eval_result["accuracy"], 0.0)
        self.assertLessEqual(eval_result["accuracy"], 1.0)
        self.assertIn("macro_precision", eval_result)
        self.assertIn("macro_recall", eval_result)
        self.assertIn("macro_f1", eval_result)
        self.assertIn("provenance_summary", eval_result)
        self.assertIn("verified_subset", eval_result)
        self.assertEqual(len(eval_result["confusion_matrix"]), 10)
        self.assertEqual(len(eval_result["per_class"]), 10)


if __name__ == "__main__":
    unittest.main()
