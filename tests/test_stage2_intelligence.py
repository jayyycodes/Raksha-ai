"""
Stage 2 (Mid) Unit Tests for Intelligence & Generation Agents (Floor 3 - Jaish).
Tests:
- Threat Scoring Agent (regional scoring, volume factor, ring weighting, trend)
- Anomaly Agent (volume spikes, threat escalations, sentiment anomalies)
- Grounded SitRep Agent (citation extraction, grounding verification, fallback synthesis)
- Profile Summary Agent (candidate-to-profile rule, sensitive-attribute filter)
- Corroboration Agent (CORROBORATED_BY, CONTRADICTS, disinformation indicator)
"""
from datetime import date
import pytest

from common.constants import (
    DEFENCE_REGIONS,
    RING_INDIA,
    RING_ADVERSARY,
    RING_GLOBAL,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
)
from common.schemas.provenance import ClaimStatus
from common.schemas.intelligence import ProfileFactOut
from agents.scoring.regional_scorer import ThreatScoringAgent, map_article_to_regions
from agents.scoring.anomaly_agent import AnomalyAgent
from agents.report.sitrep_agent import GroundedSitRepAgent
from agents.profile.profile_agent import (
    ProfileSummaryAgent,
    is_eligible_for_profile,
    contains_sensitive_attribute,
)
from agents.corroboration.corroboration_agent import CorroborationAgent


# ── 1. Threat Scoring Agent Tests ──────────────────────────────────────────

def test_map_article_to_regions():
    regions = map_article_to_regions("Artillery movement along LAC in Eastern Ladakh")
    assert "LAC-Ladakh" in regions

    loc_regions = map_article_to_regions("Infiltration alert in Poonch along Line of Control")
    assert "LoC-Kashmir" in loc_regions

    maritime_regions = map_article_to_regions("Submarine tracked in Arabian Sea near Malacca")
    assert "Indian-Ocean" in maritime_regions

    cyber_regions = map_article_to_regions("Ransomware attack targets power grid telemetry")
    assert "Cyber" in cyber_regions


def test_regional_threat_scoring_calculation():
    scorer = ThreatScoringAgent()
    articles = [
        {
            "id": 1,
            "title": "Cross-border artillery firing with multiple casualties",
            "content": "Heavy exchanges across LoC posts.",
            "event_type": "border_incident",
            "ring": RING_ADVERSARY,
            "threat_level": 9,
            "sentiment": "alarming",
        },
        {
            "id": 2,
            "title": "Infiltration squad intercepted near forward post",
            "content": "Terrorists engaged.",
            "event_type": "terror_activity",
            "ring": RING_INDIA,
            "threat_level": 8,
            "sentiment": "aggressive",
        },
    ]

    out = scorer.calculate_score_for_articles(
        region="LoC-Kashmir",
        articles=articles,
        previous_score=4.0,
    )
    assert out.region == "LoC-Kashmir"
    assert out.score >= 6.5
    assert out.trend == "rising"
    assert out.article_count == 2
    assert out.provenance.method == "weighted_regional_threat_v2"


def test_regional_scoring_all_nine_regions():
    scorer = ThreatScoringAgent()
    sample_articles = [
        {"id": 1, "title": "Standoff in Depsang plains Ladakh", "ring": 2, "threat_level": 8},
        {"id": 2, "title": "CERT-In identifies critical malware payload", "ring": 1, "threat_level": 7},
    ]
    results = scorer.calculate_all_regions(sample_articles)
    assert len(results) == len(DEFENCE_REGIONS)
    regions_covered = {r.region for r in results}
    assert regions_covered == set(DEFENCE_REGIONS)


# ── 2. Anomaly Detection Tests ─────────────────────────────────────────────

def test_anomaly_detection_volume_surge():
    agent = AnomalyAgent()
    articles = [{"id": i, "threat_level": 4, "sentiment": "neutral"} for i in range(12)]
    out = agent.detect_region_anomaly(
        region="LAC-Ladakh",
        current_articles=articles,
        baseline_daily_average=3.0,
    )
    assert out.is_anomaly is True
    assert out.deviation_factor == 4.0
    assert out.alert_severity in (SEVERITY_HIGH, SEVERITY_CRITICAL)


def test_anomaly_detection_normal_baseline():
    agent = AnomalyAgent()
    articles = [{"id": 1, "threat_level": 3, "sentiment": "neutral"}]
    out = agent.detect_region_anomaly(
        region="Western-Border",
        current_articles=articles,
        baseline_daily_average=2.0,
    )
    assert out.is_anomaly is False
    assert out.alert_severity is None


def test_anomaly_detection_sentiment_spike():
    agent = AnomalyAgent()
    articles = [
        {"id": 1, "threat_level": 5, "sentiment": "alarming"},
        {"id": 2, "threat_level": 6, "sentiment": "aggressive"},
        {"id": 3, "threat_level": 5, "sentiment": "alarming"},
    ]
    out = agent.detect_region_anomaly(
        region="LoC-Kashmir",
        current_articles=articles,
        baseline_daily_average=3.0,
    )
    assert out.is_anomaly is True
    assert out.alert_severity == SEVERITY_MEDIUM


# ── 3. Grounded SitRep Tests ───────────────────────────────────────────────

def test_sitrep_citation_extraction_and_grounding():
    agent = GroundedSitRepAgent()
    valid_ids = {101, 102}

    # Supported sentence with valid citation
    s1, is_sup1 = agent._extract_citations("Patrols intensified in western sector [Source #101].", valid_ids)
    assert s1 == [101]
    assert is_sup1 is True

    # Unsupported sentence with no citations
    s2, is_sup2 = agent._extract_citations("Unconfirmed rumors circulated online.", valid_ids)
    assert s2 == []
    assert is_sup2 is False

    # Fake citation not in valid_ids
    s3, is_sup3 = agent._extract_citations("Fabricated report citing fake source [Source #999].", valid_ids)
    assert s3 == []
    assert is_sup3 is False


def test_sitrep_deterministic_synthesis():
    agent = GroundedSitRepAgent()
    articles = [
        {"id": 101, "title": "Rafale aircraft conduct training sortie over Ladakh", "ring": 1, "event_type": "aerial"},
        {"id": 102, "title": "Boundary talks held between foreign ministries", "ring": 1, "event_type": "diplomatic"},
    ]
    rep = agent.generate_report(
        report_date=date(2026, 11, 11),
        articles=articles,
        force_fallback=True,
    )
    assert rep.article_count == 2
    assert rep.grounding_rate == 1.0
    assert len(rep.sentences) == 2
    for s in rep.sentences:
        assert s.is_supported is True
        assert len(s.citations) > 0


# ── 4. Profile Summary & Sensitive-Attribute Filter Tests ─────────────────

def test_candidate_to_profile_rule():
    # 2 mentions from 1 source: not eligible
    assert is_eligible_for_profile(mention_count=2, source_count=1) is False
    # 3 mentions from 1 source: not eligible
    assert is_eligible_for_profile(mention_count=3, source_count=1) is False
    # 3 mentions from 2 sources: eligible!
    assert is_eligible_for_profile(mention_count=3, source_count=2) is True
    # 5 mentions from 3 sources: eligible!
    assert is_eligible_for_profile(mention_count=5, source_count=3) is True
    # Analyst promoted: eligible even with 1 mention
    assert is_eligible_for_profile(mention_count=1, source_count=1, analyst_promoted=True) is True


def test_sensitive_attribute_filter_blocks_protected_attributes():
    agent = ProfileSummaryAgent()

    # Verify detection function
    is_sens, term = contains_sensitive_attribute("The individual belongs to a prominent religious faith.")
    assert is_sens is True
    assert term.lower() == "religious"

    caste_sens, _ = contains_sensitive_attribute("Reference to community caste background.")
    assert caste_sens is True

    health_sens, _ = contains_sensitive_attribute("Undergoing treatment for severe medical condition.")
    assert health_sens is True

    clean_sens, _ = contains_sensitive_attribute("Officer served as Director General of Border Roads.")
    assert clean_sens is False

    # Verify filter strips sensitive facts
    facts = [
        ProfileFactOut(fact="Served as Commander of Northern Strike Corps.", claim_status=ClaimStatus.OFFICIAL_DESIGNATION),
        ProfileFactOut(fact="Belongs to a specific religion and caste hierarchy.", claim_status=ClaimStatus.REPORTED),
        ProfileFactOut(fact="Mentioned in defence procurement modernization reports.", claim_status=ClaimStatus.REPORTED),
    ]
    filtered = agent.filter_facts(facts)
    assert len(filtered) == 2
    assert all("caste" not in f.fact.lower() for f in filtered)
    assert all("religion" not in f.fact.lower() for f in filtered)


def test_profile_summary_generation():
    agent = ProfileSummaryAgent()
    articles = [
        {"id": 1, "title": "DRDO reviews indigenous radar project", "source_name": "PIB", "event_type": "military_movement", "entities": ["DRDO"]},
        {"id": 2, "title": "Flight trials of radar system", "source_name": "The Hindu", "event_type": "military_movement", "entities": ["DRDO", "IAF"]},
        {"id": 3, "title": "Radar procurement approved", "source_name": "ANI", "event_type": "military_movement", "entities": ["DRDO"]},
    ]
    summary = agent.generate_summary(
        entity_id=10,
        entity_name="DRDO",
        entity_type="ORGANISATION",
        articles=articles,
    )
    assert summary.entity_name == "DRDO"
    assert len(summary.facts) == 3
    assert "IAF" in summary.associated_entities
    assert summary.provenance.method == "attributed_profile_compiler_v2"


# ── 5. Corroboration Agent Tests ──────────────────────────────────────────

def test_corroboration_agent_corroborated_by():
    agent = CorroborationAgent()
    link = agent.analyze_pair(
        source_article_id=1,
        source_text="Indian Navy confirms anti-piracy escort in Gulf of Aden.",
        source_ring=RING_INDIA,
        compare_article_id=2,
        compare_text="International maritime agency confirms successful escort operation by Indian warship.",
        compare_ring=RING_GLOBAL,
    )
    assert link.relation == "CORROBORATED_BY"
    assert link.confidence >= 0.8


def test_corroboration_agent_contradicts():
    agent = CorroborationAgent()
    link = agent.analyze_pair(
        source_article_id=1,
        source_text="Army spokesperson confirms foiling infiltration bid with no loss of life.",
        source_ring=RING_INDIA,
        compare_article_id=2,
        compare_text="Adversary military spokesperson denies incursion and claims heavy casualties inflicted.",
        compare_ring=RING_ADVERSARY,
    )
    assert link.relation == "CONTRADICTS"
    assert "Conflicting framing" in link.explanation or "conflict" in link.explanation or "divergence" in link.explanation
