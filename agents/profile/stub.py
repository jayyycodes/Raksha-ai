"""
Profile Summary Agent Stub.
Owner: Jaish
Stage: 1 (Contract Stub)

Generates source-attributed profile summaries with claim_status.
Applies the sensitive-attribute filter (never infer or store religion, caste, ethnicity, health).
"""
import re
from typing import List
from common.schemas.intelligence import ProfileFactOut, ProfileSummaryIn, ProfileSummaryOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent

# Hard safety filter: sensitive attributes that must NEVER be persisted or inferred
SENSITIVE_ATTRIBUTE_PATTERNS = [
    r"\breligion\b", r"\bcaste\b", r"\bethnicity\b", r"\bfaith\b",
    r"\bsect\b", r"\bmedical condition\b", r"\bhealth status\b",
]


class ProfileAgentStub(BaseAgent[ProfileSummaryIn, ProfileSummaryOut]):
    name = "profile_agent_stub"
    version = "0.1.0-stub"

    def _sanitize_facts(self, raw_facts: List[ProfileFactOut]) -> List[ProfileFactOut]:
        """Filters out any facts containing sensitive protected attributes."""
        sanitized = []
        for fact in raw_facts:
            is_sensitive = False
            for pattern in SENSITIVE_ATTRIBUTE_PATTERNS:
                if re.search(pattern, fact.fact, re.IGNORECASE):
                    is_sensitive = True
                    break
            if not is_sensitive:
                sanitized.append(fact)
        return sanitized

    def run(self, input_data: ProfileSummaryIn) -> ProfileSummaryOut:
        prov = Provenance(
            source_ids=[art.get("id", 1) for art in input_data.associated_articles],
            method="stub_profile_summarizer",
            model_version=f"{self.name}:{self.version}",
            confidence=0.88,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        sample_facts = [
            ProfileFactOut(
                fact=f"{input_data.entity_name} identified as a key actor in defence procurement briefings.",
                claim_status=ClaimStatus.OFFICIAL_DESIGNATION,
                source_ids=[101],
            ),
            ProfileFactOut(
                fact="Mentioned in regional media regarding border infrastructure review meetings.",
                claim_status=ClaimStatus.REPORTED,
                source_ids=[102],
            ),
        ]

        clean_facts = self._sanitize_facts(sample_facts)

        return ProfileSummaryOut(
            entity_id=input_data.entity_id,
            entity_name=input_data.entity_name,
            entity_type=input_data.entity_type,
            summary=(
                f"Profile summary for {input_data.entity_name} ({input_data.entity_type}). "
                "Documented in publicly available defence reporting across multiple monitoring rings."
            ),
            facts=clean_facts,
            claim_status=ClaimStatus.REPORTED,
            associated_entities=["Ministry of Defence", "Northern Command"],
            provenance=prov,
        )
