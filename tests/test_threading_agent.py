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


if __name__ == "__main__":
    unittest.main()
