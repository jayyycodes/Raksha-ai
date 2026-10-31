# scoring agent stub
from typing import List, Dict
from agents.base import Agent

class ScoringAgent:
    name = "scoring"
    version = "0.1"

    def run(self, batch: List[Dict]) -> List[Dict]:
        # Very simple scoring: use threat_level from extraction if present, else default 1
        results = []
        for article in batch:
            threat = article.get("threat_level", 1)
            results.append({
                "article_id": article["id"],
                "region": "unknown",
                "score": threat,
                "trend": "stable",
                "method": "stub",
                "model_version": "none"
            })
        return results

