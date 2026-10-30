"""
Unit tests for Threat Classifier v0 (Jaish).
"""
import pytest
from agents.scoring.classifier_v0 import ThreatClassifierV0
from common.schemas.intelligence import ThreatCategory, ThreatClassifyIn


@pytest.fixture
def classifier():
    return ThreatClassifierV0()


def test_high_threat_keywords(classifier):
    item = ThreatClassifyIn(
        title="Heavy cross-border artillery firing reported along LoC with casualties",
        content="Forward posts targeted.",
        event_type="border_incident",
        ring=2,
    )
    result = classifier.run(item)
    assert result.category == ThreatCategory.HIGH
    assert result.threat_level >= 8
    assert "artillery" in result.matched_keywords or "casualties" in result.matched_keywords
    assert result.provenance.method == "rule_keyword_event_v0"


def test_medium_threat_keywords(classifier):
    item = ThreatClassifyIn(
        title="Indian Navy frigate engages in joint surveillance and patrol exercise",
        content="Maritime patrol ongoing.",
        event_type="naval",
        ring=1,
    )
    result = classifier.run(item)
    assert result.category == ThreatCategory.MEDIUM
    assert 4 <= result.threat_level <= 7


def test_low_threat_general(classifier):
    item = ThreatClassifyIn(
        title="Bilateral cultural delegation visits ancient Buddhist heritage sites",
        content="Discussion on tourism and cultural ties.",
        event_type="general",
        ring=1,
    )
    result = classifier.run(item)
    assert result.category == ThreatCategory.LOW
    assert result.threat_level <= 3


def test_adversary_ring_weighting(classifier):
    # Same content, different ring
    out_ring1 = classifier.classify(title="Troop patrol sighted near border pass", event_type="general", ring=1)
    out_ring2 = classifier.classify(title="Troop patrol sighted near border pass", event_type="general", ring=2)
    assert out_ring2.score >= out_ring1.score
