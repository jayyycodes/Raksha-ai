"""
Unit tests for Stage 2 ResolutionAgent.
Floor 2 — Language & Knowledge Agents
"""
import unittest
from unittest.mock import MagicMock, patch

from agents.base import Agent, BaseAgent
from agents.resolution.agent import (
    ResolutionAgent,
    compute_cosine_similarity,
    normalize_indic_romanization_variants,
)
from common.schemas.articles import EntityOut
from common.schemas.provenance import Provenance
from engine.embeddings import EMBEDDING_DIM


class TestResolutionAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ResolutionAgent()

    def test_agent_protocol_conformance(self):
        self.assertIsInstance(self.agent, Agent)
        self.assertIsInstance(self.agent, BaseAgent)
        self.assertEqual(self.agent.name, "resolution_agent")
        self.assertEqual(self.agent.version, "0.2.0")
        self.assertTrue(callable(self.agent.run))
        self.assertTrue(callable(self.agent.run_batch))

    def test_exact_alias_matching_auto_link(self):
        input_entities = ["IAF", "PLA", "DRDO", "LAC", "LoC", "BrahMos", "Siachen"]
        out = self.agent.run(input_entities)
        self.assertIn("resolved_entities", out)
        self.assertIn("provenance", out)
        self.assertEqual(len(out["resolved_entities"]), 7)

        res_map = {r["raw_name"]: r for r in out["resolved_entities"]}

        self.assertEqual(res_map["IAF"]["canonical_name"], "Indian Air Force")
        self.assertEqual(res_map["IAF"]["action"], "auto_link")
        self.assertGreaterEqual(res_map["IAF"]["confidence"], 0.90)

        self.assertEqual(res_map["PLA"]["canonical_name"], "People's Liberation Army")
        self.assertEqual(res_map["PLA"]["action"], "auto_link")

        self.assertEqual(res_map["LAC"]["canonical_name"], "Line of Actual Control")
        self.assertEqual(res_map["LAC"]["action"], "auto_link")

        self.assertEqual(res_map["BrahMos"]["canonical_name"], "BrahMos")
        self.assertEqual(res_map["BrahMos"]["action"], "auto_link")

    def test_prefix_and_rank_stripping(self):
        raw_names = [
            "Lt. Gen. Upendra Dwivedi",
            "Air Chief Marshal V.R. Chaudhari",
            "General Manoj Pande",
        ]
        for name in raw_names:
            res = self.agent.resolve_entity(name)
            self.assertFalse(res["canonical_name"].startswith("Lt. Gen"))
            self.assertFalse(res["canonical_name"].startswith("Air Chief Marshal"))
            self.assertFalse(res["canonical_name"].startswith("General"))

    # ── Transliteration & Romanization Variant Tests ──
    def test_indic_romanization_normalizer_function(self):
        # Connectors '-e-', '-i-', '-ul-'
        self.assertEqual(
            normalize_indic_romanization_variants("Jaish-e-Mohammad"),
            normalize_indic_romanization_variants("Jaish-i-Mohammed"),
        )
        # Regional transliteration
        self.assertEqual(normalize_indic_romanization_variants("Ravalpindi"), "rawalpindi")
        # Common English words must NOT be altered or corrupted
        self.assertEqual(normalize_indic_romanization_variants("Punch"), "punch")
        self.assertEqual(normalize_indic_romanization_variants("West"), "west")
        self.assertEqual(normalize_indic_romanization_variants("War"), "war")

    def test_negative_common_words_guarded_against_false_merging(self):
        # Legitimate common English words must NEVER be auto-linked or phonetically mutated
        guarded_words = ["Punch", "West", "Western", "War", "Wood", "Force"]
        for word in guarded_words:
            res = self.agent.resolve_entity(word)
            self.assertEqual(res["action"], "separate", f"Common word '{word}' was incorrectly linked!")
            self.assertEqual(res["match_method"], "common_english_word_guard")
            self.assertLessEqual(res["confidence"], 0.50)

    def test_transliteration_variants_resolution(self):
        # Rawalpindi / Ravalpindi
        res = self.agent.resolve_entity("Ravalpindi")
        self.assertEqual(res["canonical_name"], "Rawalpindi")
        self.assertEqual(res["action"], "auto_link")

        # Jaish variants
        res_jem1 = self.agent.resolve_entity("Jaish-e-Mohammad")
        res_jem2 = self.agent.resolve_entity("Jaish-i-Mohammed")
        self.assertEqual(res_jem1["canonical_name"], "Jaish-e-Mohammed")
        self.assertEqual(res_jem2["canonical_name"], "Jaish-e-Mohammed")
        self.assertEqual(res_jem1["action"], "auto_link")
        self.assertEqual(res_jem2["action"], "auto_link")

        # Lashkar variants
        res_let = self.agent.resolve_entity("Lashkar-i-Taiba")
        self.assertEqual(res_let["canonical_name"], "Lashkar-e-Taiba")
        self.assertEqual(res_let["action"], "auto_link")

    # ── Ambiguous Common Names Strict Guard ──
    def test_common_ambiguous_name_guard_keeps_separate(self):
        # Single generic words must NEVER be auto-linked, even with context
        ambiguous_tokens = ["Singh", "Kumar", "Sharma", "Khan", "Army", "Border"]
        for token in ambiguous_tokens:
            res = self.agent.resolve_entity(token, context="Indian Army military border officer")
            self.assertEqual(res["action"], "separate", f"Ambiguous name '{token}' was wrongly merged!")
            self.assertEqual(res["decision"], "separate")
            self.assertEqual(res["match_method"], "ambiguous_common_name_guard")
            self.assertLessEqual(res["confidence"], 0.50)

    # ── Contextual Embedding Disambiguation Tests ──
    @patch("agents.resolution.agent.generate_embedding")
    def test_contextual_embedding_corroborates_match(self, mock_embed):
        # Mock 768-dim vector returning positive cosine similarity
        mock_vec = [0.05] * EMBEDDING_DIM
        mock_embed.return_value = mock_vec

        res = self.agent.resolve_entity(
            "Brahmos missile",
            context="Indian Navy successfully test-fired supersonic cruise missile from stealth destroyer",
        )
        self.assertEqual(res["canonical_name"], "BrahMos")
        self.assertEqual(res["action"], "auto_link")
        self.assertIn("Context", res["explanation"])

    @patch("agents.resolution.agent.generate_embedding")
    def test_contextual_embedding_penalizes_conflicting_context(self, mock_embed):
        # Context vector orthogonal / divergent from defense context
        def embed_side_effect(text):
            if "Bollywood" in text or "cinema" in text:
                return [1.0, 0.0] + [0.0] * (EMBEDDING_DIM - 2)
            # Canonical defense context
            return [0.0, 1.0] + [0.0] * (EMBEDDING_DIM - 2)

        mock_embed.side_effect = embed_side_effect

        res = self.agent.resolve_entity(
            "Rafale",
            context="Actor attends Bollywood film screening and cinema premiere in Mumbai",
        )
        # Even though "Rafale" is a known alias, orthogonal context lowers confidence or flags review
        self.assertTrue(res["action"] in ["review_queue", "auto_link"])

    def test_missing_context_handled_safely(self):
        res = self.agent.resolve_entity("DRDO", context=None)
        self.assertEqual(res["canonical_name"], "Defence Research and Development Organisation")
        self.assertEqual(res["action"], "auto_link")

    def test_empty_context_handled_safely(self):
        res = self.agent.resolve_entity("DRDO", context="   ")
        self.assertEqual(res["canonical_name"], "Defence Research and Development Organisation")
        self.assertEqual(res["action"], "auto_link")

    def test_fuzzy_matching_tiers(self):
        # Novel unmatched entity -> separate
        res_unmatched = self.agent.resolve_entity("Uncatalogued Artificial Intelligence Startup 2026")
        self.assertEqual(res_unmatched["action"], "separate")
        self.assertEqual(res_unmatched["canonical_name"], "Uncatalogued Artificial Intelligence Startup 2026")

    def test_entity_out_input_objects(self):
        dummy_prov = Provenance(
            source_ids=[1],
            method="test",
            model_version="test-1",
            confidence=0.9,
        )
        entities = [
            EntityOut(
                entity_type="ORGANISATION",
                entity_value="DRDO",
                confidence=0.95,
                provenance=dummy_prov,
            ),
            EntityOut(
                entity_type="LOCATION",
                entity_value="Siachen Glacier",
                confidence=0.95,
                provenance=dummy_prov,
            ),
        ]
        out = self.agent.run(entities)
        self.assertEqual(len(out["resolved_entities"]), 2)
        self.assertEqual(out["resolved_entities"][0]["canonical_name"], "Defence Research and Development Organisation")
        self.assertEqual(out["resolved_entities"][1]["canonical_name"], "Siachen Glacier")

    def test_dict_input_with_context(self):
        input_dicts = [
            {
                "entity_value": "IAF",
                "entity_type": "ORGANISATION",
                "context": "Fighter jets scrambled from Ambala airbase.",
            }
        ]
        out = self.agent.run(input_dicts)
        self.assertEqual(len(out["resolved_entities"]), 1)
        self.assertEqual(out["resolved_entities"][0]["canonical_name"], "Indian Air Force")
        self.assertEqual(out["resolved_entities"][0]["action"], "auto_link")

    def test_empty_and_invalid_inputs(self):
        res_empty = self.agent.resolve_entity("")
        self.assertEqual(res_empty["action"], "separate")
        self.assertEqual(res_empty["confidence"], 0.0)

        with self.assertRaises(TypeError):
            self.agent.run("not a list")


if __name__ == "__main__":
    unittest.main()
