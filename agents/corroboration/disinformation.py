"""
Disinformation Scoring Agent v1 (Stage 3 Solid - Milestone M9).
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Calculates narrative divergence and disinformation risk by evaluating cross-source
contradictions and corroborations across Rings 1 to 4:
- Cross-ring contradiction ratios (Ring 1 India vs Ring 2 Adversary vs Ring 4 Neutral Global).
- Uncorroborated adversary narrative surges.
- Source diversity and claim verification indices.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

from common.constants import (
    RING_INDIA,
    RING_ADVERSARY,
    RING_REGIONAL,
    RING_GLOBAL,
)
from agents.corroboration.corroboration_agent import CorroborationAgent


class DisinformationMetrics(BaseModel):
    """Component metrics for disinformation risk scoring."""
    total_articles: int = 0
    total_comparisons: int = 0
    corroboration_count: int = 0
    contradiction_count: int = 0
    contradiction_ratio: float = 0.0
    adversary_isolation_index: float = 0.0
    neutral_corroboration_rate: float = 0.0


class DisinformationScoreOut(BaseModel):
    """Overall disinformation assessment for an event cluster or article."""
    score: float = Field(..., ge=0.0, le=1.0, description="0.0 (fully corroborated) to 1.0 (high disinformation probability)")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    primary_divergence_reason: str
    metrics: DisinformationMetrics
    ring_breakdown: dict[str, int]
    flagged_contradictions: list[dict[str, Any]] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DisinformationScorer:
    """
    Evaluates multi-source news clusters for disinformation and narrative warfare.
    """

    def __init__(self):
        self.corroboration_agent = CorroborationAgent()

    def evaluate_cluster(self, articles: list[dict[str, Any]]) -> DisinformationScoreOut:
        """
        Evaluate a cluster of related articles reporting on the same event or topic.
        """
        if not articles or len(articles) < 2:
            return DisinformationScoreOut(
                score=0.1,
                risk_level="LOW",
                primary_divergence_reason="Insufficient multi-source volume for cross-verification",
                metrics=DisinformationMetrics(total_articles=len(articles)),
                ring_breakdown={f"ring_{r}": 0 for r in (1, 2, 3, 4)},
            )

        ring_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for a in articles:
            r = a.get("ring", 1)
            ring_counts[r] = ring_counts.get(r, 0) + 1

        corroborations = 0
        contradictions = 0
        total_pairs = 0
        flagged_contradictions = []

        adversary_articles = [a for a in articles if a.get("ring") == RING_ADVERSARY]
        india_articles = [a for a in articles if a.get("ring") == RING_INDIA]
        global_articles = [a for a in articles if a.get("ring") == RING_GLOBAL]

        # Cross-evaluate all pairs
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                a1 = articles[i]
                a2 = articles[j]
                total_pairs += 1

                link = self.corroboration_agent.analyze_pair(
                    source_article_id=a1.get("id", i),
                    source_text=f"{a1.get('title', '')} {a1.get('content', '')}",
                    source_ring=a1.get("ring", 1),
                    compare_article_id=a2.get("id", j),
                    compare_text=f"{a2.get('title', '')} {a2.get('content', '')}",
                    compare_ring=a2.get("ring", 1),
                )

                if link.relation == "CORROBORATED_BY":
                    corroborations += 1
                elif link.relation == "CONTRADICTS":
                    contradictions += 1
                    flagged_contradictions.append({
                        "source_1": a1.get("source_name", "Unknown"),
                        "source_2": a2.get("source_name", "Unknown"),
                        "ring_1": a1.get("ring", 1),
                        "ring_2": a2.get("ring", 1),
                        "reason": link.explanation,
                    })

        contradiction_ratio = round(contradictions / max(1, total_pairs), 4)

        # Check adversary isolation (Ring 2 making claims unsupported by Rings 1 & 4)
        adversary_isolated = 0
        for adv in adversary_articles:
            adv_text = f"{adv.get('title', '')} {adv.get('content', '')}"
            supported = False
            for glob in (india_articles + global_articles):
                glob_text = f"{glob.get('title', '')} {glob.get('content', '')}"
                res = self.corroboration_agent.analyze_pair(
                    source_article_id=adv.get("id", 0),
                    source_text=adv_text,
                    source_ring=RING_ADVERSARY,
                    compare_article_id=glob.get("id", 1),
                    compare_text=glob_text,
                    compare_ring=glob.get("ring", 1),
                )
                if res.relation == "CORROBORATED_BY":
                    supported = True
                    break
            if not supported:
                adversary_isolated += 1

        adversary_isolation_rate = round(adversary_isolated / max(1, len(adversary_articles)), 4) if adversary_articles else 0.0

        # Global corroboration rate: share of Indian or Adversary claims validated by global outlets
        global_validations = 0
        for g in global_articles:
            g_text = f"{g.get('title', '')} {g.get('content', '')}"
            for ind in india_articles:
                ind_text = f"{ind.get('title', '')} {ind.get('content', '')}"
                res = self.corroboration_agent.analyze_pair(
                    source_article_id=g.get("id", 0),
                    source_text=g_text,
                    source_ring=RING_GLOBAL,
                    compare_article_id=ind.get("id", 1),
                    compare_text=ind_text,
                    compare_ring=RING_INDIA,
                )
                if res.relation == "CORROBORATED_BY":
                    global_validations += 1
                    break
        neutral_corroboration_rate = round(global_validations / max(1, len(global_articles)), 4) if global_articles else 0.5

        # Weighted formula for Disinformation Score [0.0, 1.0]:
        # High score means high risk of disinformation / information warfare.
        raw_score = (
            (contradiction_ratio * 0.45) +
            (adversary_isolation_rate * 0.40) +
            ((1.0 - neutral_corroboration_rate) * 0.15)
        )
        final_score = round(min(1.0, max(0.0, raw_score)), 3)

        if final_score >= 0.75:
            risk_level = "CRITICAL"
            reason = "High volume of sharp factual denials with uncorroborated adversary framing."
        elif final_score >= 0.50:
            risk_level = "HIGH"
            reason = "Elevated cross-ring narrative friction; claims disputed by counter-parties."
        elif final_score >= 0.30:
            risk_level = "MEDIUM"
            reason = "Moderate discrepancies in casualty/damage framing with partial corroboration."
        else:
            risk_level = "LOW"
            reason = "Consistent facts corroborated across domestic, regional and global reporting."

        return DisinformationScoreOut(
            score=final_score,
            risk_level=risk_level,
            primary_divergence_reason=reason,
            metrics=DisinformationMetrics(
                total_articles=len(articles),
                total_comparisons=total_pairs,
                corroboration_count=corroborations,
                contradiction_count=contradictions,
                contradiction_ratio=contradiction_ratio,
                adversary_isolation_index=adversary_isolation_rate,
                neutral_corroboration_rate=neutral_corroboration_rate,
            ),
            ring_breakdown={
                "ring_1_india": ring_counts[1],
                "ring_2_adversary": ring_counts[2],
                "ring_3_regional": ring_counts[3],
                "ring_4_global": ring_counts[4],
            },
            flagged_contradictions=flagged_contradictions[:10],
        )
