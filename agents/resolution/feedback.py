"""
Resolution Feedback Engine — Raksha AI Stage 3 Solid
Floor 2 — Language & Knowledge Agents
Owner: Ary

Implements isolated, validated feedback records, workspace-aware scoping,
runtime alias overlays (positive feedback), pair-specific negative constraints
(anti-merging rules), deterministic decision supersession, and fail-closed safety.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

PREFIX_PATTERN = re.compile(
    r"^(?:(?:General|Gen|Lt Gen|Lt\. Gen|Lieutenant General|Maj Gen|Maj\. Gen|Major General|"
    r"Brigadier|Brig|Col|Colonel|Maj|Major|Captain|Capt|Lieutenant|Lt|"
    r"Air Chief Marshal|Air Marshal|Air Commodore|Group Captain|Wing Commander|Squadron Leader|"
    r"Admiral|Vice Admiral|Rear Admiral|Commodore|"
    r"President|Prime Minister|PM|Defence Minister|Minister|Shri|Smt|Mr|Mrs|Ms|Dr)\.?\s+)+",
    re.IGNORECASE,
)


def normalize_entity_name(name: str) -> str:
    """
    Standardize entity string: strip ranks/honorifics,
    strip punctuation, collapse whitespace, and lowercase.
    """
    if not name:
        return ""
    cleaned = PREFIX_PATTERN.sub("", name.strip())
    cleaned = re.sub(r"[\.\,]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def normalize_workspace_id(workspace_id: Any) -> Optional[str]:
    """
    Normalize workspace ID to a standardized string representation.
    Accepts positive integers or non-empty strings.
    Rejects booleans, non-positive numbers, floats, or unsupported types.
    """
    if workspace_id is None:
        return None
    if isinstance(workspace_id, bool):
        raise TypeError("Boolean value is not a valid workspace_id")
    if isinstance(workspace_id, int):
        if workspace_id <= 0:
            raise ValueError(f"workspace_id must be a positive integer, got {workspace_id}")
        return str(workspace_id)
    if isinstance(workspace_id, str):
        cleaned = workspace_id.strip()
        if not cleaned:
            raise ValueError("workspace_id cannot be an empty or whitespace string")
        if cleaned.isdigit():
            val = int(cleaned)
            if val <= 0:
                raise ValueError(f"workspace_id must be a positive integer, got {val}")
            return str(val)
        return cleaned
    raise TypeError(f"workspace_id must be an int, str, or None, got {type(workspace_id).__name__}")


def normalize_timestamp(dt: Any) -> datetime:
    """
    Validate that dt is a timezone-aware datetime instance and normalize to UTC.
    Rejects naive datetimes.
    """
    if not isinstance(dt, datetime):
        raise TypeError(f"reviewed_at must be a datetime instance, got {type(dt).__name__}")
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("reviewed_at must be timezone-aware (naive datetimes are rejected)")
    return dt.astimezone(timezone.utc)


class FeedbackDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class FeedbackRecord:
    """
    Immutable, validated feedback record from human analyst verification.
    """
    source_mention: str
    target_canonical: str
    decision: Union[FeedbackDecision, str]
    decision_id: str
    reviewed_at: datetime
    entity_type: Optional[str] = None
    analyst_id: Optional[str] = None
    workspace_id: Optional[Union[int, str]] = None
    is_global: bool = False
    notes: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.source_mention, str) or not self.source_mention.strip():
            raise ValueError("source_mention must be a non-empty string")
        if not isinstance(self.target_canonical, str) or not self.target_canonical.strip():
            raise ValueError("target_canonical must be a non-empty string")
        if not isinstance(self.decision_id, (str, int)) or not str(self.decision_id).strip():
            raise ValueError("decision_id must be a non-empty string or integer")

        # Enforce timezone-aware timestamp normalized to UTC
        norm_dt = normalize_timestamp(self.reviewed_at)
        object.__setattr__(self, "reviewed_at", norm_dt)

        # Validate decision: accepted or rejected only
        dec_val = self.decision.value if isinstance(self.decision, FeedbackDecision) else str(self.decision).lower().strip()
        if dec_val not in (FeedbackDecision.ACCEPTED.value, FeedbackDecision.REJECTED.value):
            raise ValueError(f"Invalid decision '{self.decision}'. Must be 'accepted' or 'rejected'.")
        object.__setattr__(self, "decision", dec_val)

        # Validate workspace scope
        if self.is_global and self.workspace_id is not None:
            raise ValueError("FeedbackRecord cannot specify both is_global=True and a workspace_id")

        if self.workspace_id is not None:
            norm_ws = normalize_workspace_id(self.workspace_id)
            object.__setattr__(self, "workspace_id", norm_ws)

    @property
    def is_scoped(self) -> bool:
        """True if the record is explicitly scoped to a workspace or explicitly global."""
        return self.is_global or self.workspace_id is not None

    @property
    def normalized_pair(self) -> Tuple[str, str]:
        """Normalized pair tuple of (normalized_source_mention, normalized_target_canonical)."""
        return (
            normalize_entity_name(self.source_mention),
            normalize_entity_name(self.target_canonical),
        )


@dataclass
class _StoreEntry:
    """Internal entry tracking latest state, timestamp, and conflict status."""
    record: Optional[FeedbackRecord]
    last_timestamp: datetime
    is_conflict: bool = False


class ResolutionFeedbackStore:
    """
    In-memory isolated feedback container for ResolutionAgent.
    Enforces workspace scoping, deterministic supersession, and fail-closed conflict resolution.
    """

    def __init__(self):
        # workspace_id (normalized string) -> {(norm_source, norm_target): _StoreEntry}
        self._workspace_stores: Dict[str, Dict[Tuple[str, str], _StoreEntry]] = {}
        # {(norm_source, norm_target): _StoreEntry} for explicitly global rules
        self._global_store: Dict[Tuple[str, str], _StoreEntry] = {}
        # Records with unattributed/unknown workspace scope (kept for audit, never applied in resolution)
        self._unattributed_records: List[FeedbackRecord] = []
        # Registry of seen decision IDs to prevent conflicting reuse
        self._records_by_decision_id: Dict[str, FeedbackRecord] = {}

    @property
    def unattributed_records(self) -> List[FeedbackRecord]:
        """List of records with unknown workspace scope that were not applied."""
        return list(self._unattributed_records)

    def add_record(self, record: FeedbackRecord) -> None:
        """
        Ingest a single FeedbackRecord with conflict detection and supersession.
        """
        if not isinstance(record, FeedbackRecord):
            raise TypeError(f"Expected FeedbackRecord instance, got {type(record).__name__}")

        # Check decision_id uniqueness and conflict
        dec_id = str(record.decision_id).strip()
        if dec_id in self._records_by_decision_id:
            existing_rec = self._records_by_decision_id[dec_id]
            if (
                existing_rec.normalized_pair == record.normalized_pair
                and existing_rec.decision == record.decision
                and existing_rec.workspace_id == record.workspace_id
                and existing_rec.is_global == record.is_global
                and existing_rec.reviewed_at == record.reviewed_at
                and existing_rec.analyst_id == record.analyst_id
                and existing_rec.entity_type == record.entity_type
                and existing_rec.notes == record.notes
            ):
                # Identical duplicate ingestion is completely idempotent.
                # Normalized identity (normalized_pair) is intentionally sufficient to accommodate
                # superficial surface variations (casing, punctuation, stripped rank prefixes)
                # under the same decision ID without corrupting state. Crucially, the original record
                # in _records_by_decision_id is never overwritten, preserving original audit strings.
                pass
            else:
                raise ValueError(
                    f"Conflicting reuse of decision_id '{dec_id}': cannot overwrite or corrupt existing decision for {existing_rec.normalized_pair}."
                )
        else:
            self._records_by_decision_id[dec_id] = record

        # Unknown workspace scope: store for tracking, but do NOT apply
        if not record.is_global and record.workspace_id is None:
            if record not in self._unattributed_records:
                self._unattributed_records.append(record)
            return

        # Determine target store
        if record.is_global:
            target_map = self._global_store
        else:
            ws_id = normalize_workspace_id(record.workspace_id)
            if ws_id not in self._workspace_stores:
                self._workspace_stores[ws_id] = {}
            target_map = self._workspace_stores[ws_id]

        pair_key = record.normalized_pair

        if pair_key not in target_map:
            target_map[pair_key] = _StoreEntry(
                record=record,
                last_timestamp=record.reviewed_at,
                is_conflict=False,
            )
            return

        entry = target_map[pair_key]

        if record.reviewed_at > entry.last_timestamp:
            # Newer decision supersedes older decision
            target_map[pair_key] = _StoreEntry(
                record=record,
                last_timestamp=record.reviewed_at,
                is_conflict=False,
            )
        elif record.reviewed_at < entry.last_timestamp:
            # Older decision arrives later; discard/ignore
            return
        else:
            # Exact same timestamp
            if entry.is_conflict:
                # Already in conflict at this timestamp; stay in conflict
                return
            if entry.record is not None and entry.record.decision == record.decision:
                # Idempotent re-ingestion of identical decision
                return
            # Conflicting decisions at exact same timestamp -> FAIL CLOSED!
            target_map[pair_key] = _StoreEntry(
                record=None,
                last_timestamp=record.reviewed_at,
                is_conflict=True,
            )

    def add_records(self, records: Iterable[FeedbackRecord]) -> None:
        """Ingest multiple FeedbackRecords."""
        for r in records:
            self.add_record(r)

    def is_pair_rejected(
        self,
        source_mention: str,
        target_canonical: str,
        workspace_id: Optional[Union[int, str]] = None,
    ) -> Tuple[bool, Optional[FeedbackRecord], str]:
        """
        Check if (source_mention, target_canonical) is blocked by a negative constraint or conflict.
        Returns: (is_blocked, matching_record, reason)
        """
        pair_key = (
            normalize_entity_name(source_mention),
            normalize_entity_name(target_canonical),
        )
        ws_norm = normalize_workspace_id(workspace_id)

        # 1. Check workspace-specific store first if workspace_id is provided
        if ws_norm is not None:
            ws_store = self._workspace_stores.get(ws_norm, {})
            if pair_key in ws_store:
                entry = ws_store[pair_key]
                if entry.is_conflict:
                    return True, None, "conflict_fail_closed"
                if entry.record and entry.record.decision == FeedbackDecision.REJECTED.value:
                    return True, entry.record, "workspace_negative_constraint"
                if entry.record and entry.record.decision == FeedbackDecision.ACCEPTED.value:
                    # Explicit workspace acceptance overrides global rejection
                    return False, entry.record, "workspace_accepted"

        # 2. Check global store
        if pair_key in self._global_store:
            entry = self._global_store[pair_key]
            if entry.is_conflict:
                return True, None, "conflict_fail_closed"
            if entry.record and entry.record.decision == FeedbackDecision.REJECTED.value:
                return True, entry.record, "global_negative_constraint"

        return False, None, ""

    def get_positive_alias(
        self,
        source_mention: str,
        workspace_id: Optional[Union[int, str]] = None,
    ) -> Tuple[Optional[FeedbackRecord], str]:
        """
        Lookup accepted alias rule for source_mention in the given workspace scope.
        Returns: (matching_record, reason)
        """
        norm_source = normalize_entity_name(source_mention)
        if not norm_source:
            return None, ""

        ws_norm = normalize_workspace_id(workspace_id)
        candidates: List[FeedbackRecord] = []

        # 1. Check workspace store if workspace_id provided
        if ws_norm is not None:
            ws_store = self._workspace_stores.get(ws_norm, {})
            ws_candidates: List[FeedbackRecord] = []
            has_conflict = False
            for (s, t), entry in ws_store.items():
                if s == norm_source:
                    if entry.is_conflict:
                        has_conflict = True
                    elif entry.record and entry.record.decision == FeedbackDecision.ACCEPTED.value:
                        ws_candidates.append(entry.record)

            if has_conflict:
                return None, "conflict_fail_closed"
            if ws_candidates:
                candidates = ws_candidates

        # 2. If no workspace candidates found, check global store
        if not candidates:
            global_candidates: List[FeedbackRecord] = []
            has_conflict = False
            for (s, t), entry in self._global_store.items():
                if s == norm_source:
                    if entry.is_conflict:
                        has_conflict = True
                    elif entry.record and entry.record.decision == FeedbackDecision.ACCEPTED.value:
                        global_candidates.append(entry.record)

            if has_conflict:
                return None, "conflict_fail_closed"
            candidates = global_candidates

        if not candidates:
            return None, ""

        if len(candidates) == 1:
            return candidates[0], "accepted_feedback_alias"

        # Multiple candidates: sort by reviewed_at DESC
        candidates.sort(key=lambda r: r.reviewed_at, reverse=True)
        if candidates[0].reviewed_at > candidates[1].reviewed_at:
            return candidates[0], "accepted_feedback_alias"

        # Equal timestamp conflict among multiple accepted candidates -> fail closed
        return None, "ambiguous_alias_conflict_fail_closed"

    def get_negative_constraint_or_conflict(
        self,
        source_mention: str,
        workspace_id: Optional[Union[int, str]] = None,
    ) -> Tuple[bool, Optional[FeedbackRecord], str, Optional[str]]:
        """
        Check if source_mention has any active negative constraint or conflict.
        Returns: (has_constraint, record, reason, target_canonical)
        """
        norm_source = normalize_entity_name(source_mention)
        if not norm_source:
            return False, None, "", None

        ws_norm = normalize_workspace_id(workspace_id)

        # 1. Check workspace store if workspace_id provided
        if ws_norm is not None:
            ws_store = self._workspace_stores.get(ws_norm, {})
            for (s, t), entry in ws_store.items():
                if s == norm_source:
                    if entry.is_conflict:
                        return True, None, "conflict_fail_closed", t
                    if entry.record and entry.record.decision == FeedbackDecision.REJECTED.value:
                        return True, entry.record, "workspace_negative_constraint", entry.record.target_canonical

        # 2. Check global store
        for (s, t), entry in self._global_store.items():
            if s == norm_source:
                if entry.is_conflict:
                    return True, None, "conflict_fail_closed", t
                if entry.record and entry.record.decision == FeedbackDecision.REJECTED.value:
                    return True, entry.record, "global_negative_constraint", entry.record.target_canonical

        return False, None, "", None
