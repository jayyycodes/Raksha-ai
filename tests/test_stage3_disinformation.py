"""
Unit Tests for Disinformation Scoring Agent v1 (Stage 3 Solid - Milestone M9).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
from agents.corroboration.disinformation import DisinformationScorer
from common.constants import RING_INDIA, RING_ADVERSARY, RING_GLOBAL


def test_disinformation_score_unanimous_corroboration():
    """Unanimous cross-ring reporting yields low disinformation risk."""
    scorer = DisinformationScorer()
    articles = [
        {
            "id": 1,
            "source_name": "The Hindu",
            "ring": RING_INDIA,
            "title": "Border security talks conclude in Chushul sector",
            "content": "Corps Commander level meeting agreed to maintain communication along LAC.",
        },
        {
            "id": 2,
            "source_name": "Reuters",
            "ring": RING_GLOBAL,
            "title": "India and China military commanders hold frontier dialogue",
            "content": "Meeting in Chushul sector concluded with both sides agreeing to maintain peace along the Line of Actual Control.",
        },
        {
            "id": 3,
            "source_name": "Global Times",
            "ring": RING_ADVERSARY,
            "title": "China-India hold commander level talks in western sector",
            "content": "Both militaries held commander talks and agreed to maintain stability on the ground.",
        },
    ]

    result = scorer.evaluate_cluster(articles)
    assert result.score <= 0.35
    assert result.risk_level in ("LOW", "MEDIUM")
    assert result.metrics.total_comparisons == 3
    assert result.metrics.corroboration_count >= 1


def test_disinformation_score_adversary_contradiction_surge():
    """Heavy denial vs assertion between Ring 2 and Ring 1 flags high disinformation risk."""
    scorer = DisinformationScorer()
    articles = [
        {
            "id": 1,
            "source_name": "Dawn Pakistan",
            "ring": RING_ADVERSARY,
            "title": "Military denies incursion claims along frontier",
            "content": "ISPR refutes allegations of cross-border infiltration, claiming zero casualties and unfounded claims by neighbouring forces.",
        },
        {
            "id": 2,
            "source_name": "Geo News",
            "ring": RING_ADVERSARY,
            "title": "Frontier situation calm as military rejects false reports",
            "content": "Spokesperson dismisses border incident claims as fabricated propaganda.",
        },
        {
            "id": 3,
            "source_name": "ANI News",
            "ring": RING_INDIA,
            "title": "Security forces neutralize infiltrating terrorists along LoC",
            "content": "Heavy exchange of fire after incursion attempt; two terrorists neutralized with recovered weapons.",
        },
        {
            "id": 4,
            "source_name": "The Hindu",
            "ring": RING_INDIA,
            "title": "Infiltration bid foiled in Rajouri sector, casualties reported",
            "content": "Army repels infiltration attempt along the Line of Control, recovering assault rifles and ammunition.",
        },
    ]

    result = scorer.evaluate_cluster(articles)
    assert result.score >= 0.50
    assert result.risk_level in ("HIGH", "CRITICAL")
    assert result.metrics.contradiction_count > 0
    assert len(result.flagged_contradictions) > 0
