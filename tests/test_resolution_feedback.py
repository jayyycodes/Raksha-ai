"""
Unit tests for ResolutionFeedback engine and its integration with ResolutionAgent.
Raksha AI Stage 3 Solid — Floor 2 (Language & Knowledge Agents)
Mandatory Safety Corrections & Final Review Test Suite
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from agents.resolution.agent import (
    CANONICAL_DEFENSE_ENTITIES,
    ResolutionAgent,
)
from agents.resolution.feedback import (
    FeedbackDecision,
    FeedbackRecord,
    ResolutionFeedbackStore,
    normalize_entity_name,
    normalize_timestamp,
    normalize_workspace_id,
)
from common.schemas.provenance import ClaimStatus


class TestResolutionFeedbackEngine(unittest.TestCase):
    """
    Test suite for FeedbackRecord validation, ResolutionFeedbackStore lifecycle,
    and ResolutionAgent feedback injection safety.
    """

    def setUp(self):
        self.t0 = datetime(2026, 11, 16, 10, 0, 0, tzinfo=timezone.utc)
        self.t1 = datetime(2026, 11, 16, 11, 0, 0, tzinfo=timezone.utc)
        self.t2 = datetime(2026, 11, 16, 12, 0, 0, tzinfo=timezone.utc)
        self.agent = ResolutionAgent()

    # 1. Input cannot override trusted workspace context
    def test_1_input_cannot_override_trusted_workspace_context(self):
        """Input dict containing a conflicting workspace_id cannot access that workspace's feedback."""
        alias = "Confidential Strike Unit"
        # Ingest feedback in workspace 999
        rec_999 = FeedbackRecord(
            source_mention=alias,
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-trusted-ws-999",
            reviewed_at=self.t1,
            workspace_id=999,
        )
        self.agent.add_feedback_records(rec_999)

        # Query batch within trusted workspace 101, but input dict attempts to spoof workspace_id=999
        batch_input = [
            {"name": alias, "workspace_id": 999},
        ]
        out = self.agent.run(batch_input, workspace_id=101)
        res = out["resolved_entities"][0]

        # Must strictly use trusted workspace 101 context: remains separate!
        self.assertEqual(res["action"], "separate")
        self.assertNotEqual(res["match_method"], "accepted_feedback_alias")
        self.assertEqual(res["workspace_id"], "101")

    # 2. Workspace 101 feedback cannot affect workspace 102
    def test_2_workspace_isolation_101_does_not_affect_102(self):
        custom_mention = "Project Suraksha Stealth Drone"
        rec_101 = FeedbackRecord(
            source_mention=custom_mention,
            target_canonical="Defence Research and Development Organisation",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-ws101",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_101)

        # In workspace 101, resolves to DRDO
        res_101 = self.agent.resolve_entity(custom_mention, workspace_id=101)
        self.assertEqual(res_101["action"], "auto_link")
        self.assertEqual(res_101["canonical_name"], "Defence Research and Development Organisation")

        # In workspace 102, remains unlinked / separate
        res_102 = self.agent.resolve_entity(custom_mention, workspace_id=102)
        self.assertEqual(res_102["action"], "separate")
        self.assertNotEqual(res_102["match_method"], "accepted_feedback_alias")

    # 3. Integer/string workspace ID consistency
    def test_3_integer_string_workspace_id_consistency(self):
        """Integer 101 and string '101' resolve identically across storage and lookup."""
        # Test normalizer directly
        self.assertEqual(normalize_workspace_id(101), "101")
        self.assertEqual(normalize_workspace_id("101"), "101")
        self.assertEqual(normalize_workspace_id(" 101 "), "101")
        self.assertIsNone(normalize_workspace_id(None))

        # Rejected types
        with self.assertRaises(TypeError):
            normalize_workspace_id(True)
        with self.assertRaises(TypeError):
            normalize_workspace_id(101.5)
        with self.assertRaises(TypeError):
            normalize_workspace_id(["101"])
        with self.assertRaises(ValueError):
            normalize_workspace_id(-1)
        with self.assertRaises(ValueError):
            normalize_workspace_id("   ")

        # Ingest as integer 101
        rec = FeedbackRecord(
            source_mention="Unit IntStr Test",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-intstr-1",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec)

        # Lookup with string "101"
        res_str = self.agent.resolve_entity("Unit IntStr Test", workspace_id="101")
        self.assertEqual(res_str["action"], "auto_link")
        self.assertEqual(res_str["canonical_name"], "Indian Air Force")

        # Lookup with integer 101
        res_int = self.agent.resolve_entity("Unit IntStr Test", workspace_id=101)
        self.assertEqual(res_int["action"], "auto_link")

    # 4. Naive timestamps are rejected
    def test_4_naive_timestamps_are_rejected(self):
        """Naive datetime without timezone info must be rejected with ValueError."""
        naive_dt = datetime(2026, 11, 16, 10, 0, 0)  # No tzinfo
        with self.assertRaises(ValueError):
            normalize_timestamp(naive_dt)

        with self.assertRaises(ValueError):
            FeedbackRecord(
                source_mention="Naive DT Test",
                target_canonical="Indian Air Force",
                decision=FeedbackDecision.ACCEPTED,
                decision_id="dec-naive-dt",
                reviewed_at=naive_dt,
                workspace_id=101,
            )

    # 5. Equivalent timezone-aware timestamps compare correctly
    def test_5_equivalent_timezone_aware_timestamps_compare_correctly(self):
        """UTC timestamp and offset timestamp for the exact same instant compare as equal."""
        # 10:00:00 UTC == 15:30:00 IST (+05:30)
        dt_utc = datetime(2026, 11, 16, 10, 0, 0, tzinfo=timezone.utc)
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        dt_ist = datetime(2026, 11, 16, 15, 30, 0, tzinfo=ist_tz)

        norm_utc = normalize_timestamp(dt_utc)
        norm_ist = normalize_timestamp(dt_ist)
        self.assertEqual(norm_utc, norm_ist)

        # Ingesting with dt_utc, then dt_ist for identical decision is idempotent
        rec_utc = FeedbackRecord(
            source_mention="TZ Equiv Mention",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-tz-1",
            reviewed_at=dt_utc,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_utc)

        # Re-ingest exact same decision with equivalent IST timestamp
        rec_ist = FeedbackRecord(
            source_mention="TZ Equiv Mention",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-tz-1",
            reviewed_at=dt_ist,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_ist)
        res = self.agent.resolve_entity("TZ Equiv Mention", workspace_id=101)
        self.assertEqual(res["action"], "auto_link")

        # Newer decision 30 minutes later in IST supersedes
        dt_ist_newer = datetime(2026, 11, 16, 16, 0, 0, tzinfo=ist_tz)
        rec_newer = FeedbackRecord(
            source_mention="TZ Equiv Mention",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-tz-2",
            reviewed_at=dt_ist_newer,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_newer)
        res_after = self.agent.resolve_entity("TZ Equiv Mention", workspace_id=101)
        self.assertEqual(res_after["action"], "separate")
        self.assertEqual(res_after["match_method"], "negative_feedback_constraint")

    # 6. Unknown canonical targets cannot auto-link
    def test_6_unknown_canonical_targets_cannot_auto_link(self):
        """Arbitrary or misspelled canonical target must fail closed and never auto-link."""
        rec = FeedbackRecord(
            source_mention="Shadow Squadron",
            target_canonical="NonExistent Space Force Command 999",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-bad-target",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec)

        res = self.agent.resolve_entity("Shadow Squadron", workspace_id=101)
        # Must fail closed: separate, never auto_link
        self.assertEqual(res["action"], "separate")
        self.assertNotEqual(res["action"], "auto_link")
        self.assertEqual(res["match_method"], "invalid_canonical_target_rejected")
        self.assertEqual(res["feedback_decision_id"], "dec-bad-target")

    # 7. Entity-type mismatch cannot auto-link
    def test_7_entity_type_mismatch_cannot_auto_link(self):
        """Feedback record specifying incompatible entity type for canonical target must fail closed."""
        # Indian Air Force is an ORGANISATION; feedback claims PERSON
        rec = FeedbackRecord(
            source_mention="Air Force Fleet",
            target_canonical="Indian Air Force",
            entity_type="PERSON",  # INCOMPATIBLE
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-type-mismatch",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec)

        res = self.agent.resolve_entity("Air Force Fleet", workspace_id=101)
        self.assertEqual(res["action"], "separate")
        self.assertNotEqual(res["action"], "auto_link")
        self.assertEqual(res["match_method"], "entity_type_mismatch_rejected")
        self.assertEqual(res["feedback_decision_id"], "dec-type-mismatch")

    # 8. One feedback-derived result does not falsely mark unrelated batch results analyst-verified
    def test_8_one_feedback_result_does_not_falsely_mark_batch_analyst_verified(self):
        """Batch provenance must remain conservative and not falsely elevate unrelated entities."""
        rec = FeedbackRecord(
            source_mention="Bravo Flight",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-mixed-batch",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec)

        # Batch contains 1 feedback entity ("Bravo Flight") and 1 baseline entity ("Siachen")
        batch_input = ["Bravo Flight", "Siachen"]
        out = self.agent.run(batch_input, workspace_id=101)
        entities = out["resolved_entities"]

        # Item 1 has feedback attribution
        self.assertEqual(entities[0]["action"], "auto_link")
        self.assertEqual(entities[0]["match_method"], "accepted_feedback_alias")
        self.assertEqual(entities[0]["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)
        self.assertEqual(entities[0]["feedback_decision_id"], "dec-mixed-batch")

        # Item 2 is baseline exact alias; must NOT be analyst verified
        self.assertEqual(entities[1]["action"], "auto_link")
        self.assertEqual(entities[1]["match_method"], "exact_defense_alias")
        self.assertEqual(entities[1]["claim_status"], ClaimStatus.OFFICIAL_DESIGNATION.value)
        self.assertNotIn("feedback_decision_id", entities[1])

        # Batch-level provenance must NOT be ANALYST_VERIFIED because the entire batch is not verified
        self.assertEqual(out["provenance"].claim_status, ClaimStatus.OFFICIAL_DESIGNATION)

    # 9. Reused conflicting decision IDs are handled safely
    def test_9_reused_conflicting_decision_ids_handled_safely(self):
        """Reusing an existing decision_id for a conflicting decision or pair must raise ValueError."""
        rec1 = FeedbackRecord(
            source_mention="Alpha Mention",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-reuse-id",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec1)

        # Attempt to reuse dec-reuse-id for a different pair
        rec2_conflicting = FeedbackRecord(
            source_mention="Beta Mention",
            target_canonical="Indian Navy",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-reuse-id",
            reviewed_at=self.t2,
            workspace_id=101,
        )
        with self.assertRaises(ValueError):
            self.agent.add_feedback_records(rec2_conflicting)

        # Ensure original record was not corrupted
        res_alpha = self.agent.resolve_entity("Alpha Mention", workspace_id=101)
        self.assertEqual(res_alpha["action"], "auto_link")
        self.assertEqual(res_alpha["canonical_name"], "Indian Air Force")

    # 10. Rejection against canonical A does not block a valid canonical B match
    def test_10_rejection_against_canonical_a_does_not_block_canonical_b_match(self):
        """Explicit rejection of (Mention, Canonical A) must never block matching to Canonical B."""
        # Mention "Vayu Guard": reject against Pakistan Air Force, accept for Indian Air Force
        rec_neg = FeedbackRecord(
            source_mention="Vayu Guard",
            target_canonical="Pakistan Air Force",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-vayu-neg",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        rec_pos = FeedbackRecord(
            source_mention="Vayu Guard",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-vayu-pos",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records([rec_neg, rec_pos])

        # Must auto-link to Indian Air Force without being blocked by the rejection of PAF
        res = self.agent.resolve_entity("Vayu Guard", workspace_id=101)
        self.assertEqual(res["action"], "auto_link")
        self.assertEqual(res["canonical_name"], "Indian Air Force")
        self.assertEqual(res["match_method"], "accepted_feedback_alias")

    # 11. Existing accepted/rejected supersession behavior remains correct
    def test_11_existing_supersession_behavior_remains_correct(self):
        # Older acceptance superseded by newer rejection
        rec_pos = FeedbackRecord(
            source_mention="Delta Wing",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-delta-pos",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        rec_neg = FeedbackRecord(
            source_mention="Delta Wing",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-delta-neg",
            reviewed_at=self.t2,
            workspace_id=101,
        )
        self.agent.add_feedback_records([rec_pos, rec_neg])
        res = self.agent.resolve_entity("Delta Wing", workspace_id=101)
        self.assertEqual(res["action"], "separate")
        self.assertEqual(res["match_method"], "negative_feedback_constraint")
        self.assertEqual(res["feedback_decision_id"], "dec-delta-neg")

    # 12. Static ontology remains unchanged
    def test_12_static_ontology_remains_unchanged(self):
        snapshot = deepcopy(CANONICAL_DEFENSE_ENTITIES)
        recs = [
            FeedbackRecord(
                source_mention="Test Mention 1",
                target_canonical="Indian Air Force",
                decision=FeedbackDecision.ACCEPTED,
                decision_id="dec-snap-1",
                reviewed_at=self.t1,
                workspace_id=101,
            ),
            FeedbackRecord(
                source_mention="Test Mention 2",
                target_canonical="Indian Navy",
                decision=FeedbackDecision.REJECTED,
                decision_id="dec-snap-2",
                reviewed_at=self.t1,
                workspace_id=101,
            ),
        ]
        self.agent.add_feedback_records(recs)
        self.assertEqual(CANONICAL_DEFENSE_ENTITIES, snapshot)

    # 13. Analyst verification semantics: accepted vs rejected provenance
    def test_13_analyst_verification_semantics_accepted_vs_rejected_provenance(self):
        """Accepted feedback is ANALYST_VERIFIED; rejected constraint is DISPUTED, never ANALYST_VERIFIED."""
        # 1. Accepted positive feedback
        rec_acc = FeedbackRecord(
            source_mention="Sarang Display Team",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-sarang-pos",
            reviewed_at=self.t1,
            analyst_id="analyst_kavita",
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_acc)
        res_acc = self.agent.resolve_entity("Sarang Display Team", workspace_id=101)

        self.assertEqual(res_acc["action"], "auto_link")
        self.assertEqual(res_acc["canonical_name"], "Indian Air Force")
        self.assertEqual(res_acc["match_method"], "accepted_feedback_alias")
        self.assertEqual(res_acc["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)
        self.assertEqual(res_acc["feedback_decision_id"], "dec-sarang-pos")
        self.assertEqual(res_acc["analyst_id"], "analyst_kavita")

        # 2. Rejected negative constraint
        rec_rej = FeedbackRecord(
            source_mention="Unverified Foreign Contingent",
            target_canonical="Indian Army",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-foreign-neg",
            reviewed_at=self.t1,
            analyst_id="analyst_kavita",
            workspace_id=101,
        )
        self.agent.add_feedback_records(rec_rej)
        res_rej = self.agent.resolve_entity("Unverified Foreign Contingent", workspace_id=101)

        # Negative feedback rejects association; must be DISPUTED, NOT ANALYST_VERIFIED
        self.assertEqual(res_rej["action"], "separate")
        self.assertEqual(res_rej["match_method"], "negative_feedback_constraint")
        self.assertEqual(res_rej["claim_status"], ClaimStatus.DISPUTED.value)
        self.assertNotEqual(res_rej["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)
        self.assertEqual(res_rej["feedback_decision_id"], "dec-foreign-neg")
        self.assertEqual(res_rej["analyst_id"], "analyst_kavita")

    # 14. Same source, two accepted targets, equal timestamps: fail closed
    def test_14_same_source_two_accepted_targets_equal_timestamps_fail_closed(self):
        """When multiple accepted targets exist at the exact same timestamp, fail closed."""
        rec_iaf = FeedbackRecord(
            source_mention="Ambiguous Eagle Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-eagle-iaf",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        rec_navy = FeedbackRecord(
            source_mention="Ambiguous Eagle Unit",
            target_canonical="Indian Navy",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-eagle-navy",
            reviewed_at=self.t1,  # Identical timestamp t1
            workspace_id=101,
        )
        self.agent.add_feedback_records([rec_iaf, rec_navy])

        res = self.agent.resolve_entity("Ambiguous Eagle Unit", workspace_id=101)
        # Ambiguous conflict at equal timestamp fails closed: separate, never auto_link
        self.assertEqual(res["action"], "separate")
        self.assertNotEqual(res["action"], "auto_link")

    # 15. Same source, two accepted targets, different timestamps: latest wins
    def test_15_same_source_two_accepted_targets_different_timestamps_latest_wins(self):
        """When multiple accepted targets exist with different timestamps, latest decision wins."""
        rec_iaf = FeedbackRecord(
            source_mention="Shifting Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-shift-iaf",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        rec_navy_newer = FeedbackRecord(
            source_mention="Shifting Unit",
            target_canonical="Indian Navy",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-shift-navy",
            reviewed_at=self.t2,  # t2 > t1
            workspace_id=101,
        )
        self.agent.add_feedback_records([rec_iaf, rec_navy_newer])

        res = self.agent.resolve_entity("Shifting Unit", workspace_id=101)
        self.assertEqual(res["action"], "auto_link")
        self.assertEqual(res["canonical_name"], "Indian Navy")
        self.assertEqual(res["feedback_decision_id"], "dec-shift-navy")

    # 16. Conflicting same-timestamp decisions never produce an automatic link
    def test_16_conflicting_same_timestamp_decisions_never_auto_link(self):
        """Equal-timestamp accepted and rejected decisions for same pair fail closed."""
        rec_acc = FeedbackRecord(
            source_mention="TugOfWar Mention",
            target_canonical="Indian Army",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-tow-acc",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        rec_rej = FeedbackRecord(
            source_mention="TugOfWar Mention",
            target_canonical="Indian Army",
            decision=FeedbackDecision.REJECTED,
            decision_id="dec-tow-rej",
            reviewed_at=self.t1,
            workspace_id=101,
        )
        self.agent.add_feedback_records([rec_acc, rec_rej])

        res = self.agent.resolve_entity("TugOfWar Mention", workspace_id=101)
        self.assertEqual(res["action"], "separate")
        self.assertNotEqual(res["action"], "auto_link")
        self.assertEqual(res["match_method"], "negative_feedback_constraint")
        self.assertEqual(res["claim_status"], ClaimStatus.DISPUTED.value)

    # 17. Empty batch provenance
    def test_17_empty_batch_provenance(self):
        """Empty input list returns empty resolved_entities with default provenance."""
        out = self.agent.run([], workspace_id=101)
        self.assertEqual(out["resolved_entities"], [])
        self.assertEqual(out["provenance"].confidence, 1.0)
        self.assertEqual(out["provenance"].claim_status, ClaimStatus.OFFICIAL_DESIGNATION)

    # 18. Batch with unsupported/skipped input items
    def test_18_batch_with_unsupported_skipped_items(self):
        """Unsupported input item types (int, None) are skipped without error."""
        out = self.agent.run([12345, "IAF", None], workspace_id=101)
        # Only "IAF" is processed
        self.assertEqual(len(out["resolved_entities"]), 1)
        self.assertEqual(out["resolved_entities"][0]["canonical_name"], "Indian Air Force")

    # 19. Common word safety guards cannot be bypassed
    def test_19_common_word_safety_guards_cannot_be_bypassed(self):
        """Common English words remain protected from feedback merging."""
        for word in ["Punch", "War", "West"]:
            rec = FeedbackRecord(
                source_mention=word,
                target_canonical="Indian Air Force",
                decision=FeedbackDecision.ACCEPTED,
                decision_id=f"dec-guard-{word}",
                reviewed_at=self.t1,
                workspace_id=101,
            )
            self.agent.add_feedback_records(rec)
            res = self.agent.resolve_entity(word, workspace_id=101)
            self.assertEqual(res["action"], "separate")
            self.assertEqual(res["match_method"], "common_english_word_guard")

    # 20. Identical attributed duplicate ingestion is idempotent
    def test_20_identical_attributed_duplicate_is_idempotent(self):
        rec = FeedbackRecord(
            source_mention="Unit Echo",
            target_canonical="Indian Army",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-idemp-attr",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_01",
            entity_type="ORGANISATION",
            notes="Initial review",
        )
        self.agent.add_feedback_records(rec)
        # Re-ingest exact same record
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity("Unit Echo", workspace_id=101)
        self.assertEqual(res["action"], "auto_link")
        self.assertEqual(res["canonical_name"], "Indian Army")

    # 21. Identical unattributed duplicate ingestion is deduplicated
    def test_21_identical_unattributed_duplicate_is_deduplicated(self):
        store = ResolutionFeedbackStore()
        rec_unattr = FeedbackRecord(
            source_mention="Unattributed Mention",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-idemp-unattr",
            reviewed_at=self.t1,
            workspace_id=None,
            is_global=False,
            analyst_id="analyst_02",
            entity_type="ORGANISATION",
            notes="No workspace attached",
        )
        store.add_record(rec_unattr)
        self.assertEqual(len(store.unattributed_records), 1)
        # Re-ingest identical record
        store.add_record(rec_unattr)
        self.assertEqual(len(store.unattributed_records), 1)

    # 22. Reused decision ID with different analyst_id raises ValueError
    def test_22_reused_decision_id_different_analyst_raises_value_error(self):
        rec1 = FeedbackRecord(
            source_mention="Mention Alpha",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-analyst-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_alice",
        )
        rec2 = FeedbackRecord(
            source_mention="Mention Alpha",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-analyst-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_bob",  # Conflicting analyst
        )
        self.agent.add_feedback_records(rec1)
        with self.assertRaises(ValueError):
            self.agent.add_feedback_records(rec2)

    # 23. Reused decision ID with different entity_type raises ValueError
    def test_23_reused_decision_id_different_entity_type_raises_value_error(self):
        rec1 = FeedbackRecord(
            source_mention="Mention Beta",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-etype-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type="ORGANISATION",
        )
        rec2 = FeedbackRecord(
            source_mention="Mention Beta",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-etype-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type="EQUIPMENT",  # Conflicting entity_type
        )
        self.agent.add_feedback_records(rec1)
        with self.assertRaises(ValueError):
            self.agent.add_feedback_records(rec2)

    # 24. Reused decision ID with different notes raises ValueError
    def test_24_reused_decision_id_different_notes_raises_value_error(self):
        rec1 = FeedbackRecord(
            source_mention="Mention Gamma",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-notes-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            notes="First note",
        )
        rec2 = FeedbackRecord(
            source_mention="Mention Gamma",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-notes-diff",
            reviewed_at=self.t1,
            workspace_id=101,
            notes="Conflicting note",
        )
        self.agent.add_feedback_records(rec1)
        with self.assertRaises(ValueError):
            self.agent.add_feedback_records(rec2)

    # 25. Original record remains unchanged after conflicting ingestion
    def test_25_original_record_remains_unchanged_after_conflicting_ingestion(self):
        store = ResolutionFeedbackStore()
        rec_orig = FeedbackRecord(
            source_mention="Mention Delta",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-immutable-check",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_orig",
            entity_type="ORGANISATION",
            notes="Original notes",
        )
        store.add_record(rec_orig)

        rec_conflict = FeedbackRecord(
            source_mention="Mention Delta",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-immutable-check",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_imposter",
            entity_type="ORGANISATION",
            notes="Original notes",
        )
        with self.assertRaises(ValueError):
            store.add_record(rec_conflict)

        # Inspect internal registry to ensure original record is preserved
        stored = store._records_by_decision_id["dec-immutable-check"]
        self.assertEqual(stored.analyst_id, "analyst_orig")
        self.assertEqual(stored.notes, "Original notes")

    # 26. Dual entity type: feedback matches and input hint matches -> accepted
    def test_26_dual_entity_type_feedback_matches_input_hint_matches_accepted(self):
        rec = FeedbackRecord(
            source_mention="Sky Falcon Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-type-match-both",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type="ORGANISATION",
        )
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity(
            "Sky Falcon Unit",
            entity_type_hint="ORGANISATION",
            workspace_id=101,
        )
        self.assertEqual(res["action"], "auto_link")
        self.assertEqual(res["match_method"], "accepted_feedback_alias")
        self.assertEqual(res["canonical_name"], "Indian Air Force")
        self.assertEqual(res["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)

    # 27. Dual entity type: feedback type missing, input hint conflicts -> fails closed
    def test_27_dual_entity_type_feedback_missing_input_hint_conflicts_fails_closed(self):
        rec = FeedbackRecord(
            source_mention="Sky Falcon Unit",
            target_canonical="Indian Air Force",  # Target canonical is ORGANISATION
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-type-hint-conflict-1",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type=None,
        )
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity(
            "Sky Falcon Unit",
            entity_type_hint="PERSON",  # Conflicts with ORGANISATION
            workspace_id=101,
        )
        self.assertEqual(res["action"], "separate")
        self.assertEqual(res["match_method"], "entity_type_mismatch_rejected")
        self.assertEqual(res["feedback_decision_id"], "dec-type-hint-conflict-1")
        self.assertEqual(res["claim_status"], ClaimStatus.REPORTED.value)

    # 28. Dual entity type: feedback type matches, input hint conflicts -> fails closed
    def test_28_dual_entity_type_feedback_matches_input_hint_conflicts_fails_closed(self):
        rec = FeedbackRecord(
            source_mention="Sky Falcon Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-type-hint-conflict-2",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type="ORGANISATION",
        )
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity(
            "Sky Falcon Unit",
            entity_type_hint="LOCATION",  # Conflicts with canonical ORGANISATION
            workspace_id=101,
        )
        self.assertEqual(res["action"], "separate")
        self.assertEqual(res["match_method"], "entity_type_mismatch_rejected")
        self.assertEqual(res["feedback_decision_id"], "dec-type-hint-conflict-2")
        self.assertEqual(res["claim_status"], ClaimStatus.REPORTED.value)

    # 29. Dual entity type: both feedback type and input hint conflict -> fails closed
    def test_29_dual_entity_type_both_types_conflict_fails_closed(self):
        rec = FeedbackRecord(
            source_mention="Sky Falcon Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-both-conflict",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type="PERSON",  # Conflicts with ORGANISATION
        )
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity(
            "Sky Falcon Unit",
            entity_type_hint="LOCATION",  # Also conflicts
            workspace_id=101,
        )
        self.assertEqual(res["action"], "separate")
        self.assertEqual(res["match_method"], "entity_type_mismatch_rejected")
        self.assertEqual(res["feedback_decision_id"], "dec-both-conflict")
        self.assertEqual(res["claim_status"], ClaimStatus.REPORTED.value)

    # 30. Dual entity type: neither type supplied -> retains safe existing behavior
    def test_30_dual_entity_type_neither_supplied_retains_safe_behavior(self):
        rec = FeedbackRecord(
            source_mention="Sky Falcon Unit",
            target_canonical="Indian Air Force",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-neither-type",
            reviewed_at=self.t1,
            workspace_id=101,
            entity_type=None,
        )
        self.agent.add_feedback_records(rec)
        res = self.agent.resolve_entity(
            "Sky Falcon Unit",
            entity_type_hint=None,
            workspace_id=101,
        )
        self.assertEqual(res["action"], "auto_link")
        self.assertEqual(res["canonical_name"], "Indian Air Force")
        self.assertEqual(res["match_method"], "accepted_feedback_alias")
        self.assertEqual(res["claim_status"], ClaimStatus.ANALYST_VERIFIED.value)

    # 31. Reused decision ID with variant raw strings but same normalized pair is idempotent
    def test_31_reused_decision_id_with_variant_raw_strings_same_normalized_pair_is_idempotent(self):
        """
        Re-ingesting a decision ID with variant raw strings (e.g. casing, honorific prefix, punctuation)
        that resolve to the exact same normalized_pair is treated as an idempotent duplicate.
        The original record in _records_by_decision_id remains completely unchanged to preserve audit provenance.
        """
        store = ResolutionFeedbackStore()
        rec_orig = FeedbackRecord(
            source_mention="Lt. Gen. Upendra Dwivedi",
            target_canonical="Indian Army",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-norm-idemp-1",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_dwivedi",
            entity_type="ORGANISATION",
            notes="Original reviewed mention with rank prefix",
        )
        store.add_record(rec_orig)

        # Variant raw strings: stripped rank in mention, uppercase target
        # Both produce normalized_pair == ("upendra dwivedi", "indian army")
        rec_variant = FeedbackRecord(
            source_mention="Upendra Dwivedi",
            target_canonical="INDIAN ARMY",
            decision=FeedbackDecision.ACCEPTED,
            decision_id="dec-norm-idemp-1",
            reviewed_at=self.t1,
            workspace_id=101,
            analyst_id="analyst_dwivedi",
            entity_type="ORGANISATION",
            notes="Original reviewed mention with rank prefix",
        )
        # Must NOT raise ValueError; treated as idempotent duplicate
        store.add_record(rec_variant)

        # Verify the original record in _records_by_decision_id remains completely intact (audit provenance preserved)
        self.assertEqual(len(store._records_by_decision_id), 1)
        stored = store._records_by_decision_id["dec-norm-idemp-1"]
        self.assertEqual(stored.source_mention, "Lt. Gen. Upendra Dwivedi")
        self.assertEqual(stored.target_canonical, "Indian Army")
        self.assertEqual(stored.analyst_id, "analyst_dwivedi")
        self.assertEqual(stored.notes, "Original reviewed mention with rank prefix")

        # Verify duplicate does not create another record in workspace or unattributed stores
        ws_map = store._workspace_stores["101"]
        self.assertEqual(len(ws_map), 1)
        self.assertEqual(len(store.unattributed_records), 0)
        pair_key = ("upendra dwivedi", "indian army")
        self.assertIn(pair_key, ws_map)
        self.assertEqual(ws_map[pair_key].record.source_mention, "Lt. Gen. Upendra Dwivedi")

        # Injected agent resolves both variants consistently to the canonical entity
        self.agent.set_feedback_store(store)
        res1 = self.agent.resolve_entity("Lt. Gen. Upendra Dwivedi", workspace_id=101)
        self.assertEqual(res1["action"], "auto_link")
        self.assertEqual(res1["canonical_name"], "Indian Army")

        res2 = self.agent.resolve_entity("Upendra Dwivedi", workspace_id=101)
        self.assertEqual(res2["action"], "auto_link")
        self.assertEqual(res2["canonical_name"], "Indian Army")


if __name__ == "__main__":
    unittest.main()
