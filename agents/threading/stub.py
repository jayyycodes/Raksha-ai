"""
Event Threading Agent Stub.
Owner: Ary (Contract Stub by Jaish)
Stage: 1 (Contract Stub)
"""
from common.schemas.events import EventLinkOut, EventThreadingIn, EventThreadingOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class ThreadingAgentStub(BaseAgent[EventThreadingIn, EventThreadingOut]):
    name = "threading_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: EventThreadingIn) -> EventThreadingOut:
        prov = Provenance(
            source_ids=[input_data.article_id],
            method="stub_cosine_and_entity_overlap",
            model_version=f"{self.name}:{self.version}",
            confidence=0.82,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        candidate_links = [
            EventLinkOut(
                event_id=1,
                article_id=input_data.article_id,
                link_method="shared_entities",
                confidence=0.85,
                is_seed=False,
                explanation=f"Overlapping entities: {', '.join(input_data.entities[:2]) if input_data.entities else 'LAC border'}",
                provenance=prov,
            )
        ]

        return EventThreadingOut(
            article_id=input_data.article_id,
            matched_event_id=1,
            candidate_links=candidate_links,
            created_new_event=False,
            new_event_title=None,
            provenance=prov,
        )
