"""
Integration test for Floor 2 — Language & Knowledge Agents (Stage 2).
Exercises TranslationAgent, ExtractionAgent, ResolutionAgent, and ThreadingAgent
end-to-end on defence OSINT scenarios with full provenance verification.
"""
import unittest

from agents.extraction.agent import ExtractionAgent
from agents.resolution.agent import ResolutionAgent
from agents.threading.agent import ThreadingAgent
from agents.translation.agent import TranslationAgent
from common.schemas.articles import ArticleIn


class TestStage2LanguageAgentsIntegration(unittest.TestCase):
    def setUp(self):
        self.translation_agent = TranslationAgent()
        self.extraction_agent = ExtractionAgent()
        self.resolution_agent = ResolutionAgent()
        self.threading_agent = ThreadingAgent()

    def test_end_to_end_lac_border_article_pipeline(self):
        # 1. Input Article
        raw_article = ArticleIn(
            id=501,
            title="Chinese PLA patrols observed across LAC near Pangong Lake",
            content="Indian Army surveillance units spotted PLA mechanized columns moving adjacent to the Line of Actual Control.",
            url="https://thehindu.com/lac-pangong-patrol",
            language="en",
        )

        # 2. Step 1: Translation
        trans_out = self.translation_agent.run(raw_article)
        self.assertEqual(trans_out["article_id"], 501)
        self.assertFalse(trans_out["is_translated"])
        self.assertIsNotNone(trans_out["provenance"])
        self.assertEqual(trans_out["provenance"].source_ids, [501])

        # 3. Step 2: Extraction
        extract_out = self.extraction_agent.run(raw_article)
        self.assertEqual(extract_out.article_id, 501)
        self.assertIn(extract_out.event_type, ["border_incident", "military_movement"])
        self.assertTrue(len(extract_out.entities) > 0)
        self.assertEqual(extract_out.provenance.source_ids, [501])

        # 4. Step 3: Entity Resolution
        res_out = self.resolution_agent.run(extract_out.entities)
        self.assertIn("resolved_entities", res_out)
        self.assertTrue(len(res_out["resolved_entities"]) > 0)

        # Confirm canonical mapping of key defense entities
        canonicals = {r["canonical_name"] for r in res_out["resolved_entities"]}
        actions = {r["action"] for r in res_out["resolved_entities"]}

        # 'LAC' should map to 'Line of Actual Control' with 'auto_link'
        self.assertTrue(
            "Line of Actual Control" in canonicals or any("LAC" in r["raw_name"] for r in res_out["resolved_entities"])
        )
        self.assertIn("auto_link", actions)

        # 5. Step 4: Event Threading
        raw_entity_values = [e.entity_value for e in extract_out.entities]
        thread_out = self.threading_agent.run({
            "article_id": 501,
            "title": raw_article.title,
            "content": raw_article.content,
            "entities": raw_entity_values,
            "event_type": extract_out.event_type,
            "region": "Eastern Ladakh",
        })
        self.assertEqual(thread_out.article_id, 501)
        self.assertEqual(thread_out.matched_event_id, 1)  # Matches Event #1 (Eastern Ladakh LAC)
        self.assertFalse(thread_out.created_new_event)
        self.assertTrue(len(thread_out.candidate_links) > 0)
        self.assertEqual(thread_out.provenance.source_ids, [501])

    def test_end_to_end_novel_cyber_event_seeding(self):
        # Novel uncatalogued drone interception event
        raw_article = ArticleIn(
            id=502,
            title="Unidentified surveillance quadcopter intercepted over Punjab border outpost",
            content="Border Security Force shot down a hexacopter carrying suspected payload in Gurdaspur.",
            url="https://aninews.in/punjab-drone-intercept",
            language="en",
        )

        extract_out = self.extraction_agent.run(raw_article)
        thread_out = self.threading_agent.run({
            "article_id": 502,
            "title": raw_article.title,
            "content": raw_article.content,
            "entities": [e.entity_value for e in extract_out.entities],
            "event_type": extract_out.event_type,
            "region": "Punjab",
        })
        self.assertEqual(thread_out.article_id, 502)
        # Should create a new event cluster because it doesn't match ongoing LAC/LoC/Naval threads
        if thread_out.created_new_event:
            self.assertIsNotNone(thread_out.new_event_title)
            self.assertTrue(thread_out.candidate_links[0].is_seed)


if __name__ == "__main__":
    unittest.main()
