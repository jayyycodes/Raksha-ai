"""
Threat Classifier v0 ΓÇö Rule-based article threat assessment.
Owner: Jaish
Stage: 1 (MVP)

Determines LOW, MEDIUM, or HIGH threat level (mapped to 1-10)
from event types, threat keywords, and source ring weights.
"""
from typing import List, Set, Tuple
from common.constants import (
    RING_INDIA,
    RING_ADVERSARY,
    RING_REGIONAL,
    RING_GLOBAL,
)
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import (
    ThreatCategory,
    ThreatClassifyIn,
    ThreatClassifyOut,
)
from agents.base import BaseAgent


# High threat indicators
HIGH_KEYWORDS = {
    "artillery", "firing", "cross-border firing", "infiltration", "casualties",
    "casualty", "martyred", "skirmish", "standoff", "clash", "nuclear",
    "ballistic missile", "hypersonic", "air strike", "airstrike", "ied blast",
    "ied", "suicide attack", "ambush", "terror attack", "hostage", "ceasefire violation",
    "border intrusion", "lac standoff", "loc firing", "war declared", "mobilization",
}

# Medium threat indicators
MEDIUM_KEYWORDS = {
    "patrol", "troop deployment", "military exercise", "war games", "warship",
    "frigate", "submarine", "fighter jet", "scramble", "drone spotted", "uav",
    "radar", "air defense", "drdo test", "missile test", "procurement",
    "defense pact", "surveillance", "cyber attack", "malware", "espionage",
    "disinformation", "propaganda", "sanctions", "expulsion of diplomat",
}

# Inherent event type base threat weights (1-10 scale)
EVENT_TYPE_BASE_SCORES = {
    "nuclear": 9.0,
    "terror_activity": 8.0,
    "border_incident": 7.5,
    "aerial": 7.0,
    "cyber_attack": 6.5,
    "military_movement": 6.0,
    "naval": 5.5,
    "disinformation": 5.0,
    "diplomatic": 4.0,
    "general": 2.5,
}


class ThreatClassifierV0(BaseAgent[ThreatClassifyIn, ThreatClassifyOut]):
    name = "threat_classifier_v0"
    version = "0.1.0"

    def _extract_matched_keywords(self, text: str) -> Tuple[List[str], List[str]]:
        text_lower = text.lower()
        matched_high = [kw for kw in HIGH_KEYWORDS if kw in text_lower]
        matched_med = [kw for kw in MEDIUM_KEYWORDS if kw in text_lower]
        return matched_high, matched_med

    def classify(
        self,
        title: str,
        content: str = "",
        event_type: str = "general",
        ring: int = 1,
    ) -> ThreatClassifyOut:
        """
        Classifies the threat level of an article.
        """
        full_text = f"{title} {content}".strip()
        matched_high, matched_med = self._extract_matched_keywords(full_text)

        base_score = EVENT_TYPE_BASE_SCORES.get(event_type.lower(), 2.5)

        # Keyword modifier
        keyword_score = (len(matched_high) * 2.0) + (len(matched_med) * 0.8)

        # Ring multiplier: Adversary media (Ring 2) escalates sensitivity if aggressive
        ring_multiplier = 1.0
        if ring == RING_ADVERSARY:
            ring_multiplier = 1.15
        elif ring == RING_INDIA:
            ring_multiplier = 1.0
        elif ring == RING_REGIONAL:
            ring_multiplier = 1.05

        computed_score = (base_score + keyword_score) * ring_multiplier
        # Clamp score between 1.0 and 10.0
        final_score = max(1.0, min(10.0, round(computed_score, 1)))

        # Categorize
        # High category requires active high-threat indicators or critical score above 8.0
        if len(matched_high) >= 2 or (len(matched_high) >= 1 and final_score >= 7.0) or final_score >= 8.2:
            category = ThreatCategory.HIGH
            level_int = max(8, min(10, int(round(final_score))))
        elif final_score >= 4.0 or len(matched_med) >= 1 or len(matched_high) == 1:
            category = ThreatCategory.MEDIUM
            level_int = max(4, min(7, int(round(final_score))))
        else:
            category = ThreatCategory.LOW
            level_int = max(1, min(3, int(round(final_score))))

        all_matched = matched_high + matched_med
        reasoning = (
            f"Event type '{event_type}' (base {base_score}), "
            f"{len(matched_high)} high-threat keywords ({', '.join(matched_high) if matched_high else 'none'}), "
            f"{len(matched_med)} medium-threat keywords, Ring {ring} weighting factor {ring_multiplier}."
        )

        return ThreatClassifyOut(
            category=category,
            threat_level=level_int,
            score=final_score,
            matched_keywords=all_matched,
            reasoning=reasoning,
            provenance=Provenance(
                source_ids=[],
                method="rule_keyword_event_v0",
                model_version=f"{self.name}:{self.version}",
                confidence=0.85 if all_matched else 0.70,
                claim_status=ClaimStatus.REPORTED,
                source_type=SourceType.PUBLIC,
            ),
        )

    def run(self, input_data: ThreatClassifyIn) -> ThreatClassifyOut:
        return self.classify(
            title=input_data.title,
            content=input_data.content or "",
            event_type=input_data.event_type,
            ring=input_data.ring or 1,
        )
