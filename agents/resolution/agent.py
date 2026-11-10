"""
Entity Resolution Agent for Raksha AI.
Floor 2 — Language & Knowledge Agents
Owner: Ary
Stage: 2 Production Implementation

Implements entity normalization, alias matching, defense ontology lookup,
Indic romanization transliteration variants, and conservative contextual embedding matching.
"""
from difflib import SequenceMatcher
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from agents.base import BaseAgent
from common.logger import get_logger
from common.schemas.articles import EntityOut
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from engine.embeddings import EMBEDDING_DIM, generate_embedding

logger = get_logger(__name__)

# Military ranks, honorifics, and prefixes to strip for canonical resolution
PREFIX_PATTERN = re.compile(
    r"^(?:(?:General|Gen|Lt Gen|Lt\. Gen|Lieutenant General|Maj Gen|Maj\. Gen|Major General|"
    r"Brigadier|Brig|Col|Colonel|Maj|Major|Captain|Capt|Lieutenant|Lt|"
    r"Air Chief Marshal|Air Marshal|Air Commodore|Group Captain|Wing Commander|Squadron Leader|"
    r"Admiral|Vice Admiral|Rear Admiral|Commodore|"
    r"President|Prime Minister|PM|Defence Minister|Minister|Shri|Smt|Mr|Mrs|Ms|Dr)\.?\s+)+",
    re.IGNORECASE,
)

# Common generic words that must never be merged automatically without strong evidence
COMMON_AMBIGUOUS_NAMES: Set[str] = {
    "singh", "kumar", "khan", "sharma", "patel", "ali", "ahmed", "li", "wang", "zhang",
    "chen", "liu", "yang", "huang", "wu", "zhao", "zhou", "xu", "sun", "ma", "zhu", "hu",
    "army", "force", "forces", "navy", "air force", "military", "police", "troops",
    "sector", "base", "border", "camp", "post", "brigade", "division", "regiment",
    "missile", "jet", "aircraft", "commander", "officer", "spokesman", "official",
    "general", "leader", "chief", "source", "insurgent", "militant", "terrorist",
}

# Common English words that must never be phonetically mutated or merged as transliterations
COMMON_ENGLISH_WORDS: Set[str] = {
    "punch", "punching", "punches", "west", "western", "vest", "vesting", "war", "wars",
    "wood", "woods", "wing", "wings", "force", "forces", "front", "guard", "fire",
    "post", "line", "point", "lake", "river", "valley", "camp", "base", "head",
    "corps", "command", "station", "union", "peace", "strike", "action", "order",
}

# Curated Defense Knowledge Base:
# Canonical Name -> (Entity Type, Aliases List, Context Description)
CANONICAL_DEFENSE_ENTITIES: Dict[str, Tuple[str, List[str], str]] = {
    # Organizations — India
    "Indian Army": (
        "ORGANISATION",
        ["ia", "indian army", "army of india", "bharatiya thalsena", "thalsena"],
        "Indian land warfare ground forces defence infantry armoured military troops Northern Command",
    ),
    "Indian Air Force": (
        "ORGANISATION",
        ["iaf", "indian air force", "air force of india", "bharatiya vayu sena", "vayu sena"],
        "Indian air warfare aerial defence fighter jets transport squadron aircraft combat pilots",
    ),
    "Indian Navy": (
        "ORGANISATION",
        ["in", "indian navy", "navy of india", "bharatiya nausena", "nausena"],
        "Indian maritime naval defence aircraft carriers warships submarines fleet Western Naval Command",
    ),
    "Defence Research and Development Organisation": (
        "ORGANISATION",
        ["drdo", "defence research and development organisation", "defense research and development organisation", "defence research & development organisation"],
        "Defence research military technology weapons missiles laboratory DRDO indigenous systems testing",
    ),
    "Indian Space Research Organisation": (
        "ORGANISATION",
        ["isro", "indian space research organisation", "space research organisation"],
        "Indian civilian and military satellite launch telemetry earth observation orbital defence",
    ),
    "Research and Analysis Wing": (
        "ORGANISATION",
        ["raw", "r&aw", "research and analysis wing"],
        "Foreign external intelligence service national security foreign espionage threat intelligence",
    ),
    "Intelligence Bureau": (
        "ORGANISATION",
        ["ib", "intelligence bureau"],
        "Domestic internal security counter intelligence surveillance Ministry of Home Affairs",
    ),
    # Organizations — Regional / Adversaries
    "People's Liberation Army": (
        "ORGANISATION",
        ["pla", "peoples liberation army", "people's liberation army", "chinese army", "chinese military", "pla ground force"],
        "Chinese military armed forces ground troops border Western Theater Command Beijing",
    ),
    "People's Liberation Army Air Force": (
        "ORGANISATION",
        ["plaaf", "peoples liberation army air force", "people's liberation army air force", "chinese air force"],
        "Chinese aerial military air force combat aircraft fighter jets Tibet airbases",
    ),
    "People's Liberation Army Navy": (
        "ORGANISATION",
        ["plan", "peoples liberation army navy", "people's liberation army navy", "chinese navy"],
        "Chinese maritime fleet submarines surface combatants naval exercises Indian Ocean",
    ),
    "Pakistan Army": (
        "ORGANISATION",
        ["pak army", "pakistan army"],
        "Pakistani ground forces military Rawalpindi General Headquarters border corps",
    ),
    "Pakistan Air Force": (
        "ORGANISATION",
        ["paf", "pakistan air force"],
        "Pakistani aerial military fighter jets combat pilots airbases interception",
    ),
    "Pakistan Navy": (
        "ORGANISATION",
        ["pn", "pakistan navy"],
        "Pakistani maritime naval fleet Arabian Sea coastal defence Karachi naval base",
    ),
    "Inter-Services Intelligence": (
        "ORGANISATION",
        ["isi", "inter-services intelligence", "inter services intelligence"],
        "Pakistani military intelligence agency espionage covert security operations Islamabad",
    ),
    "Jaish-e-Mohammed": (
        "ORGANISATION",
        ["jem", "jaish-e-mohammed", "jaish-e-mohammad", "jaish-i-mohammed", "jaish e mohammed", "jaish-i-muhammad"],
        "Designated terrorist militant organization Kashmir insurgency cross-border attacks suicide bombings",
    ),
    "Lashkar-e-Taiba": (
        "ORGANISATION",
        ["let", "lashkar-e-taiba", "lashkar-e-tayyiba", "lashkar-i-taiba", "lashkar e toiba"],
        "Designated militant terrorist organization cross-border infiltration terror training camps",
    ),
    # Strategic Locations
    "Line of Actual Control": (
        "LOCATION",
        ["lac", "line of actual control", "sino-indian lac", "lac border"],
        "Sino-Indian border demarcation line Eastern Ladakh Arunachal Pradesh military standoff patrol points",
    ),
    "Line of Control": (
        "LOCATION",
        ["loc", "line of control", "indo-pak loc", "loc border", "ceasefire line"],
        "Indo-Pak military boundary Jammu and Kashmir Poonch Rajouri ceasefire cross-border firing",
    ),
    "Siachen Glacier": (
        "LOCATION",
        ["siachen", "siachen glacier", "saltoro ridge"],
        "High-altitude military outpost Karakoram Range Saltoro ridge glacier northern Ladakh extreme cold",
    ),
    "Galwan Valley": (
        "LOCATION",
        ["galwan", "galwan valley", "patrolling point 14", "pp14"],
        "Eastern Ladakh river valley June 2020 military clash patrolling point 14 disengagement",
    ),
    "Pangong Tso": (
        "LOCATION",
        ["pangong", "pangong tso", "pangong lake", "finger 4", "finger 8"],
        "High-altitude endorheic lake Eastern Ladakh Finger areas north bank south bank military patrol",
    ),
    "Doklam Plateau": (
        "LOCATION",
        ["doklam", "doklam plateau", "donglang"],
        "Tri-junction plateau border Bhutan India China 2017 military standoff Siliguri corridor",
    ),
    "Daulat Beg Oldie": (
        "LOCATION",
        ["dbo", "daulat beg oldie", "daulat beg oldi"],
        "Advanced landing ground military airstrip northern Ladakh Sub-Sector North Karakoram Pass",
    ),
    "Rawalpindi": (
        "LOCATION",
        ["rawalpindi", "ravalpindi", "pindi"],
        "Pakistani garrison city military General Headquarters Punjab Pakistan near Islamabad",
    ),
    "Islamabad": (
        "LOCATION",
        ["islamabad", "islamabad capital"],
        "Capital city Pakistan federal administration diplomatic foreign ministry",
    ),
    "New Delhi": (
        "LOCATION",
        ["delhi", "new delhi", "national capital region"],
        "Capital city India South Block North Block Ministry of Defence national leadership",
    ),
    "Beijing": (
        "LOCATION",
        ["beijing", "peking"],
        "Capital city China Central Military Commission Zhongnanhai national government",
    ),
    # Equipment & Weapons
    "BrahMos": (
        "EQUIPMENT",
        ["brahmos", "brahmos missile", "brahmos supersonic cruise missile", "brahmos aerospace"],
        "Supersonic cruise missile joint venture DRDO NPO Mashinostroyeniya precision strike weapon",
    ),
    "Dassault Rafale": (
        "EQUIPMENT",
        ["rafale", "dassault rafale", "rafale fighter", "rafale jets"],
        "French multirole twin-engine fighter aircraft Indian Air Force Meteor missiles Ambala Hasimara",
    ),
    "HAL Tejas": (
        "EQUIPMENT",
        ["tejas", "hal tejas", "lca tejas", "light combat aircraft tejas"],
        "Indigenous single-engine light combat aircraft Hindustan Aeronautics Limited Indian Air Force",
    ),
    "Sukhoi Su-30MKI": (
        "EQUIPMENT",
        ["su-30mki", "su-30", "su30", "sukhoi-30", "sukhoi su-30"],
        "Twin-engine air superiority multirole combat fighter jet license built HAL Indian Air Force",
    ),
    "S-400 Triumf": (
        "EQUIPMENT",
        ["s-400", "s400", "s-400 triumf", "sa-21 growler"],
        "Long-range mobile surface-to-air missile air defence system Russian supplied radar interceptor",
    ),
    "Agni-V": (
        "EQUIPMENT",
        ["agni-v", "agni 5", "agni-5", "agni v"],
        "Canisterised intercontinental ballistic missile nuclear capable strategic strike MIRV DRDO",
    ),
    "Agni-P": (
        "EQUIPMENT",
        ["agni-p", "agni prime", "agni-prime"],
        "Next generation medium-range canisterised nuclear capable ballistic missile DRDO tested",
    ),
    "INS Vikrant": (
        "EQUIPMENT",
        ["ins vikrant", "vikrant", "iac-1"],
        "Indigenous aircraft carrier Indian Navy Cochin Shipyard MiG-29K aviation strike carrier",
    ),
    "INS Vikramaditya": (
        "EQUIPMENT",
        ["ins vikramaditya", "vikramaditya"],
        "Modified Kiev-class aircraft carrier flagship Indian Navy Western Fleet Arabian Sea",
    ),
    "JF-17 Thunder": (
        "EQUIPMENT",
        ["jf-17", "jf17", "jf-17 thunder", "fc-1 xiaolong"],
        "Single-engine multirole combat aircraft Pakistan Air Force Chengdu PAC Kamra",
    ),
    "Chengdu J-20": (
        "EQUIPMENT",
        ["j-20", "j20", "chengdu j-20", "mighty dragon"],
        "Fifth-generation stealth air superiority twin-jet fighter aircraft People's Liberation Army Air Force",
    ),
}


def normalize_indic_romanization_variants(text: str) -> str:
    """
    Normalizes specific composite name connectors and vetted orthographic variants
    found in South Asian defense English transliterations (e.g. Urdu/Hindi romanizations):
      - Connectors: '-e-', '-i-', '-ul-', '-al-' standardized to consistent tokens.
      - Suffixes: 'muhammad' / 'mohammad' -> 'mohammed'.
      - Specific geographic variant: 'ravalpindi' -> 'rawalpindi'.
    NOTE: Does NOT perform destructive blind folds (such as arbitrary w->v or oo->u)
    to prevent corrupting legitimate English words (such as 'west' -> 'vest' or 'punch' -> 'poonch').
    """
    if not text:
        return ""
    t = text.lower().strip()
    if t in COMMON_ENGLISH_WORDS or t in COMMON_AMBIGUOUS_NAMES:
        return t
    # Normalize connectors in composite names (Jaish-e-Mohammed, Hizb-ul-Mujahideen)
    t = re.sub(r"[\-\_\s]+(?:e|i|ul|al)[\-\_\s]+", " ", t)
    t = re.sub(r"\bhizb(?:ul)?\b", "hizb", t)
    t = re.sub(r"m[ou]hamm?[ae]d", "mohammed", t)
    t = re.sub(r"\bravalpindi\b", "rawalpindi", t)
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_entity_name(name: str) -> str:
    """
    Standardize raw entity string: strip honorifics/ranks,
    lowercase, and normalize whitespace and common punctuation.
    """
    if not name:
        return ""
    cleaned = PREFIX_PATTERN.sub("", name.strip())
    cleaned = re.sub(r"[\.\,]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def compute_string_similarity(a: str, b: str) -> float:
    """Return standard sequence similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two numeric vectors.
    Validates dimensional consistency and finite values.
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


class ResolutionAgent(BaseAgent[Union[List[str], List[Dict[str, Any]], List[EntityOut]], Dict[str, Any]]):
    """
    Resolves extracted entities against canonical knowledge entities,
    differentiating strong matches (auto_link), ambiguous matches (review_queue),
    and unlinked entities (separate) using alias matching, transliteration normalization,
    and optional contextual dense embeddings.
    """
    name: str = "resolution_agent"
    version: str = "0.2.0"

    def __init__(self):
        super().__init__()
        # Invert canonical alias map for exact lookup: normalized_alias -> (canonical, etype, context_desc)
        self._alias_to_canonical: Dict[str, Tuple[str, str, str]] = {}
        # Inverted romanized transliteration map
        self._translit_to_canonical: Dict[str, Tuple[str, str, str]] = {}
        # Cached 768-dim embeddings for canonical entity descriptions
        self._canonical_context_embeddings: Dict[str, List[float]] = {}

        for canonical, (etype, aliases, context_desc) in CANONICAL_DEFENSE_ENTITIES.items():
            norm_canonical = normalize_entity_name(canonical)
            self._alias_to_canonical[norm_canonical] = (canonical, etype, context_desc)
            self._translit_to_canonical[normalize_indic_romanization_variants(canonical)] = (canonical, etype, context_desc)

            for alias in aliases:
                norm_alias = normalize_entity_name(alias)
                self._alias_to_canonical[norm_alias] = (canonical, etype, context_desc)
                translit_alias = normalize_indic_romanization_variants(alias)
                self._translit_to_canonical[translit_alias] = (canonical, etype, context_desc)

    def _get_canonical_embedding(self, canonical_name: str, context_desc: str) -> Optional[List[float]]:
        """Retrieve or lazily compute 768-dim context embedding for canonical entity."""
        if canonical_name in self._canonical_context_embeddings:
            return self._canonical_context_embeddings[canonical_name]
        try:
            vec = generate_embedding(context_desc)
            if len(vec) == EMBEDDING_DIM:
                self._canonical_context_embeddings[canonical_name] = vec
                return vec
        except Exception as exc:
            logger.debug("Canonical embedding computation unavailable for %s: %s", canonical_name, exc)
        return None

    def resolve_entity(
        self,
        raw_name: str,
        entity_type_hint: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a single entity name into its canonical identity and action tier.
        Optionally uses surrounding textual context for dense semantic verification.
        """
        trimmed = raw_name.strip()
        clean_name = PREFIX_PATTERN.sub("", trimmed).strip()
        norm_name = normalize_entity_name(trimmed)
        translit_name = normalize_indic_romanization_variants(trimmed)

        if not norm_name:
            return {
                "raw_name": raw_name,
                "canonical_name": raw_name,
                "entity_type": entity_type_hint or "UNKNOWN",
                "confidence": 0.0,
                "action": "separate",
                "decision": "separate",
                "match_method": "empty_input",
                "explanation": "Empty entity string",
            }

        # Guard 1: Check for common English dictionary words
        tokens = norm_name.split()
        if len(tokens) == 1 and tokens[0] in COMMON_ENGLISH_WORDS:
            return {
                "raw_name": raw_name,
                "canonical_name": clean_name or trimmed,
                "entity_type": entity_type_hint or "UNKNOWN",
                "confidence": 0.20,
                "action": "separate",
                "decision": "separate",
                "match_method": "common_english_word_guard",
                "explanation": f"Common English word '{tokens[0]}' protected from transliteration/alias merging.",
            }

        # Guard 2: Check for ambiguous common single-token generic names
        if len(tokens) == 1 and tokens[0] in COMMON_AMBIGUOUS_NAMES:
            return {
                "raw_name": raw_name,
                "canonical_name": clean_name or trimmed,
                "entity_type": entity_type_hint or "UNKNOWN",
                "confidence": 0.35,
                "action": "separate",
                "decision": "separate",
                "match_method": "ambiguous_common_name_guard",
                "explanation": f"Single generic token '{tokens[0]}' held separate without corroborating full identity.",
            }

        # Generate mention context embedding if context is provided
        mention_embedding: Optional[List[float]] = None
        context_evaluated = False
        if context and context.strip():
            try:
                mention_embedding = generate_embedding(context.strip())
                context_evaluated = True
            except Exception as exc:
                logger.debug("Mention context embedding generation unavailable: %s", exc)

        # 1. Exact alias / canonical match (Strong match tier)
        if norm_name in self._alias_to_canonical:
            canonical, etype, context_desc = self._alias_to_canonical[norm_name]
            score = 0.98
            explanation = f"Exact match with canonical defense entity '{canonical}'."

            # Verify context if available
            if mention_embedding:
                can_vec = self._get_canonical_embedding(canonical, context_desc)
                if can_vec:
                    try:
                        ctx_sim = compute_cosine_similarity(mention_embedding, can_vec)
                        explanation += f" Context corroboration: {ctx_sim:.2f}."
                    except Exception as exc:
                        logger.debug("Context similarity computation error: %s", exc)

            return {
                "raw_name": raw_name,
                "canonical_name": canonical,
                "entity_type": etype,
                "confidence": score,
                "action": "auto_link",
                "decision": "auto_link",
                "match_method": "exact_defense_alias",
                "explanation": explanation,
            }

        # 2. Indic Romanization transliteration match
        if translit_name in self._translit_to_canonical:
            canonical, etype, context_desc = self._translit_to_canonical[translit_name]
            score = 0.92
            explanation = f"Transliteration variant match -> '{canonical}'."

            if mention_embedding:
                can_vec = self._get_canonical_embedding(canonical, context_desc)
                if can_vec:
                    try:
                        ctx_sim = compute_cosine_similarity(mention_embedding, can_vec)
                        score = min(0.96, score + (0.04 * ctx_sim))
                        explanation += f" Context cosine: {ctx_sim:.2f}."
                    except Exception:
                        pass

            return {
                "raw_name": raw_name,
                "canonical_name": canonical,
                "entity_type": etype,
                "confidence": round(score, 4),
                "action": "auto_link",
                "decision": "auto_link",
                "match_method": "indic_romanization_transliteration",
                "explanation": explanation,
            }

        # 3. Fuzzy match against known aliases with contextual embedding support
        best_canonical = clean_name or trimmed
        best_type = entity_type_hint or "UNKNOWN"
        best_desc = ""
        best_score = 0.0
        best_alias = ""

        for alias, (canonical, etype, desc) in self._alias_to_canonical.items():
            if entity_type_hint and etype != entity_type_hint:
                continue

            score = compute_string_similarity(norm_name, alias)
            # Token inclusion bonus
            if len(norm_name) > 3 and norm_name in alias:
                score = max(score, 0.85)

            if score > best_score:
                best_score = score
                best_canonical = canonical
                best_type = etype
                best_desc = desc
                best_alias = alias

        # Incorporate contextual similarity if mention embedding is available
        ctx_bonus = 0.0
        ctx_sim = 0.0
        if mention_embedding and best_desc:
            can_vec = self._get_canonical_embedding(best_canonical, best_desc)
            if can_vec:
                try:
                    ctx_sim = compute_cosine_similarity(mention_embedding, can_vec)
                    # Corroborate or penalize based on context
                    if ctx_sim >= 0.70 and best_score >= 0.75:
                        ctx_bonus = 0.08
                    elif ctx_sim < 0.35:
                        ctx_bonus = -0.15
                except Exception as exc:
                    logger.debug("Context similarity check failed: %s", exc)

        adjusted_score = round(min(1.0, max(0.0, best_score + ctx_bonus)), 4)

        # Conservative Decision Logic:
        # Strong match: >= 0.88 -> auto_link
        # Medium match: 0.65 to 0.87 -> review_queue
        # Weak match: < 0.65 -> separate
        if adjusted_score >= 0.88:
            action = "auto_link"
            method = "fuzzy_high_confidence"
            explanation = f"High similarity ({adjusted_score:.2f}) with alias '{best_alias}' -> '{best_canonical}'."
        elif adjusted_score >= 0.65:
            action = "review_queue"
            method = "fuzzy_medium_review"
            explanation = f"Moderate similarity ({adjusted_score:.2f}) with alias '{best_alias}'. Analyst review required."
        else:
            action = "separate"
            method = "unmatched_separate"
            best_canonical = clean_name or trimmed
            adjusted_score = 0.40
            explanation = f"No canonical defense entity match found (score {best_score:.2f}). Preserved as distinct entity."

        if context_evaluated:
            explanation += f" (Context cosine: {ctx_sim:.2f})"

        return {
            "raw_name": raw_name,
            "canonical_name": best_canonical,
            "entity_type": best_type,
            "confidence": adjusted_score,
            "action": action,
            "decision": action,
            "match_method": method,
            "explanation": explanation,
        }

    def run(
        self,
        input_data: Union[List[str], List[Dict[str, Any]], List[EntityOut]],
    ) -> Dict[str, Any]:
        """
        Execute entity resolution over a list of entity mentions or names.
        """
        if not isinstance(input_data, list):
            raise TypeError(f"ResolutionAgent expects list input, got {type(input_data).__name__}")

        resolved_list: List[Dict[str, Any]] = []

        for item in input_data:
            if isinstance(item, str):
                res = self.resolve_entity(item)
            elif isinstance(item, EntityOut):
                res = self.resolve_entity(item.entity_value, entity_type_hint=item.entity_type)
            elif isinstance(item, dict):
                raw_name = item.get("entity_value") or item.get("raw_name") or item.get("name") or ""
                etype = item.get("entity_type")
                context = item.get("context") or item.get("sentence")
                res = self.resolve_entity(str(raw_name), entity_type_hint=etype, context=context)
            else:
                logger.warning("Skipping unknown item type in entity resolution: %s", type(item))
                continue

            resolved_list.append(res)

        avg_conf = 1.0
        if resolved_list:
            avg_conf = round(sum(r["confidence"] for r in resolved_list) / len(resolved_list), 4)

        prov = Provenance(
            source_ids=[],
            method="defense_ontology_transliteration_and_contextual_resolution",
            model_version=f"{self.name}:{self.version}",
            confidence=avg_conf,
            claim_status=ClaimStatus.OFFICIAL_DESIGNATION,
            source_type=SourceType.PUBLIC,
        )

        return {
            "resolved_entities": resolved_list,
            "provenance": prov,
        }
