"""
Entity Resolution Agent Stub.
Owner: Ary (Contract Stub by Jaish)
Stage: 1 (Contract Stub)
"""
from typing import Dict, List
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class ResolutionAgentStub(BaseAgent[List[str], Dict[str, any]]):
    name = "resolution_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: List[str]) -> Dict[str, any]:
        # Simple alias normalization stub
        alias_map = {
            "iaf": "Indian Air Force",
            "pla": "People's Liberation Army",
            "drdo": "Defence Research and Development Organisation",
        }
        resolved = []
        for name in input_data:
            canonical = alias_map.get(name.lower().strip(), name.strip())
            resolved.append({
                "raw_name": name,
                "canonical_name": canonical,
                "confidence": 0.95 if name.lower() in alias_map else 0.65,
                "action": "auto_link" if name.lower() in alias_map else "review_queue",
            })

        return {
            "resolved_entities": resolved,
            "provenance": Provenance(
                source_ids=[],
                method="stub_alias_lookup",
                model_version=f"{self.name}:{self.version}",
                confidence=0.85,
                claim_status=ClaimStatus.OFFICIAL_DESIGNATION,
                source_type=SourceType.PUBLIC,
            ),
        }
