"""
GET /api/map/incidents — Geospatial Tactical Incident Mapping for Leaflet.js
4-Ring Global Strategic Gazetteer with Event and Entity Lineage Links.
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.schemas.map import MapIncident, MapResponse

router = APIRouter(prefix="/map", tags=["Geospatial Map"])


def get_db():
    with _get_db() as db:
        yield db


# Comprehensive 4-Ring Global Strategic Gazetteer (50+ Locations)
GLOBAL_GAZETTEER = [
    # ── Ring 1: Northern & Western Strategic Borders ─────────────
    {"name": "Galwan Valley", "lat": 34.25, "lon": 78.33, "region": "Eastern Ladakh", "ring": 1, "keywords": ["galwan", "eastern ladakh"]},
    {"name": "Depsang Plains", "lat": 35.25, "lon": 77.95, "region": "Eastern Ladakh", "ring": 1, "keywords": ["depsang", "daulat beg oldie", "dbo"]},
    {"name": "Demchok Sector", "lat": 32.70, "lon": 79.43, "region": "Eastern Ladakh", "ring": 1, "keywords": ["demchok", "chumar", "indus valley"]},
    {"name": "Pangong Tso", "lat": 33.72, "lon": 78.75, "region": "Eastern Ladakh", "ring": 1, "keywords": ["pangong", "fingers area", "spanggur"]},
    {"name": "Tawang Sector", "lat": 27.58, "lon": 91.86, "region": "Arunachal Pradesh", "ring": 1, "keywords": ["tawang", "kameng", "bum la"]},
    {"name": "Kibithu Frontier", "lat": 28.26, "lon": 97.02, "region": "Arunachal Pradesh", "ring": 1, "keywords": ["kibithu", "walong", "anjaw"]},
    {"name": "Line of Control (Rajouri-Poonch)", "lat": 33.37, "lon": 74.30, "region": "Jammu & Kashmir", "ring": 1, "keywords": ["rajouri", "poonch", "loc", "mendir"]},
    {"name": "Line of Control (Uri-Baramulla)", "lat": 34.08, "lon": 74.03, "region": "Jammu & Kashmir", "ring": 1, "keywords": ["uri", "baramulla", "kupwara", "keran", "tithwal"]},
    {"name": "Sir Creek Border", "lat": 23.63, "lon": 68.20, "region": "Gujarat", "ring": 1, "keywords": ["sir creek", "kutch", "rann of kutch", "bhuj"]},
    {"name": "Siliguri Corridor", "lat": 26.72, "lon": 88.42, "region": "North Bengal", "ring": 1, "keywords": ["siliguri", "chicken's neck", "hasimara"]},
    
    # ── Ring 1: National Centres & Command Headquarters ─────────
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "region": "Telangana", "ring": 1, "keywords": ["hyderabad", "secunderabad", "telangana", "andhra", "obc"]},
    {"name": "New Delhi (HQ)", "lat": 28.6139, "lon": 77.2090, "region": "National Capital", "ring": 1, "keywords": ["new delhi", "delhi", "south block", "mod", "pmo", "parliament", "congress", "bjp", "nda"]},
    {"name": "Mumbai (Western Naval Cmd)", "lat": 18.9220, "lon": 72.8347, "region": "Maharashtra", "ring": 1, "keywords": ["mumbai", "bombay", "western naval"]},
    {"name": "Bengaluru (Defence R&D)", "lat": 12.9716, "lon": 77.5946, "region": "Karnataka", "ring": 1, "keywords": ["bengaluru", "bangalore", "isro", "hal", "drdo"]},
    {"name": "Kolkata (Eastern Army Cmd)", "lat": 22.5726, "lon": 88.3639, "region": "West Bengal", "ring": 1, "keywords": ["kolkata", "calcutta", "fort william", "eastern command"]},
    {"name": "Visakhapatnam (Eastern Naval Cmd)", "lat": 17.6868, "lon": 83.2185, "region": "Andhra Coast", "ring": 1, "keywords": ["visakhapatnam", "vizag", "eastern naval command"]},
    {"name": "Port Blair (ANC Joint Cmd)", "lat": 11.6234, "lon": 92.7265, "region": "Andaman & Nicobar", "ring": 1, "keywords": ["port blair", "andaman", "nicobar"]},
    {"name": "Jaipur (South Western Cmd)", "lat": 26.9124, "lon": 75.7873, "region": "Rajasthan", "ring": 1, "keywords": ["jaipur", "rajasthan", "lok mandhan"]},
    
    # ── Ring 2: Primary Adversaries (Pakistan & China) ───────────
    {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479, "region": "Pakistan", "ring": 2, "keywords": ["islamabad", "pakistan government", "shehbaz", "sharif"]},
    {"name": "Rawalpindi (GHQ)", "lat": 33.5984, "lon": 73.0441, "region": "Pakistan", "ring": 2, "keywords": ["rawalpindi", "ghq", "pakistan army", "dg ispr", "asim munir"]},
    {"name": "Gwadar Port", "lat": 25.1264, "lon": 62.3225, "region": "Balochistan, Pakistan", "ring": 2, "keywords": ["gwadar", "cpec", "balochistan", "makran"]},
    {"name": "Lahore Sector", "lat": 31.5204, "lon": 74.3587, "region": "Punjab, Pakistan", "ring": 2, "keywords": ["lahore", "punjab pakistan", "wagah"]},
    {"name": "Karachi Naval Hub", "lat": 24.8607, "lon": 67.0011, "region": "Sindh, Pakistan", "ring": 2, "keywords": ["karachi", "pns", "sindh", "maritime pakistan"]},
    {"name": "Muzaffarabad", "lat": 34.3700, "lon": 73.4711, "region": "PoK", "ring": 2, "keywords": ["muzaffarabad", "pok", "azad kashmir", "neelum"]},
    {"name": "Beijing (CMC & PLA HQ)", "lat": 39.9042, "lon": 116.4074, "region": "China", "ring": 2, "keywords": ["beijing", "central military commission", "pla", "china", "xi jinping", "ministry of national defense"]},
    {"name": "Chengdu (Western Theater Cmd)", "lat": 30.5728, "lon": 104.0668, "region": "Sichuan, China", "ring": 2, "keywords": ["chengdu", "western theater command", "wtc", "sichuan"]},
    {"name": "Lhasa Military District", "lat": 29.6525, "lon": 91.1721, "region": "Tibet, China", "ring": 2, "keywords": ["lhasa", "tibet", "tibet military district", "shigatse"]},
    {"name": "Hotan Airbase", "lat": 37.1123, "lon": 79.9304, "region": "Xinjiang, China", "ring": 2, "keywords": ["hotan", "hetian", "xinjiang", "kashgar", "tarim"]},
    {"name": "Yulin Naval Base (Hainan)", "lat": 18.2200, "lon": 109.5200, "region": "South China Sea", "ring": 2, "keywords": ["hainan", "yulin", "sanya", "submarine base", "aircraft carrier"]},
    
    # ── Ring 3: Regional Periphery ───────────────────────────────
    {"name": "Kathmandu", "lat": 27.7172, "lon": 85.3240, "region": "Nepal", "ring": 3, "keywords": ["nepal", "kathmandu", "tihar", "laxmi puja", "nea", "oli", "himalayan"]},
    {"name": "Dhaka", "lat": 23.8103, "lon": 90.4125, "region": "Bangladesh", "ring": 3, "keywords": ["dhaka", "bangladesh", "hasina", "yunus", "biman"]},
    {"name": "Chittagong Port", "lat": 22.3569, "lon": 91.7832, "region": "Bangladesh", "ring": 3, "keywords": ["chittagong", "cox's bazar", "bay of bengal", "matarbari"]},
    {"name": "Colombo", "lat": 6.9271, "lon": 79.8612, "region": "Sri Lanka", "ring": 3, "keywords": ["colombo", "sri lanka", "dissanayake", "wickremesinghe"]},
    {"name": "Hambantota Port", "lat": 6.1246, "lon": 81.1185, "region": "Southern Sri Lanka", "ring": 3, "keywords": ["hambantota", "sri lanka port"]},
    {"name": "Kabul", "lat": 34.5553, "lon": 69.2075, "region": "Afghanistan", "ring": 3, "keywords": ["kabul", "afghanistan", "taliban", "tolo", "kandahar"]},
    {"name": "Naypyidaw", "lat": 19.7633, "lon": 96.0785, "region": "Myanmar", "ring": 3, "keywords": ["naypyidaw", "myanmar", "burma", "junta", "yangon", "sittwe"]},
    {"name": "Male", "lat": 4.1755, "lon": 73.5093, "region": "Maldives", "ring": 3, "keywords": ["maldives", "male", "muizzu"]},
    {"name": "Thimphu", "lat": 27.4728, "lon": 89.6393, "region": "Bhutan", "ring": 3, "keywords": ["thimphu", "bhutan", "doklam", "paro"]},
    
    # ── Ring 4: Strategic Maritime Chokepoints & Global Powers ───
    {"name": "Strait of Malacca", "lat": 2.5000, "lon": 101.5000, "region": "Maritime Chokepoint", "ring": 4, "keywords": ["malacca", "singapore strait", "sumatra", "chokepoint"]},
    {"name": "Bab-el-Mandeb", "lat": 12.5800, "lon": 43.3300, "region": "Red Sea / Gulf of Aden", "ring": 4, "keywords": ["bab-el-mandeb", "red sea", "houthi", "gulf of aden", "yemen"]},
    {"name": "Strait of Hormuz", "lat": 26.5667, "lon": 56.2500, "region": "Persian Gulf", "ring": 4, "keywords": ["hormuz", "persian gulf", "oman", "uae"]},
    {"name": "Diego Garcia", "lat": -7.3195, "lon": 72.4228, "region": "Central Indian Ocean", "ring": 4, "keywords": ["diego garcia", "chagos", "us naval base", "bomber base"]},
    {"name": "South China Sea", "lat": 12.0000, "lon": 114.0000, "region": "Indo-Pacific", "ring": 4, "keywords": ["south china sea", "spratly", "paracel", "nine-dash"]},
    {"name": "Taipei", "lat": 25.0330, "lon": 121.5654, "region": "Taiwan Strait", "ring": 4, "keywords": ["taiwan", "taipei", "taiwan strait", "pla air defense"]},
    {"name": "Washington D.C.", "lat": 38.9072, "lon": -77.0369, "region": "United States", "ring": 4, "keywords": ["washington", "pentagon", "white house", "united states", "us navy", "state department"]},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173, "region": "Russia", "ring": 4, "keywords": ["moscow", "kremlin", "russia", "putin", "s-400"]},
    {"name": "Tehran", "lat": 35.6892, "lon": 51.3890, "region": "Iran", "ring": 4, "keywords": ["tehran", "iran", "irgc"]},
]


def _match_gazetteer(title: str, content: str, source_country: Optional[str], ring: int) -> dict:
    """Accurately match article to 4-Ring Global Gazetteer with fallback based on country/ring."""
    search_text = f"{title} {content[:400]}".lower()

    # 1. Exact keyword match across gazetteer
    for loc in GLOBAL_GAZETTEER:
        if any(k in search_text for k in loc["keywords"]):
            return loc

    # 2. Regional/Country fallback to avoid misattributing domestic/regional news to the wrong border
    c_lower = (source_country or "").lower()
    if "pakistan" in c_lower or ring == 2:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Islamabad"), GLOBAL_GAZETTEER[18])
    if "china" in c_lower:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Beijing (CMC & PLA HQ)"), GLOBAL_GAZETTEER[24])
    if "nepal" in c_lower or ring == 3:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Kathmandu"), GLOBAL_GAZETTEER[29])
    if "bangladesh" in c_lower:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Dhaka"), GLOBAL_GAZETTEER[30])
    if "sri lanka" in c_lower:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Colombo"), GLOBAL_GAZETTEER[32])
    if "afghanistan" in c_lower:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Kabul"), GLOBAL_GAZETTEER[34])
    if "myanmar" in c_lower:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Naypyidaw"), GLOBAL_GAZETTEER[35])
    if ring == 4:
        return next((l for l in GLOBAL_GAZETTEER if l["name"] == "Strait of Malacca"), GLOBAL_GAZETTEER[38])

    # Default Indian Command HQ for Ring 1 articles
    return next((l for l in GLOBAL_GAZETTEER if l["name"] == "New Delhi (HQ)"), GLOBAL_GAZETTEER[11])


@router.get("/incidents", response_model=MapResponse)
@router.get("", response_model=MapResponse)
def get_map_incidents(
    ring: Optional[int] = Query(None, ge=1, le=4, description="Filter by source ring"),
    threat_level_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum threat score"),
    limit: int = Query(50, ge=5, le=200),
    db=Depends(get_db),
):
    """
    Returns geo-located tactical incidents with coordinates, severity, and canonical links.
    Used by Leaflet.js map with custom ring markers and threat color-coding.
    """
    # Normalize query params when invoked directly in tests
    if not isinstance(ring, int):
        ring = None
    if not isinstance(threat_level_min, int):
        threat_level_min = None
    if not isinstance(limit, int):
        limit = 50

    where_clauses = ["a.is_processed = TRUE"]
    params: dict = {"limit": limit * 2}

    if ring is not None:
        where_clauses.append("s.ring = :ring")
        params["ring"] = ring
    if threat_level_min is not None:
        where_clauses.append("aa.threat_level >= :threat_level_min")
        params["threat_level_min"] = threat_level_min

    where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = db.execute(
        text(f"""
            SELECT a.id, a.title, a.content, a.url, a.published_at,
                   s.name AS source_name, s.ring, s.country AS source_country,
                   aa.event_type, aa.threat_level, aa.sentiment, aa.summary,
                   ev.id AS event_id, ev.title AS event_title
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            JOIN article_analysis aa ON aa.article_id = a.id
            LEFT JOIN event_articles ea ON ea.article_id = a.id
            LEFT JOIN events ev ON ev.id = ea.event_id
            {where_sql}
            ORDER BY a.published_at DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    if not rows:
        return MapResponse(incidents=[], total=0)

    article_ids = [r.id for r in rows]

    # Fetch related entities for these articles
    entities_by_article: Dict[int, List[dict]] = {}
    if article_ids:
        ent_rows = db.execute(
            text("""
                SELECT e.article_id, en.id AS entity_id, en.name, en.entity_type
                FROM entities e
                JOIN entity_nodes en ON en.name = e.entity_value
                WHERE e.article_id = ANY(:aids)
                LIMIT 200
            """),
            {"aids": article_ids},
        ).fetchall()
        for er in ent_rows:
            entities_by_article.setdefault(er.article_id, []).append({
                "id": er.entity_id,
                "name": er.name,
                "type": er.entity_type,
            })

    incidents: List[MapIncident] = []

    for i, r in enumerate(rows):
        matched_loc = _match_gazetteer(
            title=r.title or "",
            content=r.content or "",
            source_country=r.source_country,
            ring=r.ring,
        )

        level = r.threat_level or 4
        category = "high" if level >= 8 else ("medium" if level >= 4 else "low")

        # Subtle offset for visual clarity when multiple incidents cluster on the same hub
        jitter_lat = ((i % 5) - 2) * 0.03
        jitter_lon = (((i * 3) % 5) - 2) * 0.03

        incidents.append(
            MapIncident(
                id=r.id,
                title=r.title,
                event_type=r.event_type or "border_incident",
                threat_level=level,
                threat_category=category,
                ring=r.ring,
                latitude=matched_loc["lat"] + jitter_lat,
                longitude=matched_loc["lon"] + jitter_lon,
                location_name=matched_loc["name"],
                region=matched_loc["region"],
                article_id=r.id,
                source_name=r.source_name,
                url=r.url,
                summary=r.summary or (r.content[:200] if r.content else None),
                event_id=r.event_id,
                event_title=r.event_title,
                related_entities=entities_by_article.get(r.id, []),
                occurred_at=r.published_at or datetime.now(timezone.utc),
            )
        )

        if len(incidents) >= limit:
            break

    return MapResponse(incidents=incidents, total=len(incidents))
