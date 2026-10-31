"""
Report Agent Stub (Grounded Daily SitRep).
Owner: Jaish
Stage: 1 (Contract Stub)

Produces structured daily intelligence report where every assertion
cites exact article IDs and unsupported sentences are flagged.
"""
from common.schemas.intelligence import SitRepIn, SitRepOut, SitRepSentence
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class ReportAgentStub(BaseAgent[SitRepIn, SitRepOut]):
    name = "report_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: SitRepIn) -> SitRepOut:
        article_ids = input_data.article_ids or [101, 102, 103]

        sentences = [
            SitRepSentence(
                text="Heightened air patrols were observed across western border sectors during the past 24 hours.",
                citations=[article_ids[0]],
                is_supported=True,
            ),
            SitRepSentence(
                text="Diplomatic delegations met in New Delhi to review boundary mechanism protocols.",
                citations=[article_ids[1]] if len(article_ids) > 1 else [article_ids[0]],
                is_supported=True,
            ),
            SitRepSentence(
                text="Unverified social media channels reported artillery deployment near northern passes.",
                citations=[article_ids[2]] if len(article_ids) > 2 else [article_ids[0]],
                is_supported=True,
            ),
        ]

        top_threats = [
            {"region": "LAC-Ladakh", "score": 6.8, "trend": "rising", "lead_event": "Aerial Reconnaissance"},
            {"region": "LoC-Kashmir", "score": 5.4, "trend": "stable", "lead_event": "Infiltration Alert"},
        ]

        prov = Provenance(
            source_ids=article_ids,
            method="stub_grounded_sitrep_groq_llama3",
            model_version=f"{self.name}:{self.version}",
            confidence=0.92,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return SitRepOut(
            report_date=input_data.report_date,
            title=f"Raksha AI Daily SitRep ΓÇö {input_data.report_date.isoformat()}",
            executive_summary=(
                "Summary of regional defence developments over the last 24 hours. "
                "Air patrol activity reported along western border sectors; bilateral boundary protocol talks convened."
            ),
            sentences=sentences,
            top_threats=top_threats,
            article_count=len(article_ids),
            grounding_rate=1.0,
            provenance=prov,
        )
