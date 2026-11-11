"""
Translation Agent for Raksha AI.
Floor 2 — Language & Knowledge Agents
Owner: Ary
Stage: 2 Production Implementation

Bridges engine.translator into the BaseAgent protocol,
handling single and batch translation with full provenance tracking.
"""
from typing import Any, Dict, List, Optional, Union

from agents.base import BaseAgent
from common.logger import get_logger
from common.schemas.articles import ArticleIn
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from engine.translator import translate

logger = get_logger(__name__)

ENGLISH_CODES = {"en", "eng", "english"}


class TranslationAgent(BaseAgent[Union[ArticleIn, Dict[str, Any]], Dict[str, Any]]):
    """
    Translates non-English articles into English using the Helsinki-NLP
    translation engine, emitting structured output and audit provenance.
    """
    name: str = "translation_agent"
    version: str = "0.2.0"

    def run(self, input_data: Union[ArticleIn, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute translation inference on a single article.
        Accepts either an ArticleIn instance or a dictionary.
        """
        if isinstance(input_data, ArticleIn):
            article_id = input_data.id
            title = input_data.title or ""
            content = input_data.content or ""
            language = (input_data.language or "en").strip().lower()
        elif isinstance(input_data, dict):
            article_id = input_data.get("id") or input_data.get("article_id")
            title = input_data.get("title") or ""
            content = input_data.get("content") or ""
            language = (input_data.get("language") or "en").strip().lower()
        else:
            raise TypeError(f"Unsupported input type for TranslationAgent: {type(input_data).__name__}")

        source_ids = [article_id] if article_id is not None else []

        # Check if already in English or empty
        if not language or language in ENGLISH_CODES:
            prov = Provenance(
                source_ids=source_ids,
                method="passthrough_english",
                model_version=f"{self.name}:{self.version}",
                confidence=1.0,
                claim_status=ClaimStatus.REPORTED,
                source_type=SourceType.PUBLIC,
            )
            return {
                "article_id": article_id,
                "original_language": language or "en",
                "is_translated": False,
                "translated_title": title,
                "translated_text": content or title,
                "provenance": prov,
            }

        # Perform translation on title and content
        translated_title = title
        translated_text = content
        is_translated = False
        method = "helsinki_opus_mt"
        confidence = 0.90

        try:
            # Translate content if present, otherwise title
            if content.strip():
                content_res = translate(content, source_lang=language, target_lang="en")
                if content_res.is_success:
                    translated_text = str(content_res)
                    is_translated = True
                else:
                    logger.warning(
                        "Content translation degraded for article %s: %s",
                        article_id,
                        content_res.error,
                    )
                    translated_text = content
                    confidence = 0.40
                    method = "helsinki_opus_mt_degraded"

            # Translate headline/title if present
            if title.strip():
                title_res = translate(title, source_lang=language, target_lang="en")
                if title_res.is_success:
                    translated_title = str(title_res)
                    is_translated = True
                else:
                    translated_title = title

        except Exception as exc:
            logger.error("Unexpected error in TranslationAgent for article %s: %s", article_id, exc)
            is_translated = False
            translated_title = title
            translated_text = content or title
            confidence = 0.20
            method = "translation_failure_fallback"

        prov = Provenance(
            source_ids=source_ids,
            method=method,
            model_version=f"{self.name}:{self.version}",
            confidence=confidence,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return {
            "article_id": article_id,
            "original_language": language,
            "is_translated": is_translated,
            "translated_title": translated_title,
            "translated_text": translated_text,
            "provenance": prov,
        }
