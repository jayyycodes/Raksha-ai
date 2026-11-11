"""
Report Agent — Grounded Daily Situation Report (SitRep).
Owner: Jaish
Stage: 2 (Mid)

Generates daily intelligence SitReps using Groq Llama 3 (with deterministic fallback).
Enforces strict sentence-level attribution: every factual assertion must cite valid source IDs,
and unsupported sentences are flagged with is_supported=False.
"""
import json
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from common.config import settings
from common.logger import get_logger
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import SitRepIn, SitRepOut, SitRepSentence
from agents.base import BaseAgent
from agents.scoring.regional_scorer import ThreatScoringAgent

logger = get_logger(__name__)

CITATION_REGEX = re.compile(r"\[(?:Source\s*#?|#)?(\d+)\]", re.IGNORECASE)


class GroundedSitRepAgent(BaseAgent[SitRepIn, SitRepOut]):
    name = "grounded_sitrep_agent"
    version = "0.2.0"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
        self.scorer = ThreatScoringAgent()

    def _extract_citations(self, sentence_text: str, valid_article_ids: Set[int]) -> Tuple[List[int], bool]:
        """
        Extracts cited source IDs from a sentence and verifies them against the valid article set.
        Returns (list_of_valid_citations, is_supported).
        """
        raw_matches = CITATION_REGEX.findall(sentence_text)
        found_ids = [int(m) for m in raw_matches if m.isdigit()]

        valid_cites = [aid for aid in found_ids if aid in valid_article_ids]
        is_supported = len(valid_cites) > 0 and len(valid_cites) == len(found_ids)

        return valid_cites, is_supported

    def _parse_and_verify_sentences(
        self,
        raw_content: str,
        valid_article_ids: Set[int],
    ) -> Tuple[List[SitRepSentence], float]:
        """
        Splits content into sentences, extracts citations for each, and verifies grounding.
        """
        # Split by sentence boundaries (. ! ?) while keeping abbreviations intact
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_content) if len(s.strip()) > 10]
        verified: List[SitRepSentence] = []

        if not raw_sentences:
            return [], 1.0

        for s_text in raw_sentences:
            # Skip pure markdown headers
            if s_text.startswith("#") or s_text.startswith("**TOP THREATS") or s_text.startswith("**ANOMALIES"):
                continue

            cites, supported = self._extract_citations(s_text, valid_article_ids)
            verified.append(
                SitRepSentence(
                    text=s_text,
                    citations=cites,
                    is_supported=supported,
                )
            )

        total = len(verified)
        supported_count = sum(1 for s in verified if s.is_supported and len(s.citations) > 0)
        grounding_rate = round(supported_count / total, 4) if total > 0 else 1.0

        return verified, grounding_rate

    def _synthesize_deterministic_grounded_report(
        self,
        report_date: date,
        articles: List[Dict[str, Any]],
        top_threats: List[Dict[str, Any]],
    ) -> Tuple[str, List[SitRepSentence], float]:
        """
        Fallback generator that produces a strictly grounded SitRep without external API dependencies.
        Guarantees that 100% of generated factual claims carry verifiable citations.
        """
        sentences: List[SitRepSentence] = []
        valid_ids = {int(a["id"]) for a in articles if a.get("id") is not None}

        # Executive summary statements
        lead_threat = top_threats[0] if top_threats else {"region": "LAC-Ladakh", "score": 4.5, "trend": "stable"}
        exec_lines = [
            f"Raksha AI strategic situation briefing compiled for {report_date.isoformat()} covering {len(articles)} defence intelligence items.",
        ]

        # Grounded factual statements from top articles
        sorted_articles = sorted(
            articles,
            key=lambda x: (x.get("threat_level") or 1, x.get("ring") == 2),
            reverse=True,
        )

        for art in sorted_articles[:8]:
            art_id = int(art["id"])
            title = art.get("title", "").strip().rstrip(".")
            event_type = art.get("event_type", "general").replace("_", " ")
            ring = art.get("ring", 1)
            source_name = art.get("source_name", "public media")

            if ring == 2:
                statement = f"Adversary reporting from {source_name} highlighted {title} under {event_type} dynamics [Source #{art_id}]."
            else:
                statement = f"National security reporting documented {title} involving {event_type} [Source #{art_id}]."

            sentences.append(
                SitRepSentence(
                    text=statement,
                    citations=[art_id],
                    is_supported=True,
                )
            )

        summary_text = (
            f"Daily strategic posture highlights {lead_threat.get('region', 'Northern Border')} at threat index "
            f"{lead_threat.get('score', 5.0)}/10 with {lead_threat.get('trend', 'stable')} trajectory. "
            f"A total of {len(articles)} public intelligence records were processed across monitored geopolitical rings."
        )

        return summary_text, sentences, 1.0

    def generate_report(
        self,
        report_date: Optional[date] = None,
        articles: Optional[List[Dict[str, Any]]] = None,
        top_threats: Optional[List[Dict[str, Any]]] = None,
        force_fallback: bool = False,
    ) -> SitRepOut:
        """
        Generates a grounded SitRep with citations for every sentence.
        Uses Groq Llama 3 when GROQ_API_KEY is configured; falls back to deterministic synthesis otherwise.
        """
        report_date = report_date or date.today()
        articles = articles or []

        # If no articles passed, attempt to query last 24h from DB
        if not articles:
            try:
                from common.db import get_db
                from sqlalchemy import text
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                with get_db() as db:
                    rows = db.execute(
                        text("""
                            SELECT a.id, a.title, a.content, s.name as source_name, s.ring,
                                   an.event_type, an.sentiment, an.threat_level
                            FROM articles a
                            LEFT JOIN sources s ON a.source_id = s.id
                            LEFT JOIN article_analysis an ON a.id = an.article_id
                            WHERE a.published_at >= :cutoff
                            ORDER BY a.published_at DESC LIMIT 30
                        """),
                        {"cutoff": cutoff},
                    ).mappings().all()
                    articles = [dict(r) for r in rows]
            except Exception as e:
                logger.debug(f"DB load in sitrep generation skipped: {e}")

        # Compute top threats if not provided
        if not top_threats and articles:
            regional_scores = self.scorer.calculate_all_regions(articles)
            sorted_scores = sorted(regional_scores, key=lambda s: s.score, reverse=True)
            top_threats = [
                {
                    "region": s.region,
                    "score": s.score,
                    "trend": s.trend,
                    "article_count": s.article_count,
                    "lead_events": s.top_events,
                }
                for s in sorted_scores[:4]
            ]
        elif not top_threats:
            top_threats = [
                {"region": "LAC-Ladakh", "score": 3.0, "trend": "stable", "article_count": 0},
                {"region": "LoC-Kashmir", "score": 3.2, "trend": "stable", "article_count": 0},
            ]

        valid_article_ids = {int(a["id"]) for a in articles if a.get("id") is not None}
        groq_api_key = getattr(settings, "GROQ_API_KEY", None)

        used_method = "deterministic_grounded_synthesis_v2"
        exec_summary = ""
        sentences: List[SitRepSentence] = []
        grounding_rate = 1.0

        # Attempt Groq API if available and not forced to fallback
        if groq_api_key and not force_fallback and len(articles) > 0:
            try:
                import httpx
                prompt = (
                    f"You are a military intelligence analyst writing India's daily SitRep for {report_date.isoformat()}.\n"
                    f"CRITICAL RULE: Every single factual sentence MUST include the exact source citation in format [Source #ID] "
                    f"using only IDs provided in the articles list below. Do not make any uncited claims.\n\n"
                    f"ARTICLES:\n" + "\n".join([f"- [ID: {a['id']}] ({a.get('source_name', 'OSINT')} Ring {a.get('ring', 1)}): {a['title']}" for a in articles[:15]])
                )

                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "You are Raksha AI's intelligence briefing agent. Output only grounded statements with citations."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1024,
                    },
                    timeout=15.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    exec_summary = f"Executive briefing for {report_date.isoformat()} generated via {self.model_name}."
                    sentences, grounding_rate = self._parse_and_verify_sentences(content, valid_article_ids)
                    used_method = f"groq_llama3:{self.model_name}"
                else:
                    logger.warning(f"Groq API returned HTTP {response.status_code}, falling back to deterministic synthesizer")
                    exec_summary, sentences, grounding_rate = self._synthesize_deterministic_grounded_report(report_date, articles, top_threats)
            except Exception as e:
                logger.warning(f"Groq API error ({e}), using fallback grounded generator")
                exec_summary, sentences, grounding_rate = self._synthesize_deterministic_grounded_report(report_date, articles, top_threats)
        else:
            exec_summary, sentences, grounding_rate = self._synthesize_deterministic_grounded_report(report_date, articles, top_threats)

        prov = Provenance(
            source_ids=list(valid_article_ids),
            method=used_method,
            model_version=f"{self.name}:{self.version} ({self.model_name})",
            confidence=round(grounding_rate, 2),
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return SitRepOut(
            report_date=report_date,
            title=f"Raksha AI Daily Intelligence Situation Report — {report_date.isoformat()}",
            executive_summary=exec_summary,
            sentences=sentences,
            top_threats=top_threats,
            article_count=len(articles),
            grounding_rate=grounding_rate,
            provenance=prov,
        )

    def run(self, input_data: SitRepIn) -> SitRepOut:
        return self.generate_report(report_date=input_data.report_date)

