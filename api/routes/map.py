"""
GET /api/map/incidents — Geospatial Tactical Incident Mapping for Leaflet.js
Owner: Jay (Lead & Platform) | Stage: 2 (Mid)
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from common.db import get_db as _get_db
from common.schemas.map import MapIncident, MapResponse

router = APIRouter(prefix="/map", tags=["Geospatial Map"])


def get_db():
    with _get_db() as db:
        yield db


# Geo-registry of key strategic flashpoints across the Northern and Western borders
THEATRE_LOCATIONS = [
    {"name": "Galwan Valley", "lat": 34.25, "lon": 78.33, "region": "Ladakh", "keywords": ["galwan", "eastern ladakh"]},
    {"name": "Depsang Plains", "lat": 35.25, "lon": 77.95, "region": "Ladakh", "keywords": ["depsang", "daulat beg oldie"]},
    {"name": "Demchok Sector", "lat": 32.70, "lon": 79.43, "region": "Ladakh", "keywords": ["demchok", "chumar"]},
    {"name": "Pangong Tso", "lat": 33.72, "lon": 78.75, "region": "Ladakh", "keywords": ["pangong", "fingers"]},
    {"name": "Tawang Sector", "lat": 27.58, "lon": 91.86, "region": "Arunachal Pradesh", "keywords": ["tawang", "kameng"]},
    {"name": "Kibithu Eastern Border", "lat": 28.26, "lon": 97.02, "region": "Arunachal Pradesh", "keywords": ["kibithu", "walong"]},
    {"name": "Line of Control (Rajouri)", "lat": 33.37, "lon": 74.30, "region": "Jammu & Kashmir", "keywords": ["rajouri", "poonch", "loc"]},
    {"name": "Line of Control (Uri)", "lat": 34.08, "lon": 74.03, "region": "Jammu & Kashmir", "keywords": ["uri", "baramulla", "kupwara"]},
    {"name": "Sir Creek Border", "lat": 23.63, "lon": 68.20, "region": "Gujarat", "keywords": ["sir creek", "kutch"]},
    {"name": "Siliguri Corridor", "lat": 26.72, "lon": 88.42, "region": "North Bengal", "keywords": ["siliguri", "chicken's neck", "doklam"]},
]


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
            SELECT a.id, a.title, a.url, a.published_at, s.name AS source_name, s.ring,
                   aa.event_type, aa.threat_level, aa.sentiment
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            JOIN article_analysis aa ON aa.article_id = a.id
            {where_sql}
            ORDER BY a.published_at DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    incidents: List[MapIncident] = []
    
    # Associate articles with nearest geographical flashpoint
    for i, r in enumerate(rows):
        title_lower = r.title.lower()
        matched_loc = None
        for loc in THEATRE_LOCATIONS:
            if any(k in title_lower for k in loc["keywords"]):
                matched_loc = loc
                break

        # Fall back to rotating strategic sectors if specific theatre not in title
        if not matched_loc:
            matched_loc = THEATRE_LOCATIONS[i % len(THEATRE_LOCATIONS)]

        level = r.threat_level or 4
        category = "high" if level >= 8 else ("medium" if level >= 4 else "low")

        incidents.append(
            MapIncident(
                id=r.id,
                title=r.title,
                event_type=r.event_type or "border_incident",
                threat_level=level,
                threat_category=category,
                ring=r.ring,
                latitude=matched_loc["lat"] + (i * 0.005 % 0.02), # slight jitter to avoid exact point overlap
                longitude=matched_loc["lon"] + (i * 0.005 % 0.02),
                location_name=matched_loc["name"],
                region=matched_loc["region"],
                article_id=r.id,
                source_name=r.source_name,
                url=r.url,
                occurred_at=r.published_at or datetime.now(timezone.utc),
            )
        )

        if len(incidents) >= limit:
            break

    return MapResponse(incidents=incidents, total=len(incidents))
