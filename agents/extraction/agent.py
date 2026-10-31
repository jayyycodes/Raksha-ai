# extraction agent stub
from typing import List, Dict
from agents.base import Agent

class ExtractionAgent:
    name = "extraction"
    version = "0.1"

    def run(self, batch: List[Dict]) -> List[Dict]:
        # Simple rule‑based stub: if title contains word "attack" => event_type "military", sentiment "negative"
        results = []
        for article in batch:
            title = article.get("title", "").lower()
            if "attack" in title:
                event_type = "military"
                sentiment = "negative"
                threat = 8
            else:
                event_type = "policy"
                sentiment = "neutral"
                threat = 3
            results.append({
                "article_id": article["id"],
                "event_type": event_type,
                "sentiment": sentiment,
                "threat_level": threat,
                "method": "stub",
                "model_version": "none"
            })
        return results

