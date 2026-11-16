"""
Unit Tests for Multi-Tier LLM Fallback & SitRep Generation (Stage 3 Solid - Milestone M10).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from datetime import date
from unittest.mock import patch, MagicMock
from agents.report.sitrep_agent import GroundedSitRepAgent


def test_sitrep_fallback_to_secondary_llm():
    """When Groq fails, agent cleanly falls back to secondary cloud LLM."""
    agent = GroundedSitRepAgent()
    sample_articles = [
        {"id": 1, "title": "Border radar suite upgraded", "content": "Air Force installs radar.", "ring": 1, "source_name": "PIB"}
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Air Force installs radar [Source #1]."}}]
    }

    with patch("common.config.settings.GROQ_API_KEY", "mock_groq_key"), \
         patch("common.config.settings.LLM_FALLBACK_API_KEY", "mock_fallback_key"), \
         patch("httpx.post", side_effect=[Exception("Groq timeout"), mock_resp]):

        report = agent.generate_report(report_date=date(2026, 11, 16), articles=sample_articles)
        assert "secondary_llm" in report.provenance.method
        assert len(report.sentences) == 1
        assert report.sentences[0].is_supported is True
        assert report.sentences[0].citations == [1]


def test_sitrep_fallback_to_ollama_offline():
    """When cloud LLMs fail, agent queries local Ollama hook."""
    agent = GroundedSitRepAgent()
    sample_articles = [
        {"id": 2, "title": "Patrols verified along LAC", "content": "Troops observe sector.", "ring": 1, "source_name": "The Hindu"}
    ]

    mock_ollama_resp = MagicMock()
    mock_ollama_resp.status_code = 200
    mock_ollama_resp.json.return_value = {
        "response": "Troops observe sector along the frontier line [Source #2]."
    }

    with patch("common.config.settings.GROQ_API_KEY", None), \
         patch("common.config.settings.LLM_FALLBACK_API_KEY", None), \
         patch("common.config.settings.OLLAMA_HOST", "http://localhost:11434"), \
         patch("httpx.post", return_value=mock_ollama_resp):

        report = agent.generate_report(report_date=date(2026, 11, 16), articles=sample_articles)
        assert "offline_ollama" in report.provenance.method
        assert len(report.sentences) == 1
        assert report.sentences[0].is_supported is True
        assert report.sentences[0].citations == [2]


def test_sitrep_fallback_to_deterministic_synthesizer():
    """When all external APIs are offline, deterministic grounded generator succeeds."""
    agent = GroundedSitRepAgent()
    sample_articles = [
        {"id": 3, "title": "Naval exercise in Arabian Sea", "content": "Warships execute tactical maneuvers.", "ring": 1, "source_name": "ANI"}
    ]

    report = agent.generate_report(report_date=date(2026, 11, 16), articles=sample_articles, force_fallback=True)
    assert report.provenance.method == "deterministic_grounded_synthesis_v2"
    assert report.grounding_rate >= 0.75
    assert len(report.sentences) > 0
