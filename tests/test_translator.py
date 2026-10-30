"""
Automated unit tests for engine/translator.py.

Tests:
1. Missing dependencies
2. Model-loading failure
3. Inference failure
4. Caching and cache invalidation
5. Concurrent multi-threaded access
6. Long text and token-aware chunking
7. Unsupported languages (source and target)
8. Skipped translations (English source, empty/None text)
9. Backwards compatibility with standard str operations

Uses the exact public signature: translate(text, source_lang, target_lang="en")
Runs with both `python -m unittest tests/test_translator.py` and `pytest tests/test_translator.py`.
"""
import concurrent.futures
import threading
import unittest
from unittest.mock import MagicMock, patch

from engine.translator import (
    DependencyError,
    InferenceError,
    MAX_CHUNK_TOKENS,
    ModelLoadError,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_SUCCESS,
    SUPPORTED_MODELS,
    TranslationResult,
    UnsupportedLanguageError,
    _chunk_text,
    _count_tokens,
    _load_model_and_tokenizer,
    _split_long_sentence,
    clear_model_cache,
    get_cached_languages,
    translate,
)


class TestTranslatorMissingDependencies(unittest.TestCase):
    """Test behavior when NLP packages (transformers, torch) are missing."""

    def setUp(self):
        clear_model_cache()

    def test_missing_dependencies_returns_failed_result(self):
        """When dependencies are missing, return failed result with error."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            side_effect=DependencyError("No module named 'transformers'"),
        ):
            res = translate("नमस्ते दुनिया", "hi")
            self.assertTrue(res.is_failed)
            self.assertFalse(res.is_success)
            self.assertEqual(res.status, STATUS_FAILED)
            self.assertIn("transformers", res.error)
            self.assertEqual(str(res), "नमस्ते दुनिया")

    def test_missing_dependencies_loader_raises_internally(self):
        """Internal loader raises DependencyError when imports fail."""
        with patch.dict("sys.modules", {"transformers": None}):
            with self.assertRaises(DependencyError):
                _load_model_and_tokenizer("Helsinki-NLP/opus-mt-hi-en")


class TestTranslatorModelLoadFailure(unittest.TestCase):
    """Test behavior when model loading or downloading fails."""

    def setUp(self):
        clear_model_cache()

    def test_model_load_failure_returns_failed_result(self):
        """Model download/initialization failure returns failed status."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            side_effect=ModelLoadError("HuggingFace connection timed out"),
        ):
            res = translate("سلام دنیا", "ur")
            self.assertTrue(res.is_failed)
            self.assertEqual(res.status, STATUS_FAILED)
            self.assertIn("timed out", res.error)
            self.assertEqual(str(res), "سلام دنیا")

    def test_corrupt_model_load_captured_in_result(self):
        """Model weight corruption is caught and reflected in result metadata."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            side_effect=ModelLoadError("Model weights corrupted"),
        ):
            res = translate("سلام دنیا", "ur")
            self.assertTrue(res.is_failed)
            self.assertEqual(res.status, STATUS_FAILED)
            self.assertIn("Model weights corrupted", res.error)


class TestTranslatorInferenceFailure(unittest.TestCase):
    """Test behavior when translation generation fails during runtime."""

    def setUp(self):
        clear_model_cache()
        self.mock_tok = MagicMock()
        self.mock_tok.encode = lambda text, add_special_tokens=False: [1, 2, 3]
        self.mock_tok.decode = lambda ids, skip_special_tokens=True: "chunk"
        self.mock_tok.return_value = {"input_ids": [1, 2, 3]}

        self.mock_model = MagicMock()
        self.mock_model.device = "cpu"
        self.mock_model.generate.side_effect = RuntimeError("CUDA out of memory")

    def test_inference_failure_returns_failed_result(self):
        """Inference error returns failed status and preserves input text."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate("你好世界", "zh")
            self.assertTrue(res.is_failed)
            self.assertEqual(res.status, STATUS_FAILED)
            self.assertIn("CUDA out of memory", res.error)
            self.assertEqual(str(res), "你好世界")

    def test_inference_failure_captures_error_description(self):
        """Inference error description is properly captured in result.error."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate("你好世界", "zh")
            self.assertTrue(res.is_failed)
            self.assertIsNotNone(res.error)
            self.assertIn("CUDA out of memory", res.error)


class TestTranslatorCaching(unittest.TestCase):
    """Test lazy loading, model caching, and cache invalidation."""

    def setUp(self):
        clear_model_cache()
        self.mock_tok = MagicMock()
        self.mock_tok.encode = lambda text, add_special_tokens=False: [1, 2, 3]
        self.mock_tok.decode = lambda ids, skip_special_tokens=True: "Hello world"
        self.mock_tok.return_value = {"input_ids": [1, 2, 3]}

        self.mock_model = MagicMock()
        self.mock_model.device = "cpu"
        self.mock_model.generate.return_value = [[1, 2, 3]]

    def test_models_are_cached_per_language(self):
        """Models are loaded once per language and reused across translation calls."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ) as loader:
            # 1. Translate Hindi first time -> loader called
            res1 = translate("नमस्ते", "hi")
            self.assertTrue(res1.is_success)
            self.assertEqual(loader.call_count, 1)
            self.assertIn("hi", get_cached_languages())

            # 2. Translate Hindi second time -> cache used, loader count remains 1
            res2 = translate("दूसरा वाक्य", "hi")
            self.assertTrue(res2.is_success)
            self.assertEqual(loader.call_count, 1)

            # 3. Translate Chinese -> loader called for 'zh', loader count becomes 2
            res3 = translate("你好", "zh")
            self.assertTrue(res3.is_success)
            self.assertEqual(loader.call_count, 2)
            self.assertSetEqual(set(get_cached_languages()), {"hi", "zh"})

    def test_clear_model_cache_evicts_loaded_models(self):
        """clear_model_cache() removes all cached models from memory."""
        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            translate("नमस्ते", "hi")
            self.assertEqual(len(get_cached_languages()), 1)

            clear_model_cache()
            self.assertEqual(len(get_cached_languages()), 0)


class TestTranslatorConcurrentAccess(unittest.TestCase):
    """Test thread-safety under heavy concurrent multi-threaded requests."""

    def setUp(self):
        clear_model_cache()

    def test_concurrent_translation_threads(self):
        """Multiple concurrent threads must not cause race conditions or corrupt cache."""
        mock_tok = MagicMock()
        mock_tok.encode = lambda text, add_special_tokens=False: [1, 2]
        mock_tok.decode = lambda ids, skip_special_tokens=True: "translated"
        mock_tok.return_value = {"input_ids": [1, 2]}

        mock_model = MagicMock()
        mock_model.device = "cpu"
        mock_model.generate.return_value = [[1, 2]]

        languages = ["hi", "ur", "zh"] * 8  # 24 concurrent requests across 3 languages

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(mock_tok, mock_model),
        ) as loader:
            def worker(lang: str) -> TranslationResult:
                return translate(f"sample text in {lang}", lang)

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(worker, languages))

            # All 24 calls must succeed
            for res in results:
                self.assertTrue(res.is_success)
                self.assertEqual(str(res), "translated")

            # Exactly 3 loads should have happened (one per unique language: hi, ur, zh)
            self.assertEqual(loader.call_count, 3)
            self.assertEqual(set(get_cached_languages()), {"hi", "ur", "zh"})


class TestTranslatorLongTextChunking(unittest.TestCase):
    """Test token-aware chunking for long articles."""

    def setUp(self):
        self.mock_tok = MagicMock()
        # Realistic token count: character count for CJK scripts, whitespace-delimited words otherwise
        def mock_encode(text, add_special_tokens=False):
            if any("\u4e00" <= c <= "\u9fff" for c in text):
                return list(range(len([c for c in text if not c.isspace()])))
            return list(range(len(text.split())))

        self.mock_tok.encode = mock_encode
        self.mock_tok.decode = lambda ids, skip_special_tokens=True: f"chunk_{len(ids)}"
        self.mock_tok.return_value = {"input_ids": [1]}

        self.mock_model = MagicMock()
        self.mock_model.device = "cpu"
        self.mock_model.generate.return_value = [[1]]

    def test_hindi_sentence_boundary_chunking(self):
        """Hindi danda (।) properly splits sentences and groups them into chunks."""
        text = "पहला वाक्य। दूसरा वाक्य। तीसरा वाक्य। चौथा वाक्य।"
        chunks = _chunk_text(text, self.mock_tok, max_tokens=4)
        self.assertTrue(len(chunks) >= 2)

    def test_chinese_punctuation_chunking(self):
        """Chinese full stop (。) properly splits sentences."""
        text = "北京是中国的首都。上海是一个经济中心。广州是一个南方大城市。"
        chunks = _chunk_text(text, self.mock_tok, max_tokens=15)
        self.assertTrue(len(chunks) >= 2)

    def test_urdu_punctuation_chunking(self):
        """Urdu full stop (۔) properly splits sentences."""
        text = "یہ پہلا جملہ ہے۔ یہ دوسرا جملہ ہے۔ یہ تیسرا جملہ ہے۔"
        chunks = _chunk_text(text, self.mock_tok, max_tokens=5)
        self.assertTrue(len(chunks) >= 2)

    def test_long_run_on_sentence_subchunking(self):
        """A single sentence exceeding max_tokens is safely sliced by tokens."""
        long_sentence = "token " * 100
        chunks = _chunk_text(long_sentence, self.mock_tok, max_tokens=20)
        self.assertEqual(len(chunks), 5)

    def test_full_long_text_translation_joins_chunks(self):
        """Long article chunks are all translated and joined with spaces."""
        clear_model_cache()
        text = "पहला बड़ा पैराग्राफ। दूसरा बड़ा पैराग्राफ। तीसरा बड़ा पैराग्राफ।"

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate(text, "hi")
            self.assertTrue(res.is_success)
            self.assertIn("chunk_", str(res))

    def test_multiple_paragraphs_preserved(self):
        """Paragraph boundaries (\n\n) are preserved in output and not flattened."""
        clear_model_cache()
        text = "पहला पैराग्राफ वाक्य 1।\n\nदूसरा पैराग्राफ वाक्य 2।"

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate(text, "hi")
            self.assertTrue(res.is_success)
            self.assertIn("\n\n", str(res))
            paragraphs = str(res).split("\n\n")
            self.assertEqual(len(paragraphs), 2)

    def test_empty_paragraphs_handled_cleanly(self):
        """Extra or empty paragraphs are cleanly normalized without breaking reassembly."""
        clear_model_cache()
        text = "\n\nपहला पैराग्राफ वाक्य।\n\n\n\nदूसरा पैराग्राफ वाक्य।\n\n"

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate(text, "hi")
            self.assertTrue(res.is_success)
            self.assertIn("\n\n", str(res))
            paragraphs = str(res).split("\n\n")
            self.assertEqual(len(paragraphs), 2)

    def test_single_paragraph_no_stray_newlines(self):
        """Normal single-paragraph input produces clean translation without stray paragraph breaks."""
        clear_model_cache()
        text = "पहला वाक्य। दूसरा वाक्य।"

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(self.mock_tok, self.mock_model),
        ):
            res = translate(text, "hi")
            self.assertTrue(res.is_success)
            self.assertNotIn("\n\n", str(res))


class TestTranslatorUnsupportedLanguages(unittest.TestCase):
    """Test handling of unsupported source and target languages."""

    def test_en_to_fr_fails_unsupported_target(self):
        """en -> fr fails with unsupported target error (not marked skipped)."""
        res = translate("Hello world", "en", target_lang="fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported target language 'fr'", res.error)

    def test_fr_to_fr_fails_unsupported_target(self):
        """fr -> fr fails with unsupported target error (not marked skipped)."""
        res = translate("Bonjour tout le monde", "fr", target_lang="fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported target language 'fr'", res.error)

    def test_fr_to_en_fails_unsupported_source(self):
        """fr -> en fails with unsupported source error."""
        res = translate("Bonjour tout le monde", "fr", target_lang="en")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported source language 'fr'", res.error)

    def test_hi_to_en_successful_mocked(self):
        """hi -> en successfully translates using a mocked model."""
        clear_model_cache()
        mock_tok = MagicMock()
        mock_tok.encode = lambda text, add_special_tokens=False: [1, 2]
        mock_tok.decode = lambda ids, skip_special_tokens=True: "Hello India"
        mock_tok.return_value = {"input_ids": [1, 2]}

        mock_model = MagicMock()
        mock_model.device = "cpu"
        mock_model.generate.return_value = [[1, 2]]

        with patch(
            "engine.translator._load_model_and_tokenizer",
            return_value=(mock_tok, mock_model),
        ):
            res = translate("नमस्ते भारत", "hi", target_lang="en")
            self.assertTrue(res.is_success)
            self.assertFalse(res.is_failed)
            self.assertEqual(res.status, STATUS_SUCCESS)
            self.assertEqual(str(res), "Hello India")

    def test_unsupported_source_language_returns_failed_result(self):
        """Unsupported source language returns failed status."""
        res = translate("Bonjour tout le monde", "fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported source language 'fr'", res.error)
        self.assertEqual(str(res), "Bonjour tout le monde")

    def test_unsupported_source_language_error_message(self):
        """Unsupported source language error message specifies valid language codes."""
        res = translate("Bonjour", "fr")
        self.assertTrue(res.is_failed)
        for expected_lang in ["ur", "zh", "hi"]:
            self.assertIn(expected_lang, res.error)

    def test_unsupported_target_language_returns_failed_result(self):
        """Unsupported target language returns failed status."""
        res = translate("नमस्ते", "hi", target_lang="es")
        self.assertTrue(res.is_failed)
        self.assertIn("Unsupported target language 'es'", res.error)

    def test_unsupported_target_language_error_message(self):
        """Unsupported target language error message specifies English requirement."""
        res = translate("नमस्ते", "hi", target_lang="es")
        self.assertTrue(res.is_failed)
        self.assertIn("English ('en')", res.error)


class TestTranslatorSkippedTranslations(unittest.TestCase):
    """Test cases where translation is deliberately skipped."""

    def test_en_to_en_is_skipped(self):
        """en -> en is cleanly skipped and returns original text."""
        res = translate("Indian Army deployed near border", "en", target_lang="en")
        self.assertTrue(res.is_skipped)
        self.assertFalse(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_SKIPPED)
        self.assertEqual(str(res), "Indian Army deployed near border")

    def test_english_source_is_skipped(self):
        """English text is marked as skipped and returns original text."""
        res = translate("Indian Army deployed near border", "en")
        self.assertTrue(res.is_skipped)
        self.assertFalse(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertEqual(res.status, STATUS_SKIPPED)
        self.assertEqual(str(res), "Indian Army deployed near border")

    def test_case_insensitive_english_is_skipped(self):
        """'EN' or ' en ' source is also skipped."""
        res = translate("Indian Navy exercise", "  EN ")
        self.assertTrue(res.is_skipped)

    def test_matching_source_and_target_is_skipped(self):
        """When source_lang equals target_lang, translation is skipped."""
        res = translate("Same language", "en", target_lang="en")
        self.assertTrue(res.is_skipped)

    def test_empty_input_is_skipped(self):
        """Empty or whitespace text is safely skipped."""
        self.assertTrue(translate("", "hi").is_skipped)
        self.assertTrue(translate("   ", "hi").is_skipped)
        self.assertTrue(translate(None, "hi").is_skipped)


class TestTranslationResultBackwardsCompatibility(unittest.TestCase):
    """Verify TranslationResult supports standard Python string operations as a str subclass."""

    def test_string_methods_and_type(self):
        res = TranslationResult("translated text", status=STATUS_SUCCESS, source_lang="hi")
        self.assertIsInstance(res, str)
        self.assertEqual(res.upper(), "TRANSLATED TEXT")
        self.assertEqual(len(res), 15)
        self.assertTrue(res.startswith("translated"))
        self.assertEqual(f"Result: {res}", "Result: translated text")


class TestEmptyInputLanguageValidationPolicy(unittest.TestCase):
    """
    Test empty-input and language-validation order policy:
    Language validation strictly precedes text emptiness checks.
    An unsupported target or unsupported non-English source must return
    STATUS_FAILED, even when input text is empty, None, or whitespace-only.
    """

    def test_empty_input_with_unsupported_target_fails(self):
        """Empty text with unsupported target must fail (not skipped)."""
        res = translate("", "hi", target_lang="fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_skipped)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported target language 'fr'", res.error)

    def test_none_input_with_unsupported_target_fails(self):
        """None text with unsupported target must fail (not skipped)."""
        res = translate(None, "hi", target_lang="fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_skipped)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported target language 'fr'", res.error)

    def test_whitespace_input_with_unsupported_target_fails(self):
        """Whitespace text with unsupported target must fail (not skipped)."""
        res = translate("   \n\t  ", "hi", target_lang="fr")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_skipped)
        self.assertEqual(res.status, STATUS_FAILED)

    def test_empty_input_with_unsupported_source_fails(self):
        """Empty text with unsupported source must fail (not skipped)."""
        res = translate("", "fr", target_lang="en")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_skipped)
        self.assertEqual(res.status, STATUS_FAILED)
        self.assertIn("Unsupported source language 'fr'", res.error)

    def test_none_input_with_unsupported_source_fails(self):
        """None text with unsupported source must fail (not skipped)."""
        res = translate(None, "fr", target_lang="en")
        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_skipped)
        self.assertEqual(res.status, STATUS_FAILED)

    def test_empty_input_with_valid_languages_is_skipped(self):
        """Empty text with valid source and target is cleanly skipped."""
        res = translate("", "hi", target_lang="en")
        self.assertTrue(res.is_skipped)
        self.assertFalse(res.is_failed)
        self.assertEqual(res.status, STATUS_SKIPPED)

    def test_none_input_with_valid_languages_is_skipped(self):
        """None text with valid source and target is cleanly skipped."""
        res = translate(None, "hi", target_lang="en")
        self.assertTrue(res.is_skipped)
        self.assertFalse(res.is_failed)
        self.assertEqual(res.status, STATUS_SKIPPED)


class TestCombinedChunkTokenValidation(unittest.TestCase):
    """
    Test token count validation:
    Verifies that complete candidate chunks are re-tokenized after joining sentences,
    and that combined text strictly stays within the configured token budget.
    """

    def test_candidate_chunk_retokenization_enforces_budget(self):
        """
        When individual sentences fit within budget but their combination exceeds it,
        re-tokenizing the candidate chunk prevents overflowing the token budget.
        """
        # Sentence 1 has 3 words, Sentence 2 has 3 words.
        # If max_tokens is 5:
        # Sentence 1 (3 tokens) fits.
        # Candidate "Sentence 1 Sentence 2" (6 tokens) > 5.
        # The candidate must split into separate chunks of <= 5 tokens.
        mock_tok = MagicMock()
        mock_tok.encode = lambda text, add_special_tokens=True: list(range(len(text.split())))
        mock_tok.decode = lambda ids, skip_special_tokens=True: " ".join(f"w{i}" for i in ids)

        text = "word one two. word three four."
        chunks = _chunk_text(text, mock_tok, max_tokens=5)

        self.assertEqual(len(chunks), 2)
        for chunk in chunks:
            token_count = _count_tokens(chunk, mock_tok)
            self.assertLessEqual(token_count, 5)

    def test_combined_token_count_respects_special_tokens(self):
        """
        Token count validation accounts for special tokens (e.g. BOS/EOS)
        added when add_special_tokens=True.
        """
        # A tokenizer where add_special_tokens=True adds 2 special tokens ([BOS], [EOS])
        class SpecialTokenMockTokenizer:
            def encode(self, text, add_special_tokens=True):
                tokens = text.split()
                return [101] + list(range(len(tokens))) + [102] if add_special_tokens else list(range(len(tokens)))

            def decode(self, ids, skip_special_tokens=True):
                filtered = [i for i in ids if i not in (101, 102)]
                return " ".join(f"token_{i}" for i in filtered)

        mock_tok = SpecialTokenMockTokenizer()
        # Budget = 6 tokens.
        # Sentence with 3 words -> encode(add_special_tokens=True) = 3 + 2 = 5 <= 6.
        # Two sentences with 3 words each joined -> 6 words + 2 special = 8 > 6.
        # Candidate re-tokenization must split them.
        text = "alpha beta gamma. delta epsilon zeta."
        chunks = _chunk_text(text, mock_tok, max_tokens=6)

        self.assertEqual(len(chunks), 2)
        for chunk in chunks:
            self.assertLessEqual(_count_tokens(chunk, mock_tok), 6)


class TestLongSentenceSubchunkingVerification(unittest.TestCase):
    """
    Test long-sentence subchunking:
    Verifies that sentences exceeding max_tokens are sliced, decoded, and re-verified
    to strictly stay within the safe token budget (including special tokens),
    and tests that word sequences in tested inputs are retained across subchunks.
    """

    def setUp(self):
        # Deterministic bidirectional mock tokenizer
        words = [f"word{i}" for i in range(200)]
        self.word_to_id = {w: i + 10 for i, w in enumerate(words)}
        self.id_to_word = {i + 10: w for i, w in enumerate(words)}

        class DeterministicTokenizer:
            def __init__(self, parent):
                self.parent = parent

            def encode(self, text, add_special_tokens=False):
                tokens = [self.parent.word_to_id.get(w, 1) for w in text.split()]
                if add_special_tokens:
                    return [101] + tokens + [102]
                return tokens

            def decode(self, ids, skip_special_tokens=True):
                words = [self.parent.id_to_word.get(i, f"w{i}") for i in ids if i not in (101, 102)]
                return " ".join(words)

        self.tokenizer = DeterministicTokenizer(self)

    def test_long_sentence_subchunking_preserves_content_and_budget(self):
        """Long sentence is subchunked with every chunk verified <= budget and tested words retained."""
        original_words = [f"word{i}" for i in range(50)]
        long_sentence = " ".join(original_words)
        max_budget = 15

        chunks = _chunk_text(long_sentence, self.tokenizer, max_tokens=max_budget)

        # 1. More than 1 chunk produced
        self.assertTrue(len(chunks) > 1)

        # 2. Every single subchunk strictly respects the token budget with special tokens
        for chunk in chunks:
            tokens_in_chunk = _count_tokens(chunk, self.tokenizer)
            self.assertLessEqual(tokens_in_chunk, max_budget)

        # 3. All non-whitespace content in tested sentence is preserved across slices
        reassembled_words = (" ".join(chunks)).split()
        self.assertEqual(reassembled_words, original_words)

    def test_split_long_sentence_shrinks_slice_if_decoded_exceeds_budget(self):
        """_split_long_sentence dynamically checks token count after decoding."""
        original_words = [f"word{i}" for i in range(30)]
        sentence = " ".join(original_words)

        subchunks = _split_long_sentence(sentence, self.tokenizer, max_tokens=10)
        self.assertTrue(len(subchunks) >= 3)

        for sc in subchunks:
            self.assertLessEqual(_count_tokens(sc, self.tokenizer), 10)

        reassembled = (" ".join(subchunks)).split()
        self.assertEqual(reassembled, original_words)

    def test_split_long_sentence_zero_budget_fails_immediately(self):
        """_split_long_sentence rejects max_tokens=0 immediately with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _split_long_sentence("sample sentence", self.tokenizer, max_tokens=0)
        self.assertIn("must be a positive integer", str(ctx.exception))

    def test_split_long_sentence_negative_budget_fails_immediately(self):
        """_split_long_sentence rejects negative max_tokens immediately with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _split_long_sentence("sample sentence", self.tokenizer, max_tokens=-5)
        self.assertIn("must be a positive integer", str(ctx.exception))

    def test_chunk_text_zero_budget_fails_immediately(self):
        """_chunk_text rejects max_tokens=0 immediately with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _chunk_text("sample sentence", self.tokenizer, max_tokens=0)
        self.assertIn("must be a positive integer", str(ctx.exception))

    def test_chunk_text_negative_budget_fails_immediately(self):
        """_chunk_text rejects negative max_tokens immediately with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _chunk_text("sample sentence", self.tokenizer, max_tokens=-10)
        self.assertIn("must be a positive integer", str(ctx.exception))

    def test_split_long_sentence_non_integer_budgets_fail_immediately(self):
        """_split_long_sentence rejects float, string, and boolean max_tokens with ValueError."""
        for invalid_budget in [1.5, "10", True, False]:
            with self.subTest(budget=invalid_budget):
                with self.assertRaises(ValueError) as ctx:
                    _split_long_sentence("sample sentence", self.tokenizer, max_tokens=invalid_budget)
                self.assertIn("must be a positive integer", str(ctx.exception))

    def test_chunk_text_non_integer_budgets_fail_immediately(self):
        """_chunk_text rejects float, string, and boolean max_tokens with ValueError."""
        for invalid_budget in [1.5, "10", True, False]:
            with self.subTest(budget=invalid_budget):
                with self.assertRaises(ValueError) as ctx:
                    _chunk_text("sample sentence", self.tokenizer, max_tokens=invalid_budget)
                self.assertIn("must be a positive integer", str(ctx.exception))

    def test_positive_integer_budgets_still_work(self):
        """Confirm standard positive integer budgets continue to work properly."""
        chunks = _chunk_text("word one. word two.", self.tokenizer, max_tokens=10)
        self.assertTrue(len(chunks) >= 1)
        subchunks = _split_long_sentence("word one word two", self.tokenizer, max_tokens=10)
        self.assertTrue(len(subchunks) >= 1)

    def test_single_token_exceeding_budget_raises_clear_exception(self):
        """
        When even the smallest possible slice (1 token) plus special tokens
        exceeds max_tokens, _split_long_sentence must raise a clear ValueError
        rather than appending an oversized chunk or claiming budget compliance.
        """
        class OversizedTokenMock:
            def encode(self, text, add_special_tokens=False):
                tokens = list(range(len(text.split())))
                if add_special_tokens:
                    # 4 special tokens added
                    return [101, 102] + tokens + [103, 104]
                return tokens

            def decode(self, ids, skip_special_tokens=True):
                return "word"

        mock_tok = OversizedTokenMock()
        # Even a single word has 1 + 4 = 5 tokens with special tokens.
        # Budget = 3 -> even smallest 1-token slice will have 5 tokens > 3.
        with self.assertRaises(ValueError) as ctx:
            _split_long_sentence("word1 word2 word3", mock_tok, max_tokens=3)
        self.assertIn("exceeds token budget", str(ctx.exception))

    def test_zero_content_tokens_exceeding_budget_raises_value_error(self):
        """
        When a non-empty sentence produces zero content token IDs (e.g. unmapped characters)
        but its special tokens exceed max_tokens, _split_long_sentence must raise a ValueError
        rather than silently returning an empty list.
        """
        class ZeroContentTokensMock:
            def encode(self, text, add_special_tokens=False):
                if add_special_tokens:
                    return [101, 102]  # 2 special tokens
                return []  # 0 content tokens

            def decode(self, ids, skip_special_tokens=True):
                return ""

        mock_tok = ZeroContentTokensMock()
        # Budget = 1 -> _count_tokens is 2 > 1. num_tokens is 0.
        with self.assertRaises(ValueError) as ctx:
            _split_long_sentence("unmapped content", mock_tok, max_tokens=1)
        self.assertIn("zero content token IDs", str(ctx.exception))


class TestSkippedTranslationContract(unittest.TestCase):
    """
    Test skipped-translation contract:
    - English source articles retain original text for downstream NLP analysis.
    - A skipped translation must never be interpreted as an instruction to discard the article.
    - Failed translations must never be treated as valid English.
    """

    def test_skipped_english_retains_original_text_for_downstream_nlp(self):
        """Skipped English translation preserves text on str(result) and original_text."""
        english_article = "Indian Navy participates in multinational maritime exercise."
        res = translate(english_article, "en", target_lang="en")

        self.assertTrue(res.is_skipped)
        self.assertFalse(res.is_failed)
        self.assertFalse(res.is_success)

        # Retains full English text for downstream analysis
        self.assertEqual(str(res), english_article)
        self.assertEqual(res.original_text, english_article)

        # Standard pipeline caller logic:
        # Both success and skipped yield valid English text for downstream NLP models
        downstream_text = str(res) if (res.is_success or res.is_skipped) else None
        self.assertEqual(downstream_text, english_article)

    def test_failed_translation_contract_prevents_treating_as_english(self):
        """Failed non-English translation has is_failed=True and must not be treated as English."""
        urdu_article = "یہ ایک غیر انگریزی خبر ہے۔"
        res = translate(urdu_article, "fr", target_lang="en")  # Unsupported source

        self.assertTrue(res.is_failed)
        self.assertFalse(res.is_success)
        self.assertFalse(res.is_skipped)
        self.assertIsNotNone(res.error)

        # Downstream pipeline caller logic: failed translation yields None or error routing
        downstream_text = str(res) if (res.is_success or res.is_skipped) else None
        self.assertIsNone(downstream_text)


if __name__ == "__main__":
    unittest.main()
