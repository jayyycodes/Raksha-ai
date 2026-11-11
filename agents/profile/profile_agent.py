"""
Profile Summary Agent & Sensitive-Attribute Filter.
Owner: Jaish
Stage: 2 (Mid)

Builds attributed profiles for key defence entities (Person, Organisation, Location, Equipment).
Enforces:
1. Candidate-to-Profile Promotion Rule: Requires >= 3 mentions from >= 2 unique sources.
2. Strict Sensitive-Attribute Filter: Never infer, store, or output religion, caste, ethnicity,
   or health status for any individual.
3. Provenance & Claim Status on every fact: 'reported', 'official_designation', 'analyst_verified'.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from common.logger import get_logger
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import ProfileFactOut, ProfileSummaryIn, ProfileSummaryOut
from agents.base import BaseAgent

logger = get_logger(__name__)

# Strict prohibited sensitive attribute regexes (India DPDP Act & responsible defence OSINT)
SENSITIVE_PATTERNS = [
    re.compile(r"\b(?:hindu|muslim|sikh|christian|jain|buddhist|parsi|jewish|islamic|religion|religious)\b", re.IGNORECASE),
    re.compile(r"\b(?:caste|dalit|brahmin|kshatriya|vaishya|shudra|sc/st|obc|subcaste|gotra)\b", re.IGNORECASE),
    re.compile(r"\b(?:ethnicity|ethnic|tribal lineage|sectarian|sect)\b", re.IGNORECASE),
    re.compile(r"\b(?:medical condition|cancer|ailment|mental health|diagnosed with|hospitalized for illness|health status)\b", re.IGNORECASE),
]

OFFICIAL_SOURCES = {
    "pib", "pib india", "drdo", "indian army", "indian air force", "indian navy",
    "ministry of defence", "mod", "mea", "pmio", "official spokesperson",
}


def is_eligible_for_profile(
    mention_count: int,
    source_count: int,
    analyst_promoted: bool = False,
) -> bool:
    """
    Enforces the Candidate-to-Profile Rule:
    An entity node qualifies as a full profile page only after:
    - >= 3 article mentions AND
    - >= 2 unique sources, OR
    - Explicit promotion by an authorized analyst.
    """
    if analyst_promoted:
        return True
    return mention_count >= 3 and source_count >= 2


def contains_sensitive_attribute(text: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if a text segment contains prohibited personal attributes.
    Returns (True, pattern_match) if sensitive, else (False, None).
    """
    for pat in SENSITIVE_PATTERNS:
        match = pat.search(text)
        if match:
            return True, match.group(0)
    return False, None


class ProfileSummaryAgent(BaseAgent[ProfileSummaryIn, ProfileSummaryOut]):
    name = "profile_summary_agent"
    version = "0.2.0"

    def filter_facts(self, raw_facts: List[ProfileFactOut]) -> List[ProfileFactOut]:
        """
        Applies the sensitive-attribute filter, removing any claim that violates privacy or safety boundaries.
        """
        clean_facts: List[ProfileFactOut] = []
        for fact in raw_facts:
            is_sensitive, term = contains_sensitive_attribute(fact.fact)
            if is_sensitive:
                logger.warning(
                    f"Sensitive-attribute filter blocked fact mentioning prohibited attribute '{term}': {fact.fact[:50]}..."
                )
                continue
            clean_facts.append(fact)
        return clean_facts

    def compile_profile_facts(
        self,
        entity_name: str,
        entity_type: str,
        articles: List[Dict[str, Any]],
    ) -> List[ProfileFactOut]:
        """
        Extracts factual statements from articles mentioning the entity and tags each with claim_status.
        """
        facts: List[ProfileFactOut] = []

        for art in articles:
            art_id = art.get("id", 0)
            title = art.get("title", "").strip()
            source_name = str(art.get("source_name", "Public News")).lower()
            event_type = art.get("event_type", "general")

            # Determine claim status based on source provenance
            if any(offic in source_name for offic in OFFICIAL_SOURCES):
                status = ClaimStatus.OFFICIAL_DESIGNATION
                conf = 0.95
            elif art.get("is_verified_by_analyst", False):
                status = ClaimStatus.ANALYST_VERIFIED
                conf = 1.0
            else:
                status = ClaimStatus.REPORTED
                conf = 0.85

            fact_text = f"Documented in connection with {event_type.replace('_', ' ')} reporting: '{title}'"

            facts.append(
                ProfileFactOut(
                    fact=fact_text,
                    claim_status=status,
                    source_ids=[art_id] if art_id else [],
                )
            )

        return self.filter_facts(facts)

    def generate_summary(
        self,
        entity_id: int,
        entity_name: str,
        entity_type: str,
        articles: List[Dict[str, Any]],
        analyst_promoted: bool = False,
    ) -> ProfileSummaryOut:
        """
        Builds a complete, attributed profile summary with vetted facts and associated entities.
        """
        source_names: Set[str] = {a.get("source_name", "Unknown") for a in articles}
        mention_count = len(articles)
        source_count = len(source_names)
        eligible = is_eligible_for_profile(mention_count, source_count, analyst_promoted)

        # Extract and sanitize facts
        clean_facts = self.compile_profile_facts(entity_name, entity_type, articles)

        # Gather co-occurring entities
        associated: Set[str] = set()
        for a in articles:
            for ent in a.get("entities", []):
                ent_val = ent if isinstance(ent, str) else ent.get("entity_value", "")
                if ent_val and ent_val.lower() != entity_name.lower():
                    associated.add(ent_val)

        # Generate summary prose
        status_note = "Full Profile (Verified multi-source)" if eligible else "Candidate Profile (Under threshold)"
        summary_prose = (
            f"{status_note} for {entity_name} [{entity_type.upper()}]. "
            f"Observed in {mention_count} reported events across {source_count} unique public sources. "
            f"Primary operational contexts include {', '.join(list({a.get('event_type', 'security') for a in articles})[:3])}."
        )

        # Ensure summary prose itself contains no sensitive attributes
        is_sensitive, term = contains_sensitive_attribute(summary_prose)
        if is_sensitive:
            summary_prose = f"Profile overview for {entity_name} [{entity_type.upper()}]. Attributed intelligence record."

        prov = Provenance(
            source_ids=[a.get("id") for a in articles if a.get("id")],
            method="attributed_profile_compiler_v2",
            model_version=f"{self.name}:{self.version}",
            confidence=0.92 if eligible else 0.75,
            claim_status=ClaimStatus.OFFICIAL_DESIGNATION if any(f.claim_status == ClaimStatus.OFFICIAL_DESIGNATION for f in clean_facts) else ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return ProfileSummaryOut(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            summary=summary_prose,
            facts=clean_facts,
            claim_status=prov.claim_status or ClaimStatus.REPORTED,
            associated_entities=list(associated)[:8],
            provenance=prov,
        )

    def run(self, input_data: ProfileSummaryIn) -> ProfileSummaryOut:
        return self.generate_summary(
            entity_id=input_data.entity_id,
            entity_name=input_data.entity_name,
            entity_type=input_data.entity_type,
            articles=input_data.associated_articles,
        )

