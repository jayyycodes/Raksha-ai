# resolution agent stub (placeholder for Mid stage)
from typing import List, Dict
from agents.base import Agent

class ResolutionAgent:
    name = "resolution"
    version = "0.1"

    def run(self, batch: List[Dict]) -> List[Dict]:
        # No actual resolution in MVP – just return empty list or pass‑through
        return []

