"""
Agent contract tests for Raksha AI.
Verifies that all stub and production agents implement the BaseAgent/Agent protocol,
return correct typed schemas, and populate provenance metadata.
"""
import pytest
from datetime import date
from agents.base import Agent, BaseAgent
from agents.translation.stub import TranslationAgentStub
from agents.extraction.stub import ExtractionAgentStub
from agents.resolution.stub import ResolutionAgentStub
from agents.threading.stub import ThreadingAgentStub
from agents.scoring.classifier_v0 import ThreatClassifierV0
from agents.report.stub import ReportAgentStub
from agents.profile.stub import ProfileAgentStub
from agents.corroboration.stub import CorroborationAgentStub

from common.schemas.articles import ArticleIn
from common.schemas.intelligence import (
    CorroborationIn,
    ProfileSummaryIn,
    SitRepIn,
    ThreatClassifyIn,
)
from common.schemas.events import EventThreadingIn


def test_agent_protocol_conformance():
    """Verify all agents conform to the runtime Agent protocol."""
    agents = [
        TranslationAgentStub(),
        ExtractionAgentStub(),
        ResolutionAgentStub(),
        ThreadingAgentStub(),
        ThreatClassifierV0(),
        ReportAgentStub(),
        ProfileAgentStub(),
        CorroborationAgentStub(),
    ]
    for ag in agents:
        assert isinstance(ag, Agent)
        assert hasattr(ag, "name") and ag.name
        assert hasattr(ag, "version") and ag.version
        assert callable(ag.run)
        assert callable(ag.run_batch)


def test_translation_stub_contract():
    agent = TranslationAgentStub()
    article = ArticleIn(id=1, title="Test Urdu Article", content="Urdu text", url="https://dawn.com/1", language="ur")
    out = agent.run(article)
    assert out["is_translated"] is True
    assert "[Translated from ur]" in out["translated_text"]
    assert out["provenance"].method == "stub_translation"


def test_extraction_stub_contract():
    agent = ExtractionAgentStub()
    article = ArticleIn(
        id=2,
        title="Rafale jets deployed near Ladakh border by Indian Army",
        content="Patrols intensified.",
        url="https://thehindu.com/2",
    )
    out = agent.run(article)
    assert out.article_id == 2
    assert out.event_type == "border_incident"
    entity_names = [e.entity_value for e in out.entities]
    assert "Ladakh" in entity_names
    assert "Rafale" in entity_names
    assert out.provenance.model_version.startswith("extraction_agent_stub")


def test_report_stub_grounding():
    agent = ReportAgentStub()
    sitrep_in = SitRepIn(report_date=date(2026, 10, 31), article_ids=[101, 102])
    out = agent.run(sitrep_in)
    assert out.grounding_rate == 1.0
    assert len(out.sentences) > 0
    for s in out.sentences:
        assert s.is_supported is True
        assert len(s.citations) > 0


def test_profile_stub_sensitive_attribute_filter():
    agent = ProfileAgentStub()
    profile_in = ProfileSummaryIn(entity_id=5, entity_name="Major Sharma", entity_type="PERSON")
    out = agent.run(profile_in)
    assert out.entity_name == "Major Sharma"
    for f in out.facts:
        text = f.fact.lower()
        assert "religion" not in text
        assert "caste" not in text
        assert "ethnicity" not in text


def test_corroboration_stub_contract():
    agent = CorroborationAgentStub()
    corrob_in = CorroborationIn(
        source_article_id=1,
        source_text="Indian forces neutralized infiltration.",
        source_ring=1,
        compare_article_id=2,
        compare_text="Adversary denies infiltration.",
        compare_ring=2,
    )
    out = agent.run(corrob_in)
    assert len(out.links) == 1
    assert out.links[0].relation == "CONTRADICTS"
    assert out.disinformation_indicator > 0.5
