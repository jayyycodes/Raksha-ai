"""
Automated unit tests for engine/embeddings.py.

Tests:
1. Model lazy loading
2. Model caching across multiple calls
3. Correct model name (sentence-transformers/all-mpnet-base-v2)
4. 768-dimensional output
5. Output values are standard Python floats
6. Empty and whitespace-only input validation
7. Incorrect embedding dimension validation
8. Model-loading failure handling
9. Inference failure handling
10. Missing dependency handling
11. Cache invalidation
12. Invalid model name validation (None, empty, whitespace, non-string)
13. Non-convertible model output handling (non-iterable, non-numeric, broken tolist)
14. Non-finite vector value rejection (NaN, +Inf, -Inf)

All tests are deterministic and mocked without downloading real models.
"""
import unittest
from unittest.mock import MagicMock, patch

from engine.embeddings import (
    DEFAULT_MODEL,
    EMBEDDING_DIM,
    DependencyError,
    InferenceError,
    ModelLoadError,
    clear_embedding_cache,
    generate_embedding,
    get_cached_models,
)


class TestEmbeddingModelSelection(unittest.TestCase):
    """Test model selection and dimensional configuration."""

    def test_default_model_is_all_mpnet_base_v2(self):
        """Default model must be all-mpnet-base-v2 to match VECTOR(768) in schema.sql."""
        self.assertEqual(DEFAULT_MODEL, "sentence-transformers/all-mpnet-base-v2")

    def test_embedding_dim_is_768(self):
        """EMBEDDING_DIM constant must be exactly 768."""
        self.assertEqual(EMBEDDING_DIM, 768)


class TestEmbeddingLazyLoadingAndCaching(unittest.TestCase):
    """Test lazy loading and thread-safe caching of embedding models."""

    def setUp(self):
        clear_embedding_cache()
        self.mock_model = MagicMock()
        self.mock_model.encode.return_value = [0.1] * 768

    def test_model_is_lazily_loaded_on_first_call(self):
        """Model is not loaded until generate_embedding is called."""
        self.assertEqual(len(get_cached_models()), 0)

        with patch("engine.embeddings._load_model", return_value=self.mock_model) as loader:
            vector = generate_embedding("Indian Army deployed at border")
            self.assertEqual(loader.call_count, 1)
            loader.assert_called_once_with(DEFAULT_MODEL)
            self.assertEqual(len(vector), 768)
            self.assertIn(DEFAULT_MODEL, get_cached_models())

    def test_model_is_cached_across_repeated_calls(self):
        """Subsequent embedding calls reuse cached model without reloading."""
        with patch("engine.embeddings._load_model", return_value=self.mock_model) as loader:
            res1 = generate_embedding("First headline")
            res2 = generate_embedding("Second headline")
            res3 = generate_embedding("Third headline")

            self.assertEqual(loader.call_count, 1)
            self.assertEqual(len(res1), 768)
            self.assertEqual(len(res2), 768)
            self.assertEqual(len(res3), 768)

    def test_clear_embedding_cache_evicts_models(self):
        """clear_embedding_cache() purges all loaded models from memory."""
        with patch("engine.embeddings._load_model", return_value=self.mock_model):
            generate_embedding("Sample text")
            self.assertEqual(len(get_cached_models()), 1)

            clear_embedding_cache()
            self.assertEqual(len(get_cached_models()), 0)


class TestEmbeddingOutputFormatAndValidation(unittest.TestCase):
    """Test output vector format, types, and dimension validation."""

    def setUp(self):
        clear_embedding_cache()

    def test_768_dimensional_output(self):
        """Generated embedding vector has exactly 768 elements."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.05 * i for i in range(768)]

        with patch("engine.embeddings._load_model", return_value=mock_model):
            vector = generate_embedding("BrahMos missile test conducted successfully")
            self.assertEqual(len(vector), 768)

    def test_output_values_are_python_floats(self):
        """All vector elements are native Python float instances."""
        mock_model = MagicMock()
        # Simulate numpy float32 or integer return from model
        mock_model.encode.return_value = [1] * 768

        with patch("engine.embeddings._load_model", return_value=mock_model):
            vector = generate_embedding("Naval exercise in Indian Ocean")
            self.assertEqual(len(vector), 768)
            for val in vector:
                self.assertIsInstance(val, float)
                self.assertEqual(val, 1.0)

    def test_numpy_array_conversion(self):
        """Output with a .tolist() method (numpy/torch) is converted to Python floats."""
        class MockNumpyArray:
            def tolist(self):
                return [0.123] * 768

        mock_model = MagicMock()
        mock_model.encode.return_value = MockNumpyArray()

        with patch("engine.embeddings._load_model", return_value=mock_model):
            vector = generate_embedding("Air Force squadron movement")
            self.assertEqual(len(vector), 768)
            self.assertIsInstance(vector, list)
            self.assertIsInstance(vector[0], float)

    def test_dimension_mismatch_raises_value_error(self):
        """If a model returns 384 dimensions (e.g. all-MiniLM-L6-v2), raise ValueError."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.1] * 384  # 384 != 768

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(ValueError) as ctx:
                generate_embedding("Short dimensional output test")
            self.assertIn("dimension mismatch", str(ctx.exception))
            self.assertIn("expected 768, got 384", str(ctx.exception))

    def test_nan_in_vector_raises_value_error(self):
        """Vector containing NaN raises ValueError."""
        mock_model = MagicMock()
        values = [0.1] * 768
        values[42] = float("nan")
        mock_model.encode.return_value = values

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(ValueError) as ctx:
                generate_embedding("Text producing NaN embedding")
            self.assertIn("non-finite value", str(ctx.exception))
            self.assertIn("nan", str(ctx.exception).lower())

    def test_positive_inf_in_vector_raises_value_error(self):
        """Vector containing +Infinity raises ValueError."""
        mock_model = MagicMock()
        values = [0.1] * 768
        values[100] = float("inf")
        mock_model.encode.return_value = values

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(ValueError) as ctx:
                generate_embedding("Text producing +Inf embedding")
            self.assertIn("non-finite value", str(ctx.exception))
            self.assertIn("inf", str(ctx.exception).lower())

    def test_negative_inf_in_vector_raises_value_error(self):
        """Vector containing -Infinity raises ValueError."""
        mock_model = MagicMock()
        values = [0.1] * 768
        values[767] = float("-inf")
        mock_model.encode.return_value = values

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(ValueError) as ctx:
                generate_embedding("Text producing -Inf embedding")
            self.assertIn("non-finite value", str(ctx.exception))
            self.assertIn("-inf", str(ctx.exception).lower())


class TestEmbeddingInputValidation(unittest.TestCase):
    """Test validation of empty, whitespace, and invalid text inputs and model names."""

    def setUp(self):
        clear_embedding_cache()

    def test_empty_string_raises_value_error(self):
        """Empty string input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("")
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_whitespace_only_string_raises_value_error(self):
        """Whitespace-only string input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("   \n\t  ")
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_none_input_raises_value_error(self):
        """None input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding(None)
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_non_string_input_raises_value_error(self):
        """Non-string input (e.g. integer, dict) raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding(12345)
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_empty_model_name_raises_value_error(self):
        """Empty model_name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("Sample text", model_name="")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

    def test_whitespace_model_name_raises_value_error(self):
        """Whitespace-only model_name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("Sample text", model_name="   \t\n  ")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

    def test_none_model_name_raises_value_error(self):
        """None model_name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("Sample text", model_name=None)
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

    def test_non_string_model_name_raises_value_error(self):
        """Non-string model_name (int, list, bool) raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_embedding("Sample text", model_name=123)
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            generate_embedding("Sample text", model_name=True)
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))


class TestEmbeddingFailureModes(unittest.TestCase):
    """Test error handling for missing dependencies, model load, inference, and conversion failures."""

    def setUp(self):
        clear_embedding_cache()

    def test_missing_dependency_raises_dependency_error(self):
        """When sentence_transformers is not installed, DependencyError is raised."""
        with patch.dict("sys.modules", {"sentence_transformers": None}):
            with self.assertRaises(DependencyError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("sentence-transformers", str(ctx.exception))

    def test_model_load_failure_raises_model_load_error(self):
        """When SentenceTransformer fails to load or download, ModelLoadError is raised."""
        with patch(
            "engine.embeddings._load_model",
            side_effect=ModelLoadError("Connection timed out downloading model weights"),
        ):
            with self.assertRaises(ModelLoadError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("timed out", str(ctx.exception))

    def test_inference_failure_raises_inference_error(self):
        """When model.encode() fails during inference, InferenceError is raised."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("CUDA out of memory")

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(InferenceError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("CUDA out of memory", str(ctx.exception))

    def test_non_iterable_model_output_raises_inference_error(self):
        """When model.encode() returns an unconvertible non-iterable object, InferenceError is raised."""
        mock_model = MagicMock()
        mock_model.encode.return_value = 12345  # integer has no .tolist() and is not iterable

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(InferenceError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("Failed to convert embedding output structure", str(ctx.exception))

    def test_non_numeric_elements_in_output_raises_inference_error(self):
        """When model output contains elements that cannot be converted to float, InferenceError is raised."""
        mock_model = MagicMock()
        mock_model.encode.return_value = ["not_a_float"] * 768

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(InferenceError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("Failed to convert embedding output values to float", str(ctx.exception))

    def test_tolist_exception_raises_inference_error(self):
        """When .tolist() on model output raises an error, InferenceError is raised."""
        mock_model = MagicMock()
        broken_output = MagicMock()
        broken_output.tolist.side_effect = RuntimeError("Corrupted tensor memory")
        mock_model.encode.return_value = broken_output

        with patch("engine.embeddings._load_model", return_value=mock_model):
            with self.assertRaises(InferenceError) as ctx:
                generate_embedding("Test headline")
            self.assertIn("Failed to convert embedding output structure", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
