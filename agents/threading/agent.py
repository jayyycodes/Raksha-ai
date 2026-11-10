"""
Event Threading Agent for Raksha AI.
Floor 2 — Language & Knowledge Agents
Owner: Ary
Stage: 2 Production Implementation

Links incoming defense articles to ongoing event clusters or seeds new event threads
using multi-factor matching: 768-dimensional embedding cosine similarity, entity overlap,
event type compatibility, and geographic alignment.
"""
from datetime import datetime, timezone
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from agents.base import BaseAgent
from common.logger import get_logger
from common.schemas.events import EventLinkOut, EventThreadingIn, EventThreadingOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from engine.embeddings import EMBEDDING_DIM, generate_embedding

logger = get_logger(__name__)

# Default active reference events when database is offline or unseeded
DEFAULT_ACTIVE_EVENTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Eastern Ladakh LAC Military Standoff & Border Talks",
        "region": "Eastern Ladakh",
        "event_type": "border_incident",
        "entities": ["LAC", "Line of Actual Control", "PLA", "Indian Army", "Ladakh", "Galwan Valley", "Pangong Tso"],
        "summary": "Ongoing border standoff and corp-commander level military de-escalation negotiations along the LAC.",
    },
    {
        "id": 2,
        "title": "Cross-Border LoC Ceasefire Monitoring and Infiltration Alerts",
        "region": "Jammu & Kashmir",
        "event_type": "border_incident",
        "entities": ["LoC", "Line of Control", "Pakistan Army", "Indian Army", "Poonch", "Rajouri", "Kashmir"],
        "summary": "Ceasefire observance and anti-infiltration surveillance along the Line of Control.",
    },
    {
        "id": 3,
        "title": "Indian Ocean Region Maritime Surveillance & Naval Exercises",
        "region": "Indian Ocean",
        "event_type": "naval",
        "entities": ["Indian Navy", "INS Vikrant", "INS Vikramaditya", "Arabian Sea", "Bay of Bengal", "PLAN"],
        "summary": "Maritime security operations, carrier strike group patrols, and anti-piracy deterrence in IOR.",
    },
    {
        "id": 4,
        "title": "Critical Infrastructure Cyber Attacks & State-Sponsored Espionage",
        "region": "National",
        "event_type": "cyber_attack",
        "entities": ["CERT-In", "DRDO", "Power Grid", "Cyber Command"],
        "summary": "Targeted cyber attacks and malware campaigns targeting Indian power and defense networks.",
    },
]


def tokenize_text(text: str) -> Set[str]:
    """Extract lowercased alphanumeric words for token matching."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
    return set(words)


def compute_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two numeric vectors.
    Strictly validates vector dimensionality and finite values.
    Returns float in range [0.0, 1.0].
    """
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimension mismatch: {len(vec_a)} vs {len(vec_b)}")

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for a, b in zip(vec_a, vec_b):
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("Vector contains non-finite values (NaN or Inf)")
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0

    sim = dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
    return max(0.0, min(1.0, float(sim)))


class ThreadingAgent(BaseAgent[Union[EventThreadingIn, Dict[str, Any]], EventThreadingOut]):
    """
    Evaluates articles for temporal and semantic event threading.
    Uses 768-dimensional sentence embeddings from engine.embeddings with
    transparent fallback to token Jaccard overlap when models are offline.
    """
    name: str = "threading_agent"
    version: str = "0.2.0"

    def __init__(self, known_events: Optional[List[Dict[str, Any]]] = None):
        super().__init__()
        self._events: List[Dict[str, Any]] = (
            list(known_events) if known_events is not None else list(DEFAULT_ACTIVE_EVENTS)
        )
        # Cache for event cluster embeddings: {event_id: 768-dim vector}
        self._event_embeddings_cache: Dict[int, List[float]] = {}

    def add_event(self, event: Dict[str, Any], embedding: Optional[List[float]] = None) -> None:
        """Register a new event cluster into the threading candidate pool."""
        self._events.append(event)
        if embedding is not None and len(embedding) == EMBEDDING_DIM:
            self._event_embeddings_cache[event.get("id", 0)] = embedding

    def _get_or_compute_event_embedding(self, event: Dict[str, Any]) -> Optional[List[float]]:
        """Retrieve cached embedding for an event cluster or compute it."""
        evt_id = event.get("id")
        if evt_id is not None and evt_id in self._event_embeddings_cache:
            return self._event_embeddings_cache[evt_id]

        # Check if pre-stored in event dictionary
        if "embedding" in event and isinstance(event["embedding"], list):
            vec = event["embedding"]
            if len(vec) == EMBEDDING_DIM and all(math.isfinite(v) for v in vec):
                if evt_id is not None:
                    self._event_embeddings_cache[evt_id] = vec
                return vec

        # Compute from event title and summary
        evt_text = f"{event.get('title', '')}. {event.get('summary', '')}".strip()
        if not evt_text:
            return None

        try:
            vec = generate_embedding(evt_text)
            if evt_id is not None:
                self._event_embeddings_cache[evt_id] = vec
            return vec
        except Exception as exc:
            logger.debug("Could not compute embedding for event #%s: %s", evt_id, exc)
            return None

    def score_match(
        self,
        article_title: str,
        article_content: str,
        article_entities: List[str],
        article_type: str,
        article_region: Optional[str],
        event: Dict[str, Any],
        article_embedding: Optional[List[float]] = None,
    ) -> Tuple[float, str, str]:
        """
        Compute weighted multi-factor match score between an article and an event cluster.
        Returns (score, rationale, text_metric_used).
        """
        # 1. Entity Overlap (weight: 0.35)
        art_ent_set = {e.lower().strip() for e in article_entities if e}
        evt_ent_set = {e.lower().strip() for e in event.get("entities", []) if e}
        shared_entities = art_ent_set & evt_ent_set
        entity_score = 0.0
        if art_ent_set and evt_ent_set:
            entity_score = compute_jaccard(art_ent_set, evt_ent_set)
            # Critical strategic keyword presence bonus
            if any(k in shared_entities for k in ["lac", "loc", "siachen", "galwan", "brahmos", "drdo"]):
                entity_score = min(1.0, entity_score + 0.30)
        elif shared_entities:
            entity_score = 0.50

        # 2. Event Type Alignment (weight: 0.25)
        evt_type = (event.get("event_type") or "general").lower()
        art_type = (article_type or "general").lower()
        if art_type == evt_type:
            type_score = 1.0
        elif (art_type in {"border_incident", "military_movement"} and evt_type in {"border_incident", "military_movement"}):
            type_score = 0.75
        elif art_type == "general" or evt_type == "general":
            type_score = 0.40
        else:
            type_score = 0.10

        # 3. Geographic / Region Alignment (weight: 0.20)
        evt_region = (event.get("region") or "").lower().strip()
        art_region = (article_region or "").lower().strip()
        if evt_region and art_region:
            if evt_region == art_region or evt_region in art_region or art_region in evt_region:
                geo_score = 1.0
            else:
                geo_score = 0.15
        elif not evt_region and not art_region:
            geo_score = 0.50
        else:
            geo_score = 0.40

        # 4. Text / Semantic Similarity (weight: 0.20)
        # Attempt 768-dimensional cosine similarity first
        text_sim = 0.0
        text_metric = "none"

        evt_embedding = self._get_or_compute_event_embedding(event)
        if article_embedding is not None and evt_embedding is not None:
            try:
                text_sim = compute_cosine_similarity(article_embedding, evt_embedding)
                text_metric = "cosine_embedding_768"
            except Exception as exc:
                logger.warning("Cosine similarity failed on event #%s: %s", event.get("id"), exc)
                text_sim = 0.0

        if text_metric == "none":
            # Transparent fallback to token Jaccard similarity when embeddings are unavailable
            art_tokens = tokenize_text(f"{article_title} {article_content}")
            evt_tokens = tokenize_text(f"{event.get('title', '')} {event.get('summary', '')}")
            text_sim = compute_jaccard(art_tokens, evt_tokens)
            text_metric = "token_jaccard_fallback"

        # Weighted composite score
        composite = (0.35 * entity_score) + (0.25 * type_score) + (0.20 * geo_score) + (0.20 * text_sim)
        composite = round(min(1.0, max(0.0, composite)), 4)

        reasons = []
        if shared_entities:
            reasons.append(f"shared entities: [{', '.join(sorted(shared_entities)[:3])}]")
        if art_type == evt_type:
            reasons.append(f"matched event_type '{art_type}'")
        if geo_score >= 0.8:
            reasons.append(f"matching region '{event.get('region')}'")
        reasons.append(f"{text_metric}: {text_sim:.2f}")

        rationale = "; ".join(reasons)
        return composite, rationale, text_metric

    def run(self, input_data: Union[EventThreadingIn, Dict[str, Any]]) -> EventThreadingOut:
        """
        Execute event threading on an article using dense embeddings and multi-factor matching.
        """
        if isinstance(input_data, EventThreadingIn):
            article_id = input_data.article_id
            title = input_data.title or ""
            content = input_data.content or ""
            entities = input_data.entities or []
            event_type = input_data.event_type or "general"
            region = input_data.region
        elif isinstance(input_data, dict):
            article_id = input_data.get("article_id") or input_data.get("id") or 0
            title = input_data.get("title") or ""
            content = input_data.get("content") or ""
            entities = input_data.get("entities") or []
            event_type = input_data.get("event_type") or "general"
            region = input_data.get("region")
        else:
            raise TypeError(f"Unsupported input type for ThreadingAgent: {type(input_data).__name__}")

        source_ids = [article_id] if article_id else []

        # Generate article embedding once for efficient candidate comparison
        article_text = f"{title}. {content}".strip()
        article_embedding: Optional[List[float]] = None
        used_embedding_pipeline = False

        if article_text:
            try:
                article_embedding = generate_embedding(article_text)
                used_embedding_pipeline = True
            except Exception as exc:
                logger.debug(
                    "Article embedding generation unavailable for #%s (%s); using fallback.",
                    article_id,
                    exc,
                )

        best_score = 0.0
        best_event: Optional[Dict[str, Any]] = None
        best_rationale = ""
        best_metric = "token_jaccard_fallback"
        candidate_links: List[EventLinkOut] = []

        # Compare against known active event clusters
        for evt in self._events:
            score, rationale, metric = self.score_match(
                title,
                content,
                entities,
                event_type,
                region,
                evt,
                article_embedding=article_embedding,
            )
            if score >= 0.40:
                link_method = (
                    "embedding_cosine_and_entities"
                    if metric == "cosine_embedding_768"
                    else "token_overlap_and_entities"
                )
                link_prov = Provenance(
                    source_ids=source_ids,
                    method=link_method,
                    model_version=f"{self.name}:{self.version}",
                    confidence=score,
                    claim_status=ClaimStatus.REPORTED,
                    source_type=SourceType.PUBLIC,
                )
                candidate_links.append(
                    EventLinkOut(
                        event_id=evt["id"],
                        article_id=article_id,
                        link_method=link_method,
                        confidence=score,
                        is_seed=False,
                        explanation=f"Match score {score:.2f} ({rationale})",
                        provenance=link_prov,
                    )
                )
            if score > best_score:
                best_score = score
                best_event = evt
                best_rationale = rationale
                best_metric = metric

        # Sort candidate links by descending confidence
        candidate_links.sort(key=lambda l: l.confidence, reverse=True)

        # Threading threshold: score >= 0.60 matches existing cluster
        THREADING_THRESHOLD = 0.60
        created_new_event = False
        new_event_title = None
        matched_event_id = None

        if best_event and best_score >= THREADING_THRESHOLD:
            matched_event_id = best_event["id"]
            created_new_event = False
        else:
            # Seed a new event cluster
            created_new_event = True
            matched_event_id = None
            category_label = event_type.replace("_", " ").title()
            new_event_title = f"{category_label}: {title[:75]}..." if len(title) > 75 else f"{category_label}: {title}"

            seed_prov = Provenance(
                source_ids=source_ids,
                method="new_cluster_seed",
                model_version=f"{self.name}:{self.version}",
                confidence=1.0,
                claim_status=ClaimStatus.REPORTED,
                source_type=SourceType.PUBLIC,
            )
            candidate_links.insert(
                0,
                EventLinkOut(
                    event_id=0,
                    article_id=article_id,
                    link_method="cluster_seed",
                    confidence=1.0,
                    is_seed=True,
                    explanation="Seed article for newly initialized event thread.",
                    provenance=seed_prov,
                ),
            )

        agent_method = (
            "multi_factor_768_embedding_threading"
            if used_embedding_pipeline and best_metric == "cosine_embedding_768"
            else "multi_factor_lexical_fallback_threading"
        )

        agent_prov = Provenance(
            source_ids=source_ids,
            method=agent_method,
            model_version=f"{self.name}:{self.version}",
            confidence=max(best_score, 0.70) if not created_new_event else 0.85,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return EventThreadingOut(
            article_id=article_id,
            matched_event_id=matched_event_id,
            candidate_links=candidate_links,
            created_new_event=created_new_event,
            new_event_title=new_event_title,
            provenance=agent_prov,
        )
