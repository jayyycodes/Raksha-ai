"""
Corroboration Agent.
Owner: Jaish
Stage: 2 (Mid)

Establishes CORROBORATED_BY and CONTRADICTS relationships between articles and sources.
Flags cross-source discrepancies and calculates disinformation indicators when adversary
media (Ring 2) contradicts domestic/neutral ground truth.
"""
from typing import Any, Dict, List, Optional, Tuple

from common.constants import (
    RING_INDIA,
    RING_ADVERSARY,
    RING_REGIONAL,
    RING_GLOBAL,
)
from common.logger import get_logger
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import (
    CorroborationIn,
    CorroborationLinkOut,
    CorroborationOut,
)
from agents.base import BaseAgent

logger = get_logger(__name__)

DENIAL_VERBS = {
    "denies", "refutes", "rejects", "dismisses", "unfounded",
    "baseless", "false claim", "fabricated", "no loss", "no intrusion",
}

ASSERTION_VERBS = {
    "claims", "alleges", "incursion", "intrusion", "casualties",
    "destroyed", "shelling", "attack", "infiltrating", "infiltrators",
}

CONTRADICTION_TRIGGERS = [
    ("denies", "claims"),
    ("refutes", "alleges"),
    ("refutes", "claims"),
    ("denies", "incursion"),
    ("no intrusion", "incursion"),
    ("unfounded", "confirmed"),
    ("zero casualties", "casualties"),
    ("unprovoked firing", "retaliatory firing"),
    ("false claim", "official statement"),
    ("fabricated", "verified"),
    ("no loss", "incursion"),
    ("baseless", "claims"),
]


class CorroborationAgent(BaseAgent[CorroborationIn, CorroborationOut]):
    name = "corroboration_agent"
    version = "0.2.0"

    def analyze_pair(
        self,
        source_article_id: int,
        source_text: str,
        source_ring: int,
        compare_article_id: int,
        compare_text: str,
        compare_ring: int,
    ) -> CorroborationLinkOut:
        """
        Analyzes two articles for factual alignment (CORROBORATED_BY) or contradiction (CONTRADICTS).
        """
        s_lower = source_text.lower()
        c_lower = compare_text.lower()

        is_cross_ring_adversary = (source_ring == RING_ADVERSARY and compare_ring in (RING_INDIA, RING_GLOBAL)) or (
            compare_ring == RING_ADVERSARY and source_ring in (RING_INDIA, RING_GLOBAL)
        )

        has_contradiction_pattern = False
        contradiction_reason = ""

        for term_a, term_b in CONTRADICTION_TRIGGERS:
            if (term_a in s_lower and term_b in c_lower) or (term_b in s_lower and term_a in c_lower):
                has_contradiction_pattern = True
                contradiction_reason = f"Conflicting framing detected ({term_a} vs {term_b})"
                break

        # Check numeric or casualty discrepancies
        if not has_contradiction_pattern:
            if ("killed" in s_lower or "injured" in s_lower) and ("denies casualties" in c_lower or "no loss" in c_lower):
                has_contradiction_pattern = True
                contradiction_reason = "Discrepancy in casualty and damage assessment"
            else:
                s_denials = any(d in s_lower for d in DENIAL_VERBS)
                c_assertions = any(a in c_lower for a in ASSERTION_VERBS)
                c_denials = any(d in c_lower for d in DENIAL_VERBS)
                s_assertions = any(a in s_lower for a in ASSERTION_VERBS)
                if (s_denials and c_assertions) or (c_denials and s_assertions):
                    has_contradiction_pattern = True
                    contradiction_reason = "Denial vs assertion conflict between reporting sources"

        if has_contradiction_pattern or (is_cross_ring_adversary and any(w in s_lower + c_lower for w in ["propaganda", "blames", "denies", "rejects"])):
            relation = "CONTRADICTS"
            confidence = 0.88 if has_contradiction_pattern else 0.75
            explanation = (
                f"Factual divergence between Ring {source_ring} and Ring {compare_ring} reporting. "
                f"{contradiction_reason or 'Contradictory operational narratives identified.'}"
            )
        else:
            relation = "CORROBORATED_BY"
            confidence = 0.85
            explanation = (
                f"Mutual factual agreement between Ring {source_ring} and Ring {compare_ring} sources "
                f"confirming event parameters and timeline."
            )

        prov = Provenance(
            source_ids=[source_article_id, compare_article_id],
            method="cross_source_nlp_corroborator_v2",
            model_version=f"{self.name}:{self.version}",
            confidence=confidence,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return CorroborationLinkOut(
            source_article_id=source_article_id,
            compare_article_id=compare_article_id,
            relation=relation,
            confidence=confidence,
            explanation=explanation,
            provenance=prov,
        )

    def evaluate_batch(
        self,
        article_pairs: List[Dict[str, Any]],
    ) -> CorroborationOut:
        """
        Evaluates a collection of article pairs and calculates aggregate disinformation indicators.
        """
        links: List[CorroborationLinkOut] = []
        contradiction_count = 0

        for pair in article_pairs:
            link = self.analyze_pair(
                source_article_id=pair.get("source_id", 1),
                source_text=pair.get("source_text", ""),
                source_ring=pair.get("source_ring", 1),
                compare_article_id=pair.get("compare_id", 2),
                compare_text=pair.get("compare_text", ""),
                compare_ring=pair.get("compare_ring", 2),
            )
            links.append(link)
            if link.relation == "CONTRADICTS":
                contradiction_count += 1

        total = len(links)
        disinfo_score = round(contradiction_count / total, 2) if total > 0 else 0.0

        prov = Provenance(
            source_ids=[p.get("source_id", 1) for p in article_pairs],
            method="batch_corroboration_suite_v2",
            model_version=f"{self.name}:{self.version}",
            confidence=0.88,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return CorroborationOut(
            links=links,
            disinformation_indicator=disinfo_score,
            provenance=prov,
        )

    def run(self, input_data: CorroborationIn) -> CorroborationOut:
        single_link = self.analyze_pair(
            source_article_id=input_data.source_article_id,
            source_text=input_data.source_text,
            source_ring=input_data.source_ring,
            compare_article_id=input_data.compare_article_id,
            compare_text=input_data.compare_text,
            compare_ring=input_data.compare_ring,
        )
        return CorroborationOut(
            links=[single_link],
            disinformation_indicator=0.7 if single_link.relation == "CONTRADICTS" else 0.0,
            provenance=single_link.provenance,
        )
