"""
Unit tests for Stage 2 ThreadingAgent.
Floor 2 — Language & Knowledge Agents
"""
import math
import unittest
from unittest.mock import patch

from agents.base import Agent, BaseAgent
from agents.threading.agent import (
    ThreadingAgent,
    compute_cosine_similarity,
    compute_jaccard,
)
from common.schemas.events import EventThreadingIn, EventThreadingOut
from engine.embeddings import EMBEDDING_DIM


class TestThreadingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ThreadingAgent()

    def test_agent_protocol_conformance(self):
        self.assertIsInstance(self.agent, Agent)
        self.assertIsInstance(self.agent, BaseAgent)
        self.assertEqual(self.agent.name, "threading_agent")
        self.assertEqual(self.agent.version, "0.2.0")
        self.assertTrue(callable(self.agent.run))
        self.assertTrue(callable(self.agent.run_batch))

    # ── Cosine Similarity Vector Validation Tests ──
    def test_cosine_similarity_identical_vectors(self):
        vec = [0.1] * EMBEDDING_DIM
        sim = compute_cosine_similarity(vec, vec)
        self.assertAlmostEqual(sim, 1.0, places=4)

    def test_cosine_similarity_orthogonal_vectors(self):
        vec_a = [1.0, 0.0] + [0.0] * (EMBEDDING_DIM - 2)
        vec_b = [0.0, 1.0] + [0.0] * (EMBEDDING_DIM - 2)
        sim = compute_cosine_similarity(vec_a, vec_b)
        self.assertAlmostEqual(sim, 0.0, places=4)

    def test_cosine_similarity_semantically_similar_vectors(self):
        vec_a = [0.5] * EMBEDDING_DIM
        vec_b = [0.5] * (EMBEDDING_DIM // 2) + [0.4] * (EMBEDDING_DIM // 2)
        sim = compute_cosine_similarity(vec_a, vec_b)
        self.assertTrue(0.90 <= sim <= 1.0)

    def test_cosine_similarity_zero_vector(self):
        zero_vec = [0.0] * EMBEDDING_DIM
        normal_vec = [0.2] * EMBEDDING_DIM
        sim = compute_cosine_similarity(zero_vec, normal_vec)
        self.assertEqual(sim, 0.0)

    def test_cosine_similarity_dimension_mismatch_raises_value_error(self):
        vec_768 = [0.1] * 768
        vec_512 = [0.1] * 512
        with self.assertRaises(ValueError):
            compute_cosine_similarity(vec_768, vec_512)

    def test_cosine_similarity_nan_raises_value_error(self):
        vec_nan = [0.1] * (EMBEDDING_DIM - 1) + [float("nan")]
        vec_valid = [0.1] * EMBEDDING_DIM
        with self.assertRaises(ValueError):
            compute_cosine_similarity(vec_nan, vec_valid)

    def test_cosine_similarity_inf_raises_value_error(self):
        vec_inf = [0.1] * (EMBEDDING_DIM - 1) + [float("inf")]
        vec_valid = [0.1] * EMBEDDING_DIM
        with self.assertRaises(ValueError):
            compute_cosine_similarity(vec_inf, vec_valid)

    # ── Embedding Integration in Threading ──
    def test_threading_with_explicit_768_embeddings(self):
        # Create candidate event with pre-cached embedding
        event = {
            "id": 10,
            "title": "Air Defence Interceptions near Western Border",
            "region": "Punjab",
            "event_type": "aerial",
            "entities": ["IAF", "PAF"],
            "summary": "Combat air patrols responding to airspace violations.",
            "embedding": [0.05] * EMBEDDING_DIM,
        }
        custom_agent = ThreadingAgent(known_events=[event])

        # Test matching with article embedding
        art_embedding = [0.05] * EMBEDDING_DIM
        score, rationale, metric = custom_agent.score_match(
            article_title="IAF jets scramble to intercept drone",
            article_content="Air defense radar detected intrusion near border.",
            article_entities=["IAF"],
            article_type="aerial",
            article_region="Punjab",
            event=event,
            article_embedding=art_embedding,
        )
        self.assertEqual(metric, "cosine_embedding_768")
        self.assertIn("cosine_embedding_768: 1.00", rationale)
        self.assertGreaterEqual(score, 0.70)

    def test_threading_fallback_to_token_jaccard_when_embeddings_unavailable(self):
        event = {
            "id": 11,
            "title": "Naval Patrols in Arabian Sea",
            "region": "Arabian Sea",
            "event_type": "naval",
            "entities": ["Indian Navy"],
            "summary": "Destroyers on patrol.",
        }
        custom_agent = ThreadingAgent(known_events=[event])
        score, rationale, metric = custom_agent.score_match(
            article_title="Indian Navy warship visits port",
            article_content="Patrol in Arabian Sea.",
            article_entities=["Indian Navy"],
            article_type="naval",
            article_region="Arabian Sea",
            event=event,
            article_embedding=None,  # No embedding
        )
        self.assertEqual(metric, "token_jaccard_fallback")
        self.assertIn("token_jaccard_fallback", rationale)

    def test_thread_to_existing_lac_event_cluster(self):
        item = EventThreadingIn(
            article_id=301,
            title="PLA increases troop rotation along Eastern Ladakh LAC",
            content="Indian Army monitors Chinese military developments near Galwan and Pangong Tso.",
            entities=["LAC", "PLA", "Indian Army", "Eastern Ladakh", "Galwan"],
            event_type="border_incident",
            region="Eastern Ladakh",
        )
        out = self.agent.run(item)
        self.assertIsInstance(out, EventThreadingOut)
        self.assertEqual(out.article_id, 301)
        self.assertEqual(out.matched_event_id, 1)  # Event #1 is Eastern Ladakh LAC standoff
        self.assertFalse(out.created_new_event)
        self.assertIsNone(out.new_event_title)
        self.assertTrue(len(out.candidate_links) > 0)

        top_link = out.candidate_links[0]
        self.assertEqual(top_link.event_id, 1)
        self.assertEqual(top_link.article_id, 301)
        self.assertGreaterEqual(top_link.confidence, 0.60)
        self.assertEqual(out.provenance.source_ids, [301])

    def test_seed_new_event_cluster_when_unmatched(self):
        item = EventThreadingIn(
            article_id=302,
            title="India and France sign space situational awareness bilateral treaty",
            content="Ministers met in Paris to exchange satellite tracking telemetry.",
            entities=["ISRO", "CNES", "Paris"],
            event_type="diplomatic",
            region="Europe",
        )
        out = self.agent.run(item)
        self.assertIsInstance(out, EventThreadingOut)
        self.assertEqual(out.article_id, 302)
        self.assertIsNone(out.matched_event_id)
        self.assertTrue(out.created_new_event)
        self.assertIsNotNone(out.new_event_title)
        self.assertIn("Diplomatic", out.new_event_title)

        seed_link = out.candidate_links[0]
        self.assertTrue(seed_link.is_seed)
        self.assertEqual(seed_link.link_method, "cluster_seed")
        self.assertEqual(seed_link.confidence, 1.0)

    def test_dict_input_compatibility(self):
        raw_dict = {
            "article_id": 304,
            "title": "Cross-border firing reported near Poonch on the LoC",
            "content": "Pakistan Army violates ceasefire along the Line of Control.",
            "entities": ["LoC", "Line of Control", "Pakistan Army"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
        }
        out = self.agent.run(raw_dict)
        self.assertEqual(out.article_id, 304)
        self.assertEqual(out.matched_event_id, 2)  # Event #2 is LoC Ceasefire monitoring

    def test_unsupported_input_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.agent.run(9999)


class TestThreadingBenchmarkAndSafety(unittest.TestCase):
    """
    Validates ThreadingAgent benchmark behavior, pairwise comparison,
    safety guards (temporal distance, sector conflict, event type compatibility),
    and absence of fallback event leakage.
    """

    def test_same_event_reports_grouped_successfully(self):
        """Identical breaking event from different sources groups as MATCH."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Artillery Exchange in Tangdhar Sector After Ceasefire Violation",
            "content": "Pakistani troops violated ceasefire by targeting forward Indian positions with mortar fire in Tangdhar.",
            "entities": ["Indian Army", "Pakistan Army", "Tangdhar", "Kupwara", "Line of Control"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-10-15T08:30:00Z",
        }
        art_b = {
            "title": "Heavy Cross-Border Shelling Reported in North Kashmir Kupwara",
            "content": "Cross-border shelling erupted early morning along LoC in North Kashmir's Tangdhar sector.",
            "entities": ["Indian Army", "LoC", "Tangdhar", "Kupwara", "Kashmir"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-10-15T11:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b, match_threshold=0.65, review_threshold=0.45)
        self.assertEqual(res["relation"], "MATCH")
        self.assertGreaterEqual(res["score"], 0.65)

    def test_distinct_sectors_kept_separate_despite_same_region(self):
        """Conflicting sub-regional sectors (Poonch vs Uri) within J&K remain DISTINCT."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Ceasefire Violation Reported in Poonch District",
            "content": "Heavy mortar fire reported in Krishna Ghati sector of Poonch district along LoC.",
            "entities": ["Indian Army", "Poonch", "Krishna Ghati", "LoC"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-09-05T07:00:00Z",
        }
        art_b = {
            "title": "Cross-Border Firing in Uri Sector of Baramulla",
            "content": "Small arms and mortar fire targeted defensive positions in Uri sector of Baramulla district.",
            "entities": ["Indian Army", "Uri", "Baramulla", "LoC"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-09-05T08:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b, match_threshold=0.65, review_threshold=0.45)
        self.assertEqual(res["relation"], "DISTINCT")
        self.assertLess(res["score"], 0.45)

    def test_distinct_dates_separated_by_temporal_cap(self):
        """Identical meetings separated by over two years remain DISTINCT via temporal cap."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Corps Commander Level Military Talks at Chushul",
            "content": "Indian and Chinese military delegates convened at Chushul to discuss disengagement.",
            "entities": ["Indian Army", "PLA", "Chushul", "Eastern Ladakh", "LAC"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2024-02-19T10:00:00Z",
        }
        art_b = {
            "title": "Corps Commander Level Military Talks at Chushul",
            "content": "Indian and Chinese military delegates convened at Chushul to discuss disengagement.",
            "entities": ["Indian Army", "PLA", "Chushul", "Eastern Ladakh", "LAC"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-10T10:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b, match_threshold=0.65, review_threshold=0.45)
        self.assertEqual(res["relation"], "DISTINCT")
        self.assertLessEqual(res["score"], 0.35)

    def test_distinct_event_types_kept_separate_despite_same_location(self):
        """Different event types (border skirmish vs ransomware) in the same district remain DISTINCT."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Border Troops Intercept Illegal Infiltration in Samba",
            "content": "BSF troops foiled armed infiltration along international boundary fence in Samba.",
            "entities": ["Border Security Force", "Samba", "Jammu"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-08-11T03:00:00Z",
        }
        art_b = {
            "title": "Ransomware Disrupts Municipal IT Servers in Samba District",
            "content": "Administrative services at municipal complex in Samba halted following ransomware infection.",
            "entities": ["Samba", "CERT-In"],
            "event_type": "cyber_attack",
            "region": "Jammu & Kashmir",
            "published_at": "2026-08-11T10:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b, match_threshold=0.65, review_threshold=0.45)
        self.assertEqual(res["relation"], "DISTINCT")

    def test_empty_known_events_prevents_default_event_leakage(self):
        """ThreadingAgent initialized with known_events=[] has zero candidates and seeds a new cluster."""
        agent = ThreadingAgent(known_events=[])
        out = agent.run({
            "article_id": 999,
            "title": "Artillery Exchange in Tangdhar Sector",
            "content": "Pakistani troops violated ceasefire in Tangdhar.",
            "entities": ["Tangdhar", "LoC"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
        })
        self.assertTrue(out.created_new_event)
        self.assertIsNone(out.matched_event_id)

    def test_run_event_threading_eval_harness_integration(self):
        """Evaluation harness runs on event_threading_eval.jsonl without errors."""
        from evaluation.harness import run_event_threading_eval
        metrics = run_event_threading_eval(match_threshold=0.65, review_threshold=0.45)

        self.assertEqual(metrics["sample_count"], 30)
        self.assertGreaterEqual(metrics["overall_accuracy"], 0.70)
        # Verify 0 false merges on true DISTINCT pairs
        self.assertEqual(metrics["confusion_matrix"]["DISTINCT"]["MATCH"], 0)
        self.assertGreaterEqual(metrics["match_metrics"]["precision"], 0.80)

    # ── Safety Guard Regression Tests (Positive & Negative Cases) ──

    def test_safety_guard_preliminary_reports_capped_to_prevent_false_merge(self):
        """Negative Guard 1: Preliminary/unconfirmed wording is capped at 0.58, preventing auto-merge."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Preliminary report of gunfire near Chushul post",
            "content": "Unconfirmed reports suggest small arms fire was heard along the LAC in Chushul.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T08:00:00Z",
        }
        art_b = {
            "title": "Border clash reported near Chushul LAC",
            "content": "Indian and PLA troops engage in standoff along the Line of Actual Control.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T09:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b)
        self.assertLessEqual(res["score"], 0.58)
        self.assertNotEqual(res["relation"], "MATCH")
        self.assertEqual(res["relation"], "REVIEW_NEEDED")

    def test_safety_guard_confirmed_reports_reach_match_without_suppression(self):
        """Positive Guard 1: Confirmed reports describing the same event reach MATCH without suppression."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Border clash erupts near Chushul LAC",
            "content": "Indian and PLA troops engage in standoff along the Line of Actual Control.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T08:00:00Z",
        }
        art_b = {
            "title": "Fresh standoff reported near Chushul sector",
            "content": "Border confrontation reported between Indian Army and PLA at Chushul.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T09:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b)
        self.assertGreaterEqual(res["score"], 0.65)
        self.assertEqual(res["relation"], "MATCH")

    def test_safety_guard_divergent_type_low_headline_capped_to_prevent_false_merge(self):
        """Negative Guard 2: Divergent event types with low title similarity are capped at 0.58."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Anti-encroachment demolition drive in border district",
            "content": "Municipal authorities clear illegal shops near border highway in Jammu.",
            "entities": ["Jammu", "Indian Army"],
            "event_type": "civil_order",
            "region": "Jammu & Kashmir",
            "published_at": "2026-10-15T08:00:00Z",
        }
        art_b = {
            "title": "Cross-border artillery shelling strikes forward post",
            "content": "Mortar shells landed near defensive perimeter in Jammu sector.",
            "entities": ["Jammu", "Indian Army"],
            "event_type": "border_incident",
            "region": "Jammu & Kashmir",
            "published_at": "2026-10-15T09:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b)
        self.assertLessEqual(res["score"], 0.58)
        self.assertNotEqual(res["relation"], "MATCH")
        self.assertEqual(res["relation"], "REVIEW_NEEDED")

    def test_safety_guard_cross_type_with_headline_alignment_not_suppressed(self):
        """Positive Guard 2: Differing event types with genuine headline alignment are not suppressed."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "PLA troop deployment surges across Chushul sector",
            "content": "Troops moving armored vehicles near friction point in Chushul.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "military_movement",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T08:00:00Z",
        }
        art_b = {
            "title": "Chinese troop deployment reported at Chushul border",
            "content": "Forward movements observed along Chushul sector at LAC.",
            "entities": ["LAC", "Chushul", "PLA"],
            "event_type": "border_incident",
            "region": "Eastern Ladakh",
            "published_at": "2026-10-15T09:00:00Z",
        }
        res = agent.compare_articles(art_a, art_b)
        self.assertGreaterEqual(res["score"], 0.65)
        self.assertEqual(res["relation"], "MATCH")

    # ── Embedding Path vs Lexical Fallback & Entity Normalization Tests ──

    def test_dense_embedding_path_exercised_when_embeddings_supplied(self):
        """Dense 768-dim embedding path is exercised when vectors are supplied directly without model download."""
        agent = ThreadingAgent(known_events=[])
        # Two identical synthetic 768-dim unit vectors
        vec_a = [0.036] * EMBEDDING_DIM
        vec_b = [0.036] * EMBEDDING_DIM

        art_a = {
            "title": "Strategic Air Patrols over Western Border",
            "content": "Air defence radar tracked incoming aircraft near international border.",
            "entities": ["IAF"],
            "event_type": "aerial",
            "region": "Punjab",
            "embedding": vec_a,
        }
        art_b = {
            "title": "IAF Intercepts Unidentified Target near Border",
            "content": "Combat air patrols scrambled after radar detection in Punjab sector.",
            "entities": ["IAF"],
            "event_type": "aerial",
            "region": "Punjab",
            "embedding": vec_b,
        }

        res = agent.compare_articles(art_a, art_b, a_embedding=vec_a, b_embedding=vec_b)
        self.assertEqual(res["text_metric"], "cosine_embedding_768")
        self.assertIn("cosine_embedding_768", res["rationale"])
        self.assertGreaterEqual(res["score"], 0.70)
        self.assertEqual(res["relation"], "MATCH")

    def test_lexical_fallback_remains_separate_when_embeddings_absent(self):
        """When embeddings are omitted and model is offline, engine safely uses lexical fallback."""
        agent = ThreadingAgent(known_events=[])
        art_a = {
            "title": "Naval Escort Operation in Gulf of Aden",
            "content": "Guided missile destroyer escorts commercial merchant vessels.",
            "entities": ["Indian Navy"],
            "event_type": "naval",
            "region": "Indian Ocean",
        }
        art_b = {
            "title": "Merchant Vessel Escorted by Indian Warship",
            "content": "Naval operations ensure maritime security in Gulf of Aden.",
            "entities": ["Indian Navy"],
            "event_type": "naval",
            "region": "Indian Ocean",
        }

        res = agent.compare_articles(art_a, art_b)
        self.assertEqual(res["text_metric"], "token_jaccard_fallback")
        self.assertIn("token_jaccard_fallback", res["rationale"])

    def test_entity_normalization_mki_variants_and_unrelated_names(self):
        """Verify MKI/mark variants are normalized to base platform while unrelated names remain uncorrupted."""
        agent = ThreadingAgent(known_events=[])

        # Test MKI variants match base platform
        event_platform = {
            "id": 50,
            "title": "Air Force Fighter Squadron Readiness",
            "summary": "Combat readiness of frontline fighter aircraft.",
            "event_type": "aerial",
            "region": "Western",
            "entities": ["su-30", "tejas"],
        }
        # Article with Su-30MKI and Tejas Mk1
        score_match, _, _ = agent.score_match(
            article_title="Frontline Fighters Scrambled",
            article_content="Squadron deployed Su-30MKI and Tejas Mk-1 jets.",
            article_entities=["Su-30MKI", "Tejas Mk1"],
            article_type="aerial",
            article_region="Western",
            event=event_platform,
        )
        self.assertGreaterEqual(score_match, 0.60)

        # Test unrelated names are NOT corrupted by MKI stripping
        event_unrelated = {
            "id": 51,
            "title": "Infrastructure Development",
            "summary": "Civil construction projects in border districts.",
            "event_type": "general",
            "region": "North",
            "entities": ["kamki", "amkit"],
        }
        # If 'kamki' was corrupted by naive replace to 'ka' or 'amkit' to 'at', overlap would fail
        score_unrelated, rationale, _ = agent.score_match(
            article_title="Infrastructure Development",
            article_content="Border works in Kamki and Amkit.",
            article_entities=["Kamki", "Amkit"],
            article_type="general",
            article_region="North",
            event=event_unrelated,
        )
        self.assertIn("kamki", rationale)
        self.assertIn("amkit", rationale)

        # Test standalone 'MKI' token is not reduced to empty string
        event_mki_alone = {
            "id": 52,
            "title": "Standardization Program",
            "summary": "Testing MKI configuration.",
            "event_type": "general",
            "region": "Central",
            "entities": ["mki"],
        }
        score_mki, rationale_mki, _ = agent.score_match(
            article_title="Standardization Program",
            article_content="Evaluation of MKI standards.",
            article_entities=["MKI"],
            article_type="general",
            article_region="Central",
            event=event_mki_alone,
        )
        self.assertIn("mki", rationale_mki)


if __name__ == "__main__":
    unittest.main()
