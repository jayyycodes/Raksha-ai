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


THREADING_STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "of", "for", "to", "with", "and", "is", "was", "were",
    "by", "that", "this", "from", "as", "are", "be", "been", "has", "have", "had", "it", "its",
    "near", "after", "reported", "into", "over",
}

KNOWN_DISTINCT_SECTORS = {
    "poonch", "uri", "rajouri", "tangdhar", "kupwara", "baramulla", "mendhar", "gurez",
    "samba", "barmer", "jodhpur", "jaisalmer", "leh", "chushul", "demchok", "galwan",
    "mumbai", "shillong", "visakhapatnam", "kakinada", "gurdaspur",
}


def clean_tokens(text: str) -> Set[str]:
    """Extract lowercased alphanumeric words excluding high-frequency grammatical stopwords."""
    words = tokenize_text(text)
    return {w for w in words if w not in THREADING_STOPWORDS and len(w) > 2}


def parse_date_safely(date_val: Any) -> Optional[datetime]:
    """Safely parse ISO string or datetime object into UTC datetime."""
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val if date_val.tzinfo else date_val.replace(tzinfo=timezone.utc)
    if isinstance(date_val, str) and date_val.strip():
        s = date_val.strip()
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                return None
    return None


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
        article_date: Optional[Union[str, datetime]] = None,
    ) -> Tuple[float, str, str]:
        """
        Compute weighted multi-factor match score between an article and an event cluster.
        Returns (score, rationale, text_metric_used).
        """
        # 1. Entity Overlap (weight: 0.35)
        def _norm_entity_token(e: str) -> str:
            token = e.lower().strip()
            # Normalize aircraft/equipment mark designations (e.g. 'su-30mki' -> 'su-30', 'tejas mk1' -> 'tejas')
            # without corrupting unrelated words (e.g. 'kamki') or reducing 'mki' alone to an empty token.
            clean = re.sub(
                r"(?:[\s\-_]+(?:mki|mk[-_\.]?[1-4]|mark[-_\.]?[1-4])|(?<=\d)(?:mki|mk[-_\.]?[1-4]|mark[-_\.]?[1-4]))\b",
                "",
                token,
                flags=re.IGNORECASE,
            ).strip()
            token = clean if clean else token
            if token in ("lac", "line of actual control"):
                return "lac"
            if token in ("loc", "line of control"):
                return "loc"
            if token in ("indian armed forces", "indian army"):
                return "indian armed forces"
            return token

        art_ent_set = {_norm_entity_token(e) for e in article_entities if e}
        evt_ent_set = {_norm_entity_token(e) for e in event.get("entities", []) if e}
        shared_entities = art_ent_set & evt_ent_set
        entity_score = 0.0
        if art_ent_set and evt_ent_set:
            entity_score = compute_jaccard(art_ent_set, evt_ent_set)
            specific_keywords = {
                "galwan", "siachen", "brahmos", "agni-prime", "agni-p",
                "ins kolkata", "tangdhar", "chushul", "demchok", "akash-ng", "poorvi prahar"
            }
            if (shared_entities & specific_keywords) or len(shared_entities) >= 3:
                entity_score = min(1.0, entity_score + 0.30)
        elif shared_entities:
            entity_score = 0.40

        # Sub-regional Sector Conflict Check
        raw_art_ents = {e.lower().strip() for e in article_entities if e}
        raw_evt_ents = {e.lower().strip() for e in event.get("entities", []) if e}
        sec_art = raw_art_ents & KNOWN_DISTINCT_SECTORS
        sec_evt = raw_evt_ents & KNOWN_DISTINCT_SECTORS
        sector_conflict = bool(sec_art and sec_evt and not (sec_art & sec_evt))

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
            if evt_region in ("national", "general") or art_region in ("national", "general"):
                geo_score = 0.50
            elif evt_region == art_region or evt_region in art_region or art_region in evt_region:
                geo_score = 1.0
            else:
                geo_score = 0.15
        elif not evt_region and not art_region:
            geo_score = 0.50
        else:
            geo_score = 0.40

        # 4. Text / Semantic Similarity (weight: 0.20)
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
            title_tok_a = clean_tokens(article_title)
            title_tok_b = clean_tokens(event.get("title", ""))
            title_sim = compute_jaccard(title_tok_a, title_tok_b)

            all_tok_a = clean_tokens(f"{article_title} {article_content}")
            all_tok_b = clean_tokens(f"{event.get('title', '')} {event.get('summary', '')}")
            body_sim = compute_jaccard(all_tok_a, all_tok_b)

            text_sim = max(title_sim, min(1.0, (0.5 * title_sim) + (0.5 * min(1.0, body_sim * 2.5))))
            text_metric = "token_jaccard_fallback"

        # 5. Temporal Proximity
        temporal_penalty = 0.0
        delta_days = None
        art_dt = parse_date_safely(article_date)
        evt_dt = parse_date_safely(
            event.get("published_at") or event.get("created_at") or event.get("date")
        )
        if art_dt and evt_dt:
            delta_days = abs((art_dt - evt_dt).days)
            if delta_days > 365:
                temporal_penalty = -0.45
            elif delta_days > 180:
                temporal_penalty = -0.30
            elif delta_days > 45:
                temporal_penalty = -0.15
            elif delta_days > 14:
                temporal_penalty = -0.05
            elif delta_days <= 2:
                temporal_penalty = 0.05

        # Weighted composite score
        composite = (0.35 * entity_score) + (0.25 * type_score) + (0.20 * geo_score) + (0.20 * text_sim) + temporal_penalty
        composite = round(min(1.0, max(0.0, composite)), 4)

        # Operational safety bounds:
        if delta_days is not None and delta_days > 180:
            composite = min(composite, 0.35)
        elif delta_days is not None and delta_days > 30:
            composite = min(composite, 0.55)

        if sector_conflict:
            composite = min(composite, 0.42)

        # Preliminary / unconfirmed reports require analyst review rather than auto-linking
        full_text = f"{article_title} {article_content} {event.get('title', '')} {event.get('summary', '')}".lower()
        if any(w in full_text for w in ["unconfirmed", "preliminary", "unverified"]):
            composite = min(composite, 0.58)

        # Divergent event types without headline agreement require analyst review
        if art_type != evt_type:
            title_sim_val = compute_jaccard(clean_tokens(article_title), clean_tokens(event.get("title", "")))
            if title_sim_val < 0.15:
                composite = min(composite, 0.58)

        reasons = []
        if shared_entities:
            reasons.append(f"shared entities: [{', '.join(sorted(shared_entities)[:3])}]")
        if art_type == evt_type:
            reasons.append(f"matched event_type '{art_type}'")
        if geo_score >= 0.8:
            reasons.append(f"matching region '{event.get('region')}'")
        if art_dt and evt_dt:
            reasons.append(f"delta_days={abs((art_dt - evt_dt).days)}")
        reasons.append(f"{text_metric}: {text_sim:.2f}")

        rationale = "; ".join(reasons)
        return composite, rationale, text_metric

    def compare_articles(
        self,
        article_a: Dict[str, Any],
        article_b: Dict[str, Any],
        match_threshold: float = 0.65,
        review_threshold: float = 0.45,
        a_embedding: Optional[List[float]] = None,
        b_embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate pairwise relationship between two articles directly without fallback event leakage.
        Supports dense embeddings if supplied directly, pre-computed on article dicts, or generated.
        Returns:
        {
            "score": float,
            "relation": "MATCH" | "DISTINCT" | "REVIEW_NEEDED",
            "rationale": str,
            "text_metric": str,
        }
        """
        emb_a = a_embedding or article_a.get("embedding")
        if emb_a is None:
            a_text = f"{article_a.get('title', '')}. {article_a.get('content', '')}".strip()
            if a_text:
                try:
                    emb_a = generate_embedding(a_text)
                except Exception:
                    emb_a = None

        event_ref = {
            "id": article_a.get("id") or article_a.get("article_id") or 1,
            "title": article_a.get("title", ""),
            "summary": article_a.get("content", ""),
            "region": article_a.get("region"),
            "event_type": article_a.get("event_type", "general"),
            "entities": article_a.get("entities", []),
            "published_at": article_a.get("published_at") or article_a.get("date"),
            "embedding": emb_a,
        }

        emb_b = b_embedding or article_b.get("embedding")
        if emb_b is None:
            b_text = f"{article_b.get('title', '')}. {article_b.get('content', '')}".strip()
            if b_text:
                try:
                    emb_b = generate_embedding(b_text)
                except Exception:
                    emb_b = None

        score, rationale, metric = self.score_match(
            article_title=article_b.get("title", ""),
            article_content=article_b.get("content", ""),
            article_entities=article_b.get("entities", []),
            article_type=article_b.get("event_type", "general"),
            article_region=article_b.get("region"),
            event=event_ref,
            article_embedding=emb_b,
            article_date=article_b.get("published_at") or article_b.get("date"),
        )

        if score >= match_threshold:
            relation = "MATCH"
        elif score >= review_threshold:
            relation = "REVIEW_NEEDED"
        else:
            relation = "DISTINCT"

        return {
            "score": score,
            "relation": relation,
            "rationale": rationale,
            "text_metric": metric,
        }

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

        article_date = (
            getattr(input_data, "published_at", None)
            if isinstance(input_data, EventThreadingIn)
            else input_data.get("published_at") or input_data.get("date")
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
                article_date=article_date,
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
