"""
Regional Threat Scoring Agent.
Owner: Jaish
Stage: 2 (Mid)

Computes regional 1 to 10 threat scores with trend direction (rising, stable, falling)
based on article volume, event type severity, sentiment, ring weighting, and historical baselines.
"""
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from common.constants import (
    DEFENCE_REGIONS,
    RING_INDIA,
    RING_ADVERSARY,
    RING_REGIONAL,
    RING_GLOBAL,
    EVENT_TYPES,
)
from common.logger import get_logger
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import RegionalThreatScoreIn, RegionalThreatScoreOut
from agents.base import BaseAgent
from agents.scoring.classifier_v0 import ThreatClassifierV0

logger = get_logger(__name__)

# Keyword to region mapping rules
REGION_KEYWORDS: Dict[str, List[str]] = {
    "LAC-Ladakh": [
        "ladakh", "lac", "line of actual control", "depsang", "galwan", "pangong",
        "daulat beg oldi", "chushul", "demchok", "hot springs", "eastern ladakh", "spanggur",
    ],
    "LAC-Arunachal": [
        "arunachal", "tawang", "kameng", "subansiri", "siang", "yangtse", "dibang",
        "walong", "eastern border", "mcmallon line", "mcmahon line",
    ],
    "LoC-Kashmir": [
        "loc", "line of control", "kashmir", "poonch", "rajouri", "kupwara",
        "uri", "baramulla", "srinagar", "jammu", "pir panjal", "akhnoor", "ceasefire violation",
    ],
    "Western-Border": [
        "punjab border", "rajasthan border", "sir creek", "gujarat border",
        "thar", "munabao", "wagah", "attari", "western command", "pakistan border",
    ],
    "Indian-Ocean": [
        "indian ocean", "arabian sea", "bay of bengal", "andaman", "nicobar",
        "malacca", "choke point", "maritime", "submarine", "warship", "naval patrol",
        "chinese vessel", "spy ship", "eez",
    ],
    "Northeast": [
        "manipur", "assam", "nagaland", "mizoram", "tripura", "myanmar border",
        "insurgency", "ulpfa", "nscn", "northeast security",
    ],
    "Cyber": [
        "cyber", "malware", "ransomware", "hack", "cert-in", "power grid",
        "espionage", "phishing", "scam", "trojan", "ddos", "critical infrastructure",
    ],
    "Global-Strategic": [
        "nuclear", "quad", "un security council", "pentagon", "iaea", "hypersonic",
        "geopolitical", "foreign ministry", "sanctions", "treaty",
    ],
    "Internal-Security": [
        "naxal", "cprf", "maoist", "bastar", "sukma", "chhattisgarh",
        "ied", "counter-terror", "nia", "internal disturbance",
    ],
}

# Baseline resting threat levels (1.0 to 3.5) for regions during quiet periods
BASELINE_RESTING_SCORES: Dict[str, float] = {
    "LAC-Ladakh": 3.0,
    "LAC-Arunachal": 2.8,
    "LoC-Kashmir": 3.2,
    "Western-Border": 2.2,
    "Indian-Ocean": 2.5,
    "Northeast": 2.0,
    "Internal-Security": 2.2,
    "Cyber": 2.5,
    "Global-Strategic": 2.0,
}


def map_article_to_regions(title: str, content: str = "", entities: Optional[List[str]] = None) -> List[str]:
    """
    Identifies which defence regions an article relates to using title, content, and entities.
    Returns matched regions (defaults to 'Global-Strategic' if no specific geographic region matches).
    """
    text = f"{title} {content} {' '.join(entities or [])}".lower()
    matched = []

    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matched.append(region)

    if not matched:
        if any(kw in text for kw in ["cyber", "network", "data breach", "malware"]):
            matched.append("Cyber")
        else:
            matched.append("Global-Strategic")

    return matched


class ThreatScoringAgent(BaseAgent[RegionalThreatScoreIn, RegionalThreatScoreOut]):
    name = "threat_scoring_agent"
    version = "0.2.0"

    def __init__(self):
        self.classifier_v0 = ThreatClassifierV0()

    def calculate_score_for_articles(
        self,
        region: str,
        articles: List[Dict[str, Any]],
        previous_score: Optional[float] = None,
    ) -> RegionalThreatScoreOut:
        """
        Calculates the threat score for a single region given its associated articles.
        """
        resting_base = BASELINE_RESTING_SCORES.get(region, 2.0)
        article_count = len(articles)

        if article_count == 0:
            current_score = resting_base
            top_events = []
            trend = "stable"
        else:
            threat_levels: List[float] = []
            ring_weights: List[float] = []
            high_severity_count = 0
            alarming_sentiment_count = 0
            event_types_seen = set()

            for art in articles:
                # Article threat level (1 to 10)
                level = art.get("threat_level")
                if level is None:
                    # Run classifier v0 on the fly
                    classified = self.classifier_v0.classify(
                        title=art.get("title", ""),
                        content=art.get("content", ""),
                        event_type=art.get("event_type", "general"),
                        ring=art.get("ring", 1),
                    )
                    level = classified.threat_level

                threat_levels.append(float(level))

                # Ring multiplier
                ring = art.get("ring", 1)
                if ring == RING_ADVERSARY:
                    ring_weights.append(1.25)
                elif ring == RING_REGIONAL:
                    ring_weights.append(1.05)
                else:
                    ring_weights.append(1.0)

                # Sentiment and event type flags
                sentiment = str(art.get("sentiment", "neutral")).lower()
                if sentiment in ("alarming", "aggressive"):
                    alarming_sentiment_count += 1

                event_type = str(art.get("event_type", "general")).lower()
                event_types_seen.add(event_type)
                if event_type in ("nuclear", "terror_activity", "border_incident", "cyber_attack"):
                    high_severity_count += 1

            # 1. Weighted threat average
            weighted_threat_sum = sum(t * w for t, w in zip(threat_levels, ring_weights))
            avg_threat = weighted_threat_sum / sum(ring_weights)

            # 2. Volume surge factor (logarithmic)
            volume_factor = min(2.5, round(math.log10(article_count + 1) * 1.5, 2))

            # 3. Severity & sentiment bonus
            severity_bonus = min(2.0, (high_severity_count * 0.4) + (alarming_sentiment_count * 0.2))

            # Composite formula
            raw_score = (avg_threat * 0.6) + (resting_base * 0.2) + volume_factor + severity_bonus
            current_score = max(1.0, min(10.0, round(raw_score, 1)))

            top_events = list(event_types_seen)[:4]

            # 4. Trend direction
            if previous_score is not None:
                diff = current_score - previous_score
                if diff >= 0.4:
                    trend = "rising"
                elif diff <= -0.4:
                    trend = "falling"
                else:
                    trend = "stable"
            else:
                # If no previous score, infer trend from volume and severity
                if current_score >= 7.0 or volume_factor >= 1.5:
                    trend = "rising"
                elif current_score <= 3.0:
                    trend = "falling"
                else:
                    trend = "stable"

        prov = Provenance(
            source_ids=[a.get("id") for a in articles if a.get("id") is not None],
            method="weighted_regional_threat_v2",
            model_version=f"{self.name}:{self.version}",
            confidence=0.88 if article_count > 0 else 0.70,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return RegionalThreatScoreOut(
            region=region,
            score=current_score,
            trend=trend,
            article_count=article_count,
            top_events=top_events,
            calculated_at=datetime.now(timezone.utc),
            provenance=prov,
        )

    def calculate_all_regions(
        self,
        articles: List[Dict[str, Any]],
        previous_scores: Optional[Dict[str, float]] = None,
    ) -> List[RegionalThreatScoreOut]:
        """
        Computes scores for all 9 strategic defence regions simultaneously.
        """
        previous_scores = previous_scores or {}
        # Partition articles by region
        region_buckets: Dict[str, List[Dict[str, Any]]] = {reg: [] for reg in DEFENCE_REGIONS}

        for art in articles:
            assigned_regions = art.get("regions") or map_article_to_regions(
                title=art.get("title", ""),
                content=art.get("content", ""),
                entities=art.get("entities", []),
            )
            for reg in assigned_regions:
                if reg in region_buckets:
                    region_buckets[reg].append(art)

        results = []
        for reg in DEFENCE_REGIONS:
            prev = previous_scores.get(reg)
            res = self.calculate_score_for_articles(
                region=reg,
                articles=region_buckets[reg],
                previous_score=prev,
            )
            results.append(res)

        return results

    def run(self, input_data: RegionalThreatScoreIn) -> RegionalThreatScoreOut:
        # Default run method conforming to Agent Protocol
        articles: List[Dict[str, Any]] = []
        # Attempt to load from DB if available
        try:
            from common.db import get_db
            from sqlalchemy import text
            cutoff = datetime.now(timezone.utc) - timedelta(hours=input_data.window_hours)
            with get_db() as db:
                rows = db.execute(
                    text("""
                        SELECT a.id, a.title, a.content, s.ring, an.event_type, an.sentiment, an.threat_level
                        FROM articles a
                        LEFT JOIN sources s ON a.source_id = s.id
                        LEFT JOIN article_analysis an ON a.id = an.article_id
                        WHERE a.published_at >= :cutoff
                    """),
                    {"cutoff": cutoff},
                ).mappings().all()
                for r in rows:
                    art_dict = dict(r)
                    if input_data.region in map_article_to_regions(art_dict["title"], art_dict.get("content") or ""):
                        articles.append(art_dict)
        except Exception as e:
            logger.debug(f"DB query skipped or failed in regional scoring: {e}")

        return self.calculate_score_for_articles(region=input_data.region, articles=articles)
