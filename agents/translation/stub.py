"""
Translation Agent Stub.
Owner: Ary (Contract Stub by Jaish)
Stage: 1 (Contract Stub)
"""
from common.schemas.articles import ArticleIn
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from agents.base import BaseAgent


class TranslationAgentStub(BaseAgent[ArticleIn, dict]):
    name = "translation_agent_stub"
    version = "0.1.0-stub"

    def run(self, input_data: ArticleIn) -> dict:
        is_translated = input_data.language not in ("en", "eng")
        translated_text = (
            f"[Translated from {input_data.language}]: {input_data.content or input_data.title}"
            if is_translated
            else input_data.content
        )
        return {
            "article_id": input_data.id,
            "original_language": input_data.language,
            "is_translated": is_translated,
            "translated_title": f"[En] {input_data.title}" if is_translated else input_data.title,
            "translated_text": translated_text,
            "provenance": Provenance(
                source_ids=[input_data.id] if input_data.id else [],
                method="stub_translation",
                model_version=f"{self.name}:{self.version}",
                confidence=1.0,
                claim_status=ClaimStatus.REPORTED,
                source_type=SourceType.PUBLIC,
            ),
        }
