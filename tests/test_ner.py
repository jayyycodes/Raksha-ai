"""
Automated unit tests for engine/ner.py (Stage 1 Basic Entity Extraction MVP).

Tests:
1. Empty and invalid input validation
2. Successful entity extraction via spaCy
3. Output dictionary exact key structure
4. Entity types are strictly within {LOCATION, ORG, PERSON, WEAPON, EVENT}
5. Numeric confidence scores within [0.0, 1.0] and heuristic default documentation
6. Defense terminology recognition (LAC, LoC, Siachen, BrahMos, DRDO)
7. LoC positive and negative tests (no lowercase 'loc' matching)
8. Conservative PRODUCT-to-WEAPON mapping and unrelated product filtering
9. Duplicate prevention (same category deduplicated; different categories preserved)
10. Unmapped spaCy labels filtering
11. Lazy loading and caching
12. Missing dependency and model load error handling

All tests are deterministic and use mocked NLP models without downloading weights.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from engine.ner import (
    DEFAULT_MODEL,
    DEFAULT_PATTERN_CONFIDENCE,
    DEFAULT_SPACY_CONFIDENCE,
    ENTITY_TYPES,
    VALID_ENTITY_TYPES,
    DependencyError,
    ModelLoadError,
    NERError,
    _is_weapon_product,
    clear_ner_cache,
    extract_entities,
    get_cached_models,
)


def _build_mock_spacy_nlp(entities: list[tuple[str, str]] | list[tuple[str, str, float]]):
    """
    Construct a mock spaCy Language pipeline returning mock Doc with entities.

    Args:
        entities: List of (text, label) or (text, label, confidence)
    """
    mock_nlp = MagicMock()

    def side_effect(text):
        doc = MagicMock()
        ents = []
        for item in entities:
            ent = MagicMock()
            ent.text = item[0]
            ent.label_ = item[1]
            if len(item) > 2:
                ent.confidence = item[2]
            else:
                del ent.confidence
            ents.append(ent)
        doc.ents = ents
        return doc

    mock_nlp.side_effect = side_effect
    return mock_nlp


class TestNERInputValidation(unittest.TestCase):
    """Test validation of empty, whitespace, None, and non-string inputs."""

    def setUp(self):
        clear_ner_cache()

    def test_empty_string_returns_empty_list(self):
        """Empty text returns empty entity list without loading model."""
        result = extract_entities("")
        self.assertEqual(result, [])

    def test_whitespace_only_string_returns_empty_list(self):
        """Whitespace-only string returns empty entity list without loading model."""
        result = extract_entities("   \t\n  ")
        self.assertEqual(result, [])

    def test_none_input_raises_value_error(self):
        """None input raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            extract_entities(None)
        self.assertIn("must be a string", str(ctx.exception))

    def test_non_string_input_raises_value_error(self):
        """Non-string inputs (e.g. integer, dict, list) raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            extract_entities(12345)
        self.assertIn("must be a string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            extract_entities(["Indian Army"])
        self.assertIn("must be a string", str(ctx.exception))

    def test_invalid_model_name_raises_value_error(self):
        """Empty, None, or non-string model_name raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            extract_entities("Valid article text", model_name="")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            extract_entities("Valid article text", model_name="   ")
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            extract_entities("Valid article text", model_name=None)
        self.assertIn("model_name must be a non-empty string", str(ctx.exception))


class TestNERExtractionSuccessAndStructure(unittest.TestCase):
    """Test successful entity extraction, dictionary structure, and valid types."""

    def setUp(self):
        clear_ner_cache()

    def test_successful_spacy_entity_extraction(self):
        """spaCy extracted entities are mapped correctly to target types."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Indian Army", "ORG"),
            ("New Delhi", "GPE"),
            ("Rajnath Singh", "PERSON"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Rajnath Singh addressed Indian Army in New Delhi.")

        self.assertEqual(len(results), 3)

        expected = [
            {"entity_type": "ORG", "entity_value": "Indian Army", "confidence": DEFAULT_SPACY_CONFIDENCE},
            {"entity_type": "LOCATION", "entity_value": "New Delhi", "confidence": DEFAULT_SPACY_CONFIDENCE},
            {"entity_type": "PERSON", "entity_value": "Rajnath Singh", "confidence": DEFAULT_SPACY_CONFIDENCE},
        ]

        for exp in expected:
            match = next((e for e in results if e["entity_value"] == exp["entity_value"]), None)
            self.assertIsNotNone(match, f"Expected entity {exp['entity_value']} not found")
            self.assertEqual(match["entity_type"], exp["entity_type"])
            self.assertAlmostEqual(match["confidence"], exp["confidence"])

    def test_output_dictionary_exact_structure(self):
        """Every returned dictionary has exactly entity_type, entity_value, and confidence."""
        mock_nlp = _build_mock_spacy_nlp([("Ladakh", "LOC")])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Troops patrolled Ladakh.")

        self.assertTrue(len(results) > 0)
        for item in results:
            self.assertIsInstance(item, dict)
            self.assertEqual(set(item.keys()), {"entity_type", "entity_value", "confidence"})
            self.assertIsInstance(item["entity_type"], str)
            self.assertIsInstance(item["entity_value"], str)
            self.assertIsInstance(item["confidence"], float)

    def test_valid_entity_types_strictly_enforced(self):
        """All returned entity_type values are within VALID_ENTITY_TYPES."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Northern Command", "ORG"),
            ("Srinagar", "GPE"),
            ("Manoj Pande", "PERSON"),
            ("Tejas", "PRODUCT"),
            ("Operation Vijay", "EVENT"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Military operations text sample")

        self.assertEqual(len(results), 5)
        for item in results:
            self.assertIn(item["entity_type"], VALID_ENTITY_TYPES)

    def test_confidence_range_and_contract(self):
        """Confidence scores must be numeric floats in [0.0, 1.0]."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Indian Navy", "ORG", 0.92),
            ("Mumbai", "GPE", 0.78),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Indian Navy based in Mumbai")

        for item in results:
            self.assertIsInstance(item["confidence"], float)
            self.assertGreaterEqual(item["confidence"], 0.0)
            self.assertLessEqual(item["confidence"], 1.0)

    def test_unmapped_spacy_labels_are_filtered(self):
        """spaCy labels like DATE, CARDINAL, MONEY, TIME are excluded."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Monday", "DATE"),
            ("1000", "CARDINAL"),
            ("Indian Air Force", "ORG"),
            ("$5 million", "MONEY"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("On Monday 1000 troops from Indian Air Force received $5 million.")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["entity_value"], "Indian Air Force")
        self.assertEqual(results[0]["entity_type"], "ORG")


class TestDefenseTerminologyRecognition(unittest.TestCase):
    """Test pattern-based recognition of specific defense terminology."""

    def setUp(self):
        clear_ner_cache()
        self.empty_nlp = _build_mock_spacy_nlp([])

    def test_lac_recognition(self):
        """LAC and Line of Actual Control are recognized as LOCATION."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results1 = extract_entities("Troops were moved along the LAC yesterday.")
            results2 = extract_entities("Patrolling resumed on the Line of Actual Control.")

        self.assertTrue(any(e["entity_value"] == "LAC" and e["entity_type"] == "LOCATION" for e in results1))
        self.assertTrue(any(
            e["entity_value"] == "Line of Actual Control" and e["entity_type"] == "LOCATION" for e in results2
        ))

    def test_loc_positive_recognition(self):
        """LoC, LOC, and Line of Control are recognized as LOCATION."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results1 = extract_entities("Cross-border firing reported along the LoC.")
            results2 = extract_entities("Surveillance intensified on the LOC sector.")
            results3 = extract_entities("Peace maintained along the Line of Control.")
            results4 = extract_entities("Troops patrolled the line of control.")

        self.assertTrue(any(e["entity_value"] == "LoC" and e["entity_type"] == "LOCATION" for e in results1))
        self.assertTrue(any(e["entity_value"] == "LOC" and e["entity_type"] == "LOCATION" for e in results2))
        self.assertTrue(any(
            e["entity_value"] == "Line of Control" and e["entity_type"] == "LOCATION" for e in results3
        ))
        self.assertTrue(any(
            e["entity_value"].lower() == "line of control" and e["entity_type"] == "LOCATION" for e in results4
        ))

    def test_loc_negative_does_not_match_lowercase_loc(self):
        """Arbitrary lowercase 'loc' (lines of code, etc.) must NOT match as LoC LOCATION."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results1 = extract_entities("The pull request modified 250 loc in total.")
            results2 = extract_entities("Check loc file header before submission.")

        # Neither should match LoC as an entity
        self.assertEqual(results1, [])
        self.assertEqual(results2, [])

    def test_siachen_recognition(self):
        """Siachen and Siachen Glacier are recognized as LOCATION."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results1 = extract_entities("Supplies were airlifted to Siachen outpost.")
            results2 = extract_entities("Soldiers deployed at Siachen Glacier base camp.")

        self.assertTrue(any(e["entity_value"] == "Siachen" and e["entity_type"] == "LOCATION" for e in results1))
        self.assertTrue(any(
            e["entity_value"] == "Siachen Glacier" and e["entity_type"] == "LOCATION" for e in results2
        ))

    def test_brahmos_recognition(self):
        """BrahMos missile is recognized as WEAPON."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results = extract_entities("A test firing of the BrahMos supersonic cruise missile was conducted.")

        self.assertTrue(any(e["entity_value"] == "BrahMos" and e["entity_type"] == "WEAPON" for e in results))

    def test_drdo_recognition(self):
        """DRDO and full name are recognized as ORG."""
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results1 = extract_entities("DRDO successfully developed the guidance system.")
            results2 = extract_entities("Defence Research and Development Organisation completed trials.")

        self.assertTrue(any(e["entity_value"] == "DRDO" and e["entity_type"] == "ORG" for e in results1))
        self.assertTrue(any(
            e["entity_value"] == "Defence Research and Development Organisation" and e["entity_type"] == "ORG"
            for e in results2
        ))

    def test_combined_defense_terms_in_single_article(self):
        """All 5 defense terms in one text are extracted accurately with valid types."""
        text = "DRDO tested BrahMos missile near Siachen and monitored LAC and LoC sectors."
        with patch("engine.ner._load_model", return_value=self.empty_nlp):
            results = extract_entities(text)

        entity_map = {e["entity_value"]: e["entity_type"] for e in results}

        self.assertEqual(entity_map.get("DRDO"), "ORG")
        self.assertEqual(entity_map.get("BrahMos"), "WEAPON")
        self.assertEqual(entity_map.get("Siachen"), "LOCATION")
        self.assertEqual(entity_map.get("LAC"), "LOCATION")
        self.assertEqual(entity_map.get("LoC"), "LOCATION")


class TestProductToWeaponConservativeMapping(unittest.TestCase):
    """Test conservative mapping of spaCy PRODUCT entities to WEAPON."""

    def setUp(self):
        clear_ner_cache()

    def test_weapon_products_are_classified_as_weapon(self):
        """Military hardware and defense platforms tagged as PRODUCT map to WEAPON."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Tejas", "PRODUCT"),
            ("Rafale fighter", "PRODUCT"),
            ("Cruise missile", "PRODUCT"),
            ("T-90 tank", "PRODUCT"),
            ("INS Vikrant", "PRODUCT"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Defense procurement included Tejas, Rafale, and T-90 tank.")

        weapon_values = [e["entity_value"] for e in results if e["entity_type"] == "WEAPON"]
        self.assertIn("Tejas", weapon_values)
        self.assertIn("Rafale fighter", weapon_values)
        self.assertIn("Cruise missile", weapon_values)
        self.assertIn("T-90 tank", weapon_values)
        self.assertIn("INS Vikrant", weapon_values)

    def test_unrelated_commercial_products_are_filtered_out(self):
        """Commercial/consumer products tagged as PRODUCT are NOT classified as WEAPON."""
        mock_nlp = _build_mock_spacy_nlp([
            ("iPhone 15", "PRODUCT"),
            ("PlayStation 5", "PRODUCT"),
            ("Microsoft Windows", "PRODUCT"),
            ("Toyota Camry", "PRODUCT"),
            ("Coca-Cola", "PRODUCT"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Consumers purchased iPhone 15, PlayStation 5, and Toyota Camry.")

        # None of these commercial products should be mapped to WEAPON
        self.assertEqual(results, [])

    def test_helper_is_weapon_product(self):
        """Direct unit test of _is_weapon_product helper function."""
        # Positives
        self.assertTrue(_is_weapon_product("Agni-V"))
        self.assertTrue(_is_weapon_product("Pinaka rocket system"))
        self.assertTrue(_is_weapon_product("K9 Vajra howitzer"))
        self.assertTrue(_is_weapon_product("Attack drone"))
        self.assertTrue(_is_weapon_product("Scorpene submarine"))

        # Negatives
        self.assertFalse(_is_weapon_product("MacBook Pro"))
        self.assertFalse(_is_weapon_product("Samsung Galaxy Tab"))
        self.assertFalse(_is_weapon_product("Nike Air Jordan"))


class TestNERDuplicatePrevention(unittest.TestCase):
    """Test deduplication while preventing accidental merge across distinct entity categories."""

    def setUp(self):
        clear_ner_cache()

    def test_duplicate_defense_terms_in_text(self):
        """Repeated mentions of defense terms produce only a single entry."""
        empty_nlp = _build_mock_spacy_nlp([])
        text = "DRDO conducted trials. DRDO announced that BrahMos was successful. Later BrahMos was praised."

        with patch("engine.ner._load_model", return_value=empty_nlp):
            results = extract_entities(text)

        drdo_count = sum(1 for e in results if e["entity_value"].lower() == "drdo")
        brahmos_count = sum(1 for e in results if e["entity_value"].lower() == "brahmos")

        self.assertEqual(drdo_count, 1)
        self.assertEqual(brahmos_count, 1)

    def test_duplicate_between_spacy_and_defense_patterns(self):
        """When both defense pattern and spaCy recognize DRDO, it appears only once."""
        mock_nlp = _build_mock_spacy_nlp([
            ("DRDO", "ORG"),
            ("New Delhi", "GPE"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("DRDO headquarters is located in New Delhi.")

        drdo_matches = [e for e in results if e["entity_value"].lower() == "drdo"]
        self.assertEqual(len(drdo_matches), 1)
        self.assertEqual(drdo_matches[0]["confidence"], DEFAULT_PATTERN_CONFIDENCE)

    def test_duplicate_spacy_entities_in_same_category(self):
        """Repeated mentions of same category entity are deduplicated."""
        mock_nlp = _build_mock_spacy_nlp([
            ("Indian Army", "ORG"),
            ("Indian Army", "ORG"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Indian Army moved forward. The Indian Army held ground.")

        army_matches = [e for e in results if e["entity_value"].lower() == "indian army"]
        self.assertEqual(len(army_matches), 1)

    def test_identical_text_in_different_categories_not_merged(self):
        """Entities with identical text but different categories are both preserved."""
        # e.g. 'Rawat' as PERSON and 'Rawat' as LOCATION
        mock_nlp = _build_mock_spacy_nlp([
            ("Rawat", "PERSON"),
            ("Rawat", "LOC"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("General Rawat inspected defenses in Rawat district.")

        self.assertEqual(len(results), 2)
        person_match = next((e for e in results if e["entity_type"] == "PERSON"), None)
        loc_match = next((e for e in results if e["entity_type"] == "LOCATION"), None)

        self.assertIsNotNone(person_match)
        self.assertIsNotNone(loc_match)
        self.assertEqual(person_match["entity_value"], "Rawat")
        self.assertEqual(loc_match["entity_value"], "Rawat")

    def test_defense_pattern_and_spacy_different_categories_both_preserved(self):
        """When a defense pattern and spaCy return identical text in different categories, both are kept."""
        # Defense pattern extracts "Agni" as WEAPON.
        # spaCy identifies "Agni" in the context of an individual's name as PERSON.
        mock_nlp = _build_mock_spacy_nlp([
            ("Agni", "PERSON"),
        ])

        with patch("engine.ner._load_model", return_value=mock_nlp):
            results = extract_entities("Commander Agni supervised the Agni missile launch.")

        weapon_match = next((e for e in results if e["entity_type"] == "WEAPON" and e["entity_value"] == "Agni"), None)
        person_match = next((e for e in results if e["entity_type"] == "PERSON" and e["entity_value"] == "Agni"), None)

        self.assertIsNotNone(weapon_match, "Defense pattern WEAPON Agni was suppressed")
        self.assertIsNotNone(person_match, "spaCy PERSON Agni was incorrectly suppressed")
        self.assertEqual(weapon_match["confidence"], DEFAULT_PATTERN_CONFIDENCE)
        self.assertEqual(person_match["confidence"], DEFAULT_SPACY_CONFIDENCE)


class TestNERLazyLoadingAndCaching(unittest.TestCase):
    """Test model lazy loading, caching across calls, and cache clearance."""

    def setUp(self):
        clear_ner_cache()
        self.mock_nlp = _build_mock_spacy_nlp([("Ladakh", "LOC")])

    def test_model_is_lazily_loaded_on_first_call(self):
        """spaCy model is not loaded until extract_entities is called."""
        self.assertEqual(len(get_cached_models()), 0)

        with patch("engine.ner._load_model", return_value=self.mock_nlp) as loader:
            results = extract_entities("Troops reached Ladakh")
            self.assertEqual(loader.call_count, 1)
            loader.assert_called_once_with(DEFAULT_MODEL)
            self.assertIn(DEFAULT_MODEL, get_cached_models())
            self.assertTrue(len(results) > 0)

    def test_model_is_cached_across_repeated_calls(self):
        """Repeated extract_entities calls reuse cached model without reloading."""
        with patch("engine.ner._load_model", return_value=self.mock_nlp) as loader:
            res1 = extract_entities("Headline one")
            res2 = extract_entities("Headline two")
            res3 = extract_entities("Headline three")

            self.assertEqual(loader.call_count, 1)

    def test_clear_ner_cache_evicts_models(self):
        """clear_ner_cache() purges all cached spaCy models from memory."""
        with patch("engine.ner._load_model", return_value=self.mock_nlp):
            extract_entities("Sample text")
            self.assertEqual(len(get_cached_models()), 1)

            clear_ner_cache()
            self.assertEqual(len(get_cached_models()), 0)


class TestNERFailureModes(unittest.TestCase):
    """Test handling of missing dependencies, model load failures, and processing errors."""

    def setUp(self):
        clear_ner_cache()

    def test_missing_dependency_raises_dependency_error(self):
        """When spacy is not installed, DependencyError is raised."""
        with patch.dict("sys.modules", {"spacy": None}):
            with self.assertRaises(DependencyError) as ctx:
                extract_entities("Sample text with Indian Army")
            self.assertIn("spacy", str(ctx.exception))

    def test_model_load_failure_raises_model_load_error(self):
        """When spaCy model cannot be loaded, ModelLoadError is raised."""
        with patch(
            "engine.ner._load_model",
            side_effect=ModelLoadError("Can't find model 'en_core_web_sm'"),
        ):
            with self.assertRaises(ModelLoadError) as ctx:
                extract_entities("Sample text")
            self.assertIn("Can't find model", str(ctx.exception))

    def test_nlp_processing_failure_raises_ner_error(self):
        """When nlp(text) fails during execution, NERError is raised."""
        mock_nlp = MagicMock()
        mock_nlp.side_effect = RuntimeError("Memory allocation failure")

        with patch("engine.ner._load_model", return_value=mock_nlp):
            with self.assertRaises(NERError) as ctx:
                extract_entities("Sample text")
            self.assertIn("Failed to process text", str(ctx.exception))


class TestNERConstantsAndTypes(unittest.TestCase):
    """Test preservation of required constants and mappings."""

    def test_default_model_is_en_core_web_sm(self):
        """Default model is en_core_web_sm for lightweight Stage 1 MVP."""
        self.assertEqual(DEFAULT_MODEL, "en_core_web_sm")

    def test_default_heuristic_confidences(self):
        """Heuristic confidence values satisfy Stage 1 numeric output contract."""
        self.assertEqual(DEFAULT_PATTERN_CONFIDENCE, 0.95)
        self.assertEqual(DEFAULT_SPACY_CONFIDENCE, 0.85)

    def test_entity_types_mapping_preserved(self):
        """ENTITY_TYPES mapping is preserved for backwards compatibility."""
        self.assertIn("LOCATION", ENTITY_TYPES)
        self.assertIn("ORG", ENTITY_TYPES)
        self.assertIn("PERSON", ENTITY_TYPES)
        self.assertIn("WEAPON", ENTITY_TYPES)
        self.assertIn("EVENT", ENTITY_TYPES)


if __name__ == "__main__":
    unittest.main()
