"""
Comprehensive tests for Multilingual Indic NLP (Phase 2).
Floor 2 — Language & Knowledge Agents
Owner: Ary
Stage: 3 Production Implementation

Covers:
- Tier 1: Unit tests for script detection, phonetic transliteration, structured person mentions.
- Tier 2: Mocked translation integration, proper-noun preservation, unsupported-language passthrough.
- Tier 3: Live MarianMT translation tests (conditionally skipped in offline test suite).
- Tier 4: Indic NLP evaluation harness integration.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from agents.resolution.agent import (
    COMMON_ENGLISH_WORDS,
    ResolutionAgent,
    normalize_indic_romanization_variants,
    normalize_indic_transliteration,
)
from agents.translation.agent import TranslationAgent
from common.schemas.articles import ArticleIn
from engine.ner import (
    extract_entities,
    extract_entities_with_spans,
    parse_structured_person_mention,
)
from engine.translator import (
    TranslationResult,
    protect_indic_proper_nouns,
    restore_indic_proper_nouns,
)
from evaluation.harness import format_indic_markdown_report, run_indic_nlp_eval
from pipeline.upload_nlp import UploadedDocumentNLPPipeline as UploadNLPPipeline, detect_document_language


class TestTier1IndicNLPUnit(unittest.TestCase):
    """Tier 1: Pure Python unit tests without external model weights."""

    def test_unicode_script_and_language_detection(self):
        """Test accurate script-aware language detection across South Asian languages."""
        # Hindi (Devanagari)
        hi_text = "भारतीय वायु सेना ने लद्दाख में लड़ाकू विमान तैनात किए।"
        lang, conf, is_mixed = detect_document_language(hi_text)
        self.assertEqual(lang, "hi")
        self.assertFalse(is_mixed)

        # Urdu (Perso-Arabic)
        ur_text = "پاک فوج کے ترجمان نے راولپنڈی میں پریس کانفرنس کی۔"
        lang, conf, is_mixed = detect_document_language(ur_text)
        self.assertEqual(lang, "ur")
        self.assertFalse(is_mixed)

        # Punjabi (Gurmukhi)
        pa_text = "ਸੀਮਾ ਸੁਰੱਖਿਆ ਬਲ ਨੇ ਅੰਮ੍ਰਿਤਸਰ ਸਰਹੱਦ ਨੇੜੇ ਡਰੋਨ ਨੂੰ ਡੇਗ ਦਿੱਤਾ।"
        lang, conf, is_mixed = detect_document_language(pa_text)
        self.assertEqual(lang, "pa")
        self.assertFalse(is_mixed)

        # Bengali (Eastern Nagari)
        bn_text = "ভারতীয় নৌসেনা বঙ্গোপসাগরে নতুন যুদ্ধজাহাজের মহড়া সম্পন্ন করেছে।"
        lang, conf, is_mixed = detect_document_language(bn_text)
        self.assertEqual(lang, "bn")
        self.assertFalse(is_mixed)

        # English / Latin
        en_text = "Indian Army conducted high altitude tactical training exercises in Ladakh."
        lang, conf, is_mixed = detect_document_language(en_text)
        self.assertEqual(lang, "en")
        self.assertFalse(is_mixed)

    def test_structured_person_mention_parsing_with_ranks(self):
        """Structured person mention parser extracts military ranks and normalizes names."""
        # Full rank and name
        res = parse_structured_person_mention("Lt Gen Upendra Dwivedi")
        self.assertEqual(res["extracted_rank"], "Lt Gen")
        self.assertEqual(res["normalized_name"], "Upendra Dwivedi")
        self.assertFalse(res["is_ambiguous"])

        # JCO rank
        res_jco = parse_structured_person_mention("Subedar Major Balbir Singh")
        self.assertEqual(res_jco["extracted_rank"], "Subedar Major")
        self.assertEqual(res_jco["normalized_name"], "Balbir Singh")

        # Ambiguous single-token surname with rank
        res_ambig = parse_structured_person_mention("General Singh")
        self.assertEqual(res_ambig["extracted_rank"], "General")
        self.assertEqual(res_ambig["normalized_name"], "Singh")
        self.assertTrue(res_ambig["is_ambiguous"])
        self.assertIn("insufficient specificity", res_ambig["evidence"])

    def test_conservative_person_resolution_guard(self):
        """ResolutionAgent holds ambiguous single-token persons in review_queue rather than auto-merging."""
        agent = ResolutionAgent()

        # Specific person with recognized identity -> auto_link
        res_valid = agent.resolve_entity("Lt Gen Upendra Dwivedi", entity_type_hint="PERSON")
        self.assertEqual(res_valid["action"], "auto_link")
        self.assertEqual(res_valid["canonical_name"], "Upendra Dwivedi")

        # Ambiguous person with rank but single surname -> review_queue
        res_ambig = agent.resolve_entity("General Singh", entity_type_hint="PERSON")
        self.assertEqual(res_ambig["action"], "review_queue")
        self.assertEqual(res_ambig["match_method"], "ambiguous_person_guard")

    def test_indic_romanization_and_phonetic_transliteration(self):
        """Phonetic variants normalize accurately while tracking transformation rules."""
        # Ravalpindi -> rawalpindi
        norm, transformed, rule = normalize_indic_transliteration("Ravalpindi")
        self.assertEqual(norm, "rawalpindi")
        self.assertTrue(transformed)
        self.assertEqual(rule, "phonetic_ravalpindi")

        # Kupwada -> kupwara
        norm, transformed, rule = normalize_indic_transliteration("Kupwada")
        self.assertEqual(norm, "kupwara")
        self.assertTrue(transformed)
        self.assertEqual(rule, "phonetic_kupwada")

        # Syachen -> siachen
        norm, transformed, rule = normalize_indic_transliteration("Syachen")
        self.assertEqual(norm, "siachen")
        self.assertTrue(transformed)
        self.assertEqual(rule, "phonetic_siachen")

        # Akhnur -> akhnoor
        norm, transformed, rule = normalize_indic_transliteration("Akhnur")
        self.assertEqual(norm, "akhnoor")
        self.assertTrue(transformed)
        self.assertEqual(rule, "phonetic_akhnur")

        # Jaish-e-Mohammad -> jaish mohammed
        norm, transformed, rule = normalize_indic_transliteration("Jaish-e-Mohammad")
        self.assertIn("mohammed", norm)
        self.assertTrue(transformed)

    def test_transliteration_safeguards_common_english_words(self):
        """Common English words are strictly guarded from phonetic mutation or false merging."""
        for word in ("west", "punch", "wood", "wing", "forces"):
            norm, transformed, rule = normalize_indic_transliteration(word)
            self.assertEqual(norm, word)
            self.assertFalse(transformed)
            self.assertEqual(rule, "common_word_guard")

    def test_extract_entities_with_spans_exact_character_offsets(self):
        """extract_entities_with_spans guarantees exact Unicode character slicing."""
        text = "भारतीय वायु सेना ने लद्दाख में सुखोई-30MKI लड़ाकू विमान तैनात किए।"
        spans = extract_entities_with_spans(text)
        self.assertGreater(len(spans), 0)
        for s in spans:
            start = s["start_char"]
            end = s["end_char"]
            val = s["entity_value"]
            self.assertEqual(text[start:end], val, f"Span slice mismatch: '{text[start:end]}' != '{val}'")


class TestTier2IndicNLPMockedIntegration(unittest.TestCase):
    """Tier 2: Mocked integration tests for translation and upload NLP."""

    def setUp(self):
        self.pipeline = UploadNLPPipeline()
        self.translation_agent = TranslationAgent()

    @patch("agents.translation.agent.translate")
    def test_translation_agent_proper_noun_preservation(self, mock_translate):
        """Proper nouns in Indic text are preserved and recorded in metadata."""
        mock_result = TranslationResult(
            text="Indian Air Force deployed Sukhoi-30MKI fighters in Ladakh.",
            status="success",
            source_lang="hi",
            target_lang="en",
            error=None,
            original_text="भारतीय वायु सेना ने लद्दाख में सुखोई-30MKI लड़ाकू विमान तैनात किए।",
        )
        mock_translate.return_value = mock_result

        article = ArticleIn(
            id=201,
            title="लद्दाख में सुखोई तैनात",
            content="भारतीय वायु सेना ने लद्दाख में सुखोई-30MKI लड़ाकू विमान तैनात किए।",
            url="https://example.com/hi/201",
            language="hi",
        )
        out = self.translation_agent.run(article)
        self.assertTrue(out["is_translated"])
        self.assertIn("preserved_proper_nouns", out)
        preserved = out["preserved_proper_nouns"]
        surface_tokens = {p["surface_token"] for p in preserved}
        self.assertIn("सुखोई-30MKI", surface_tokens)
        self.assertIn("लद्दाख", surface_tokens)

    def test_unsupported_language_passthrough_punjabi_and_bengali(self):
        """Unsupported Indic languages pass through with 100% text fidelity and explicit warnings."""
        pa_text = "ਸੀਮਾ ਸੁਰੱਖਿਆ ਬਲ ਨੇ ਅੰਮ੍ਰਿਤਸਰ ਸਰਹੱਦ ਨੇੜੇ ਪਾਕਿਸਤਾਨੀ ਡਰੋਨ ਨੂੰ ਗੋਲੀ ਮਾਰ ਕੇ ਡੇਗ ਦਿੱਤਾ।"
        analysis_pa = self.pipeline.process_document(
            content=pa_text,
            filename="punjabi_bulletin.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis_pa.detected_language, "pa")
        self.assertTrue(any("pa" in w and "not supported" in w for w in analysis_pa.warnings))
        # Text is retained intact across chunks
        self.assertEqual(analysis_pa.chunks[0].text, pa_text)

        bn_text = "ভারতীয় নৌসেনা বঙ্গোপসাগরে নতুন যুদ্ধজাহাজের মহড়া সম্পন্ন করেছে।"
        analysis_bn = self.pipeline.process_document(
            content=bn_text,
            filename="bengali_dispatch.txt",
            workspace_id=101,
        )
        self.assertEqual(analysis_bn.detected_language, "bn")
        self.assertTrue(any("bn" in w and "not supported" in w for w in analysis_bn.warnings))
        self.assertEqual(analysis_bn.chunks[0].text, bn_text)


class TestTier3LiveTranslationInference(unittest.TestCase):
    """Tier 3: Actual MarianMT inference tests (environment-guarded)."""

    @unittest.skipIf(
        not os.getenv("RUN_LIVE_TRANSLATION_TESTS"),
        "Live translation model inference skipped in standard offline test suite.",
    )
    def test_live_hindi_translation_inference(self):
        """Live inference test on Helsinki-NLP/opus-mt-hi-en (requires downloaded weights)."""
        from engine.translator import translate
        res = translate("भारतीय सेना ने सियाचिन में गश्त की।", source_lang="hi", target_lang="en")
        self.assertTrue(res.is_success)
        self.assertIn("army", str(res).lower())


class TestTier4IndicNLPEvaluationHarness(unittest.TestCase):
    """Tier 4: Benchmark regression runner integration."""

    def test_indic_nlp_evaluation_harness_integration(self):
        """run_indic_nlp_eval loads indic_nlp_eval.jsonl and computes all required metrics."""
        res = run_indic_nlp_eval()
        self.assertEqual(res["agent_name"], "IndicNLPAgent")
        self.assertEqual(res["benchmark_type"], "initial_regression_benchmark")
        self.assertEqual(res["total_samples"], 36)

        # Assert key performance floors on the initial regression benchmark
        self.assertEqual(res["language_detection_accuracy"], 1.0)
        self.assertGreaterEqual(res["span_level_metrics"]["f1"], 0.90)
        self.assertGreaterEqual(res["canonical_entity_metrics"]["f1"], 0.90)
        self.assertGreaterEqual(res["proper_noun_preservation_rate"], 0.95)
        self.assertEqual(res["transliteration"]["precision"], 1.0)
        self.assertEqual(res["transliteration"]["false_positive_merges"], 0)
        self.assertEqual(res["unsupported_passthrough_fidelity"], 1.0)

        # Formatter test
        md = format_indic_markdown_report(res)
        self.assertIn("Indic NLP Evaluation Report", md)
        self.assertIn("hindi_native", md)
        self.assertIn("romanized_indic", md)


if __name__ == "__main__":
    unittest.main()
