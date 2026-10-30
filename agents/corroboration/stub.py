"""
Corroboration Agent Stub.
Owner: Jaish
Stage: 1 (Contract Stub)

Identifies CORROBORATED_BY and CONTRADICTS relationships between reports.
"""
from common.schemas.intelligence import (
    CorroborationIn,
    CorroborationLinkOut,
    CorroborationOut,
)
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class CorroborationAgentStub(BaseAgent[CorroborationIn, CorroborationOut]):
    name = "corroboration_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: CorroborationIn) -> CorroborationOut:
        prov = Provenance(
            source_ids=[input_data.source_article_id, input_data.compare_article_id],
            method="stub_cross_source_contradiction_check",
            model_version=f"{self.name}:{self.version}",
            confidence=0.85,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        # Ring 2 (adversary) vs Ring 1 (India) divergence stub
        is_adversarial_pair = (input_data.source_ring == 2 and input_data.compare_ring == 1) or (
            input_data.source_ring == 1 and input_data.compare_ring == 2
        )

        relation = "CONTRADICTS" if is_adversarial_pair else "CORROBORATED_BY"
        explanation = (
            "Divergent casualty claims between adversary media and Indian official release."
            if is_adversarial_pair
            else "Mutual confirmation of patrol schedule and location coordinates."
        )

        link = CorroborationLinkOut(
            source_article_id=input_data.source_article_id,
            compare_article_id=input_data.compare_article_id,
            relation=relation,
            confidence=0.88,
            explanation=explanation,
            provenance=prov,
        )

        return CorroborationOut(
            links=[link],
            disinformation_indicator=0.65 if relation == "CONTRADICTS" else 0.1,
            provenance=prov,
        )
