# translation agent stub
from typing import List, Dict
from agents.base import Agent

class TranslationAgent:
    name = "translation"
    version = "0.1"

    def run(self, batch: List[Dict]) -> List[Dict]:
        # For each article, just echo the original text as "translated_text"
        results = []
        for article in batch:
            results.append({
                "article_id": article["id"],
                "translated_text": article.get("content", "") or "[no content]",
                "method": "stub",
                "model_version": "none"
            })
        return results

