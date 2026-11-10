"""
Unit tests for Stage 2 TranslationAgent.
Floor 2 — Language & Knowledge Agents
"""
import unittest
from unittest.mock import MagicMock, patch

from agents.base import Agent, BaseAgent
from agents.translation.agent import TranslationAgent
from common.schemas.articles import ArticleIn
from common.schemas.provenance import Provenance
from engine.translator import TranslationResult


class TestTranslationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = TranslationAgent()

    def test_agent_protocol_conformance(self):
        self.assertIsInstance(self.agent, Agent)
        self.assertIsInstance(self.agent, BaseAgent)
        self.assertEqual(self.agent.name, "translation_agent")
        self.assertEqual(self.agent.version, "0.2.0")
        self.assertTrue(callable(self.agent.run))
        self.assertTrue(callable(self.agent.run_batch))

    def test_english_article_skipped_passthrough(self):
        article = ArticleIn(
            id=101,
            title="Indian Army conducts joint exercise in Ladakh",
            content="Troops participated in high-altitude drills.",
            url="https://example.com/en/1",
            language="en",
        )
        out = self.agent.run(article)
        self.assertEqual(out["article_id"], 101)
        self.assertEqual(out["original_language"], "en")
        self.assertFalse(out["is_translated"])
        self.assertEqual(out["translated_title"], "Indian Army conducts joint exercise in Ladakh")
        self.assertEqual(out["translated_text"], "Troops participated in high-altitude drills.")
        self.assertEqual(out["provenance"].method, "passthrough_english")
        self.assertEqual(out["provenance"].source_ids, [101])
        self.assertEqual(out["provenance"].confidence, 1.0)

    def test_dict_input_compatibility(self):
        dict_input = {
            "id": 102,
            "title": "Border patrol alert",
            "content": "Alert raised along the border.",
            "language": "en",
        }
        out = self.agent.run(dict_input)
        self.assertEqual(out["article_id"], 102)
        self.assertFalse(out["is_translated"])
        self.assertEqual(out["provenance"].source_ids, [102])

    def test_unsupported_input_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.agent.run("just a string")

    @patch("agents.translation.agent.translate")
    def test_foreign_language_successful_translation(self, mock_translate):
        # Mock successful translation result
        success_result = TranslationResult(
            text="Pakistani security forces arrest four suspects",
            status="success",
            source_lang="ur",
            target_lang="en",
            error=None,
            original_text="پاکستانی فورسز نے چار ملزمان کو گرفتار کر لیا",
        )
        mock_translate.return_value = success_result

        article = ArticleIn(
            id=103,
            title="خبر",
            content="پاکستانی فورسز نے چار ملزمان کو گرفتار کر لیا",
            url="https://example.com/ur/1",
            language="ur",
        )
        out = self.agent.run(article)
        self.assertEqual(out["article_id"], 103)
        self.assertEqual(out["original_language"], "ur")
        self.assertTrue(out["is_translated"])
        self.assertEqual(out["translated_text"], "Pakistani security forces arrest four suspects")
        self.assertEqual(out["provenance"].method, "helsinki_opus_mt")
        self.assertEqual(out["provenance"].confidence, 0.90)

    @patch("agents.translation.agent.translate")
    def test_foreign_language_degraded_translation(self, mock_translate):
        failed_result = TranslationResult(
            text="",
            status="failed",
            source_lang="zh",
            target_lang="en",
            error="Translation model unavailable",
            original_text="some text",
        )
        mock_translate.return_value = failed_result

        article = ArticleIn(
            id=104,
            title="标题",
            content="some text",
            url="https://example.com/zh/1",
            language="zh",
        )
        out = self.agent.run(article)
        self.assertEqual(out["article_id"], 104)
        self.assertFalse(out["is_translated"])
        self.assertEqual(out["provenance"].method, "helsinki_opus_mt_degraded")
        self.assertEqual(out["provenance"].confidence, 0.40)

    def test_batch_translation(self):
        articles = [
            ArticleIn(id=1, title="Article 1", content="Text 1", url="http://1", language="en"),
            ArticleIn(id=2, title="Article 2", content="Text 2", url="http://2", language="en"),
        ]
        results = self.agent.run_batch(articles)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["article_id"], 1)
        self.assertEqual(results[1]["article_id"], 2)


if __name__ == "__main__":
    unittest.main()
