"""
Unit tests for Stage 2 ExtractionAgent.
Floor 2 — Language & Knowledge Agents
"""
import unittest
from unittest.mock import patch

from agents.base import Agent, BaseAgent
from agents.extraction.agent import ExtractionAgent
from common.schemas.articles import ArticleAnalysisOut, ArticleIn, EntityOut


class TestExtractionAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ExtractionAgent()

    def test_agent_protocol_conformance(self):
        self.assertIsInstance(self.agent, Agent)
        self.assertIsInstance(self.agent, BaseAgent)
        self.assertEqual(self.agent.name, "extraction_agent")
        self.assertEqual(self.agent.version, "0.2.0")
        self.assertTrue(callable(self.agent.run))
        self.assertTrue(callable(self.agent.run_batch))

    def test_border_incident_extraction_integration(self):
        article = ArticleIn(
            id=201,
            title="Border skirmish along LoC in Poonch sector",
            content="Indian Army and Pakistan Army exchange cross-border fire near the Line of Control.",
            url="https://example.com/loc-clash",
            language="en",
        )
        out = self.agent.run(article)
        self.assertIsInstance(out, ArticleAnalysisOut)
        self.assertEqual(out.article_id, 201)
        self.assertEqual(out.event_type, "border_incident")
        self.assertIn(out.threat_category, ["medium", "high"])
        self.assertTrue(len(out.entities) > 0)

        # Check entity values
        entity_values = [e.entity_value for e in out.entities]
        self.assertTrue(any("Line of Control" in val or "LoC" in val for val in entity_values))

        # Check entity types normalization
        for ent in out.entities:
            self.assertIn(ent.entity_type, ["LOCATION", "ORGANISATION", "EQUIPMENT", "PERSON", "EVENT"])
            self.assertIsNotNone(ent.provenance)
            self.assertEqual(ent.provenance.source_ids, [201])

        # Check overall provenance
        self.assertEqual(out.provenance.method, "ner_and_event_classifier")
        self.assertEqual(out.provenance.source_ids, [201])

    def test_dict_input_compatibility(self):
        raw_dict = {
            "id": 202,
            "title": "DRDO tests BrahMos supersonic cruise missile",
            "content": "Successful flight trial conducted from Chandipur test range.",
        }
        out = self.agent.run(raw_dict)
        self.assertEqual(out.article_id, 202)
        entity_values = [e.entity_value for e in out.entities]
        self.assertTrue("DRDO" in entity_values or "BrahMos" in entity_values)

    def test_unsupported_input_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.agent.run(12345)

    def test_empty_content_handled_cleanly(self):
        article = ArticleIn(
            id=203,
            title="Notice without content",
            content="",
            url="https://example.com/empty",
        )
        out = self.agent.run(article)
        self.assertEqual(out.article_id, 203)
        self.assertIn(out.event_type, ["general", "aerial", "cyber_attack", "diplomatic"])
        self.assertIsInstance(out.entities, list)

    @patch("agents.extraction.agent.extract_entities")
    @patch("agents.extraction.agent.classify_event")
    def test_resilience_to_engine_exceptions(self, mock_classify, mock_ner):
        mock_ner.side_effect = RuntimeError("Spacy crash")
        mock_classify.side_effect = RuntimeError("Classifier crash")

        article = ArticleIn(
            id=204,
            title="Normal headline",
            content="Normal content",
            url="https://example.com/crash-test",
        )
        out = self.agent.run(article)
        self.assertEqual(out.article_id, 204)
        self.assertEqual(out.event_type, "general")
        self.assertEqual(len(out.entities), 0)
        self.assertEqual(out.provenance.method, "ner_and_event_classifier")


if __name__ == "__main__":
    unittest.main()
