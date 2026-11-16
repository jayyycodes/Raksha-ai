"""
ResolutionAgent Feedback Loop and Calibration Safety Tests.
Owner: Ary (Floor 2 - Language & Knowledge Agents)
Stage: 3 (Phase 3: Feedback Evaluation and ResolutionAgent Threshold Calibration)

Validates:
- Workspace-isolated positive & negative feedback loops.
- Cross-workspace isolation guarantees.
- Negative constraint blocking of unsafe alias matches.
- Pending feedback non-interference.
- Newer feedback supersession over older decisions.
- Equal-timestamp conflict fail-closed semantics.
- Reused decision ID provenance validation.
- Entity type compatibility checks.
- Common English word immunity.
- Unattributed feedback isolation.
- Threshold calibration runner reproducibility and safety.
"""
from datetime import datetime, timezone
import pytest

from agents.resolution.agent import ResolutionAgent
from agents.resolution.feedback import FeedbackRecord, ResolutionFeedbackStore
from evaluation.harness import run_resolution_feedback_eval, sweep_resolution_thresholds


class TestResolutionFeedbackLoopSafety:
    """Rigorous verification of the human-in-the-loop feedback mechanisms."""

    def test_positive_feedback_in_correct_workspace_auto_links(self):
        """Positive feedback in workspace 101 auto-links to canonical and marks ANALYST_VERIFIED."""
        store = ResolutionFeedbackStore()
        rec = FeedbackRecord(
            decision_id="dec_fb_01",
            source_mention="Project Garuda",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_alpha",
            reviewed_at=datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_record(rec)

        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Project Garuda", workspace_id=101, entity_type_hint="EQUIPMENT")

        assert res["action"] == "auto_link"
        assert res["canonical_name"] == "BrahMos"
        assert res["match_method"] == "accepted_feedback_alias"
        assert res["claim_status"] == "analyst_verified"
        assert res["analyst_id"] == "analyst_alpha"
        assert res["feedback_decision_id"] == "dec_fb_01"

    def test_positive_feedback_in_other_workspace_does_not_leak(self):
        """Positive feedback in workspace 101 must NOT leak to workspace 102."""
        store = ResolutionFeedbackStore()
        rec = FeedbackRecord(
            decision_id="dec_fb_02",
            source_mention="Project Garuda",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_alpha",
            reviewed_at=datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_record(rec)

        agent = ResolutionAgent(feedback_store=store)
        res_102 = agent.resolve_entity("Project Garuda", workspace_id=102, entity_type_hint="EQUIPMENT")

        assert res_102["action"] == "separate"
        assert res_102["canonical_name"] == "Project Garuda"
        assert res_102.get("match_method") != "accepted_feedback_alias"

    def test_negative_feedback_prevents_unsafe_alias_match(self):
        """Negative feedback rejects an alias match, returning separate and DISPUTED status."""
        store = ResolutionFeedbackStore()
        rec = FeedbackRecord(
            decision_id="dec_fb_03",
            source_mention="Falcon Battery",
            target_canonical="S-400 Triumf",
            decision="rejected",
            analyst_id="analyst_beta",
            reviewed_at=datetime(2026, 11, 11, 10, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_record(rec)

        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Falcon Battery", workspace_id=101, entity_type_hint="EQUIPMENT")

        assert res["action"] == "separate"
        assert res["match_method"] == "negative_feedback_constraint"
        assert res["claim_status"] == "disputed"
        assert res["feedback_decision_id"] == "dec_fb_03"

    def test_pending_feedback_does_not_influence_resolution(self):
        """Items not accepted/rejected in the store have no influence on resolution decisions."""
        store = ResolutionFeedbackStore()
        # No accepted or rejected record added for Project Phoenix
        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Project Phoenix", workspace_id=101, entity_type_hint="EQUIPMENT")

        assert res["action"] == "separate"
        assert res["canonical_name"] == "Project Phoenix"
        assert res.get("feedback_decision_id") is None

    def test_newer_feedback_supersedes_older_feedback(self):
        """Newer rejection decision supersedes older acceptance decision for the same alias."""
        store = ResolutionFeedbackStore()
        older_rec = FeedbackRecord(
            decision_id="dec_fb_04_old",
            source_mention="Project Varuna",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_alpha",
            reviewed_at=datetime(2026, 11, 10, 10, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        newer_rec = FeedbackRecord(
            decision_id="dec_fb_04_new",
            source_mention="Project Varuna",
            target_canonical="BrahMos",
            decision="rejected",
            analyst_id="analyst_beta",
            reviewed_at=datetime(2026, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_records([older_rec, newer_rec])

        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Project Varuna", workspace_id=101, entity_type_hint="EQUIPMENT")

        assert res["action"] == "separate"
        assert res["match_method"] == "negative_feedback_constraint"
        assert res["feedback_decision_id"] == "dec_fb_04_new"

    def test_conflicting_decisions_at_equal_timestamps_fail_closed(self):
        """Two analysts accepting different canonicals at the exact same timestamp must fail closed."""
        store = ResolutionFeedbackStore()
        ts = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)
        rec_a = FeedbackRecord(
            decision_id="dec_fb_conflict_a",
            source_mention="Project Trishul",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_1",
            reviewed_at=ts,
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        rec_b = FeedbackRecord(
            decision_id="dec_fb_conflict_b",
            source_mention="Project Trishul",
            target_canonical="S-400 Triumf",
            decision="accepted",
            analyst_id="analyst_2",
            reviewed_at=ts,
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_records([rec_a, rec_b])

        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Project Trishul", workspace_id=101, entity_type_hint="EQUIPMENT")

        # Must NOT auto-link to either canonical
        assert res["action"] in ("separate", "review_queue")
        assert res["action"] != "auto_link"

    def test_duplicate_decision_ids_validation(self):
        """Reusing a decision ID with different analyst or entity type must raise ValueError."""
        store = ResolutionFeedbackStore()
        ts = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
        rec1 = FeedbackRecord(
            decision_id="dec_unique_101",
            source_mention="Falcon Radar",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_alpha",
            reviewed_at=ts,
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        store.add_record(rec1)

        # Same decision ID but conflicting analyst
        rec2 = FeedbackRecord(
            decision_id="dec_unique_101",
            source_mention="Falcon Radar",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_different",
            reviewed_at=ts,
            entity_type="EQUIPMENT",
            workspace_id=101,
        )
        with pytest.raises(ValueError, match="Conflicting reuse of decision_id"):
            store.add_record(rec2)

    def test_invalid_entity_types_cannot_bypass_safeguards(self):
        """Feedback specifying an incompatible entity type (PERSON for EQUIPMENT) fails closed."""
        store = ResolutionFeedbackStore()
        rec = FeedbackRecord(
            decision_id="dec_fb_type_err",
            source_mention="Project Agni-V",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id="analyst_delta",
            reviewed_at=datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc),
            entity_type="PERSON",  # BrahMos is EQUIPMENT, not PERSON
            workspace_id=101,
        )
        store.add_record(rec)

        agent = ResolutionAgent(feedback_store=store)
        res = agent.resolve_entity("Project Agni-V", workspace_id=101, entity_type_hint="PERSON")

        assert res["action"] == "separate"
        assert res["match_method"] == "entity_type_mismatch_rejected"

    def test_common_english_words_cannot_become_aliases(self):
        """High-frequency common English words are protected against resolution."""
        agent = ResolutionAgent()
        for word in ("west", "strike", "forces", "border", "wing"):
            res = agent.resolve_entity(word, workspace_id=101)
            assert res["action"] == "separate"
            assert res["match_method"] in (
                "common_english_word_guard",
                "ambiguous_common_name_guard",
                "unmatched_separate",
                "unmatched",
            )

    def test_unattributed_feedback_is_workspace_isolated(self):
        """Unattributed feedback record operates strictly within its designated workspace."""
        store = ResolutionFeedbackStore()
        rec = FeedbackRecord(
            decision_id="dec_fb_unatt",
            source_mention="Project Delta",
            target_canonical="BrahMos",
            decision="accepted",
            analyst_id=None,
            reviewed_at=datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            entity_type="EQUIPMENT",
            workspace_id=505,
        )
        store.add_record(rec)

        agent = ResolutionAgent(feedback_store=store)
        res_505 = agent.resolve_entity("Project Delta", workspace_id=505, entity_type_hint="EQUIPMENT")
        res_506 = agent.resolve_entity("Project Delta", workspace_id=506, entity_type_hint="EQUIPMENT")

        assert res_505["action"] == "auto_link"
        assert res_506["action"] == "separate"

    def test_configurable_thresholds_on_resolution_agent(self):
        """ResolutionAgent respects custom auto_link_threshold and review_queue_threshold."""
        agent_conservative = ResolutionAgent(auto_link_threshold=0.95, review_queue_threshold=0.70)
        assert agent_conservative.auto_link_threshold == 0.95
        assert agent_conservative.review_queue_threshold == 0.70

        agent_permissive = ResolutionAgent(auto_link_threshold=0.75, review_queue_threshold=0.50)
        assert agent_permissive.auto_link_threshold == 0.75
        assert agent_permissive.review_queue_threshold == 0.50

    def test_threshold_validation_valid_and_invalid_boundaries(self):
        """Validates constructor requires 0.0 <= review_queue <= auto_link <= 1.0."""
        # Valid boundaries
        a1 = ResolutionAgent(auto_link_threshold=1.0, review_queue_threshold=0.0)
        assert a1.auto_link_threshold == 1.0 and a1.review_queue_threshold == 0.0

        a2 = ResolutionAgent(auto_link_threshold=0.80, review_queue_threshold=0.80)
        assert a2.auto_link_threshold == 0.80 and a2.review_queue_threshold == 0.80

        a3 = ResolutionAgent(auto_link_threshold=0.0, review_queue_threshold=0.0)
        assert a3.auto_link_threshold == 0.0 and a3.review_queue_threshold == 0.0

        # Invalid: review_queue > auto_link
        with pytest.raises(ValueError, match="Invalid resolution thresholds"):
            ResolutionAgent(auto_link_threshold=0.60, review_queue_threshold=0.80)

        # Invalid: auto_link > 1.0
        with pytest.raises(ValueError, match="Invalid resolution thresholds"):
            ResolutionAgent(auto_link_threshold=1.05, review_queue_threshold=0.50)

        # Invalid: review_queue < 0.0
        with pytest.raises(ValueError, match="Invalid resolution thresholds"):
            ResolutionAgent(auto_link_threshold=0.88, review_queue_threshold=-0.10)

    def test_rank_conflict_coverage_exact_and_non_exact_paths(self):
        """Conflicting ranks are detected across exact and non-exact resolution paths."""
        from evaluation.harness import classify_entity_pair

        agent = ResolutionAgent()

        # 1. Exact vs Exact with conflicting ranks
        res_lt_gen = agent.resolve_entity("Lt Gen Upendra Dwivedi")
        res_major = agent.resolve_entity("Major Upendra Dwivedi")
        assert res_lt_gen["extracted_rank"] == "Lt Gen"
        assert res_major["extracted_rank"] == "Major"
        assert classify_entity_pair(res_lt_gen, res_major) == "REVIEW_NEEDED"

        # 2. Exact vs Fuzzy non-exact with conflicting ranks
        res_col_fuzzy = agent.resolve_entity("Col. Upendra Dwevedi")
        assert res_col_fuzzy["extracted_rank"] == "Col."
        assert classify_entity_pair(res_lt_gen, res_col_fuzzy) == "REVIEW_NEEDED"

        # 3. Single-mention resolution with conflicting rank against canonical entity
        res_col_dwivedi = agent.resolve_entity("Colonel Upendra Dwivedi")
        assert res_col_dwivedi["action"] == "review_queue"
        assert res_col_dwivedi["match_method"] == "conflicting_rank_guard"
        assert res_col_dwivedi["extracted_rank"] == "Colonel"

        # 4. Equivalent rank abbreviations must match without conflict
        res_gen = agent.resolve_entity("General Upendra Dwivedi")
        res_gen_abbr = agent.resolve_entity("Gen Upendra Dwivedi")
        assert res_gen["extracted_rank"] == "General"
        assert res_gen_abbr["extracted_rank"] == "Gen"
        assert classify_entity_pair(res_gen, res_gen_abbr) == "MATCH"

        # 5. Mention without rank correctly matches canonical entity
        res_bare = agent.resolve_entity("Upendra Dwivedi")
        assert res_bare["extracted_rank"] is None
        assert classify_entity_pair(res_gen, res_bare) == "MATCH"

    def test_resolution_feedback_eval_runner_integration(self):
        """The benchmark evaluation runner runs cleanly and reports zero false auto-merges."""
        metrics = run_resolution_feedback_eval()

        assert metrics["sample_count"] == 30
        assert metrics["false_auto_merges"] == 0
        assert metrics["review_required_auto_linked"] == 0
        assert metrics["auto_link_precision"] == 1.0
        assert metrics["overall_safety_rate"] == 1.0
        assert metrics["review_queue_rate"] > 0.0

        sweep = sweep_resolution_thresholds()
        assert len(sweep) == 7
        for entry in sweep:
            assert entry["false_auto_merges"] == 0
            assert entry["auto_link_precision"] == 1.0
