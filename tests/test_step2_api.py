"""
Unit & Contract Tests for Stage 2 Step 2 Backend APIs
(Events, Threats, Alerts, Watchlists, Expanded Search, Profile Merge/Split/Notes).
Owner: Jay (Lead & Platform)
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.main import app
from api.routes.alerts import get_db as alerts_get_db
from api.routes.events import get_db as events_get_db
from api.routes.profiles import get_db as profiles_get_db
from api.routes.search import get_db as search_get_db
from api.routes.threats import get_db as threats_get_db
from api.routes.watchlists import get_db as watchlists_get_db


def _override_db(mock_db):
    def _dep():
        yield mock_db
    return _dep


def test_events_list_and_detail():
    mock_db = MagicMock()
    ev_row = SimpleNamespace(
        id=1,
        title="Ladakh Depsang Verification Patrols",
        region="LAC-Ladakh",
        event_type="border_incident",
        status="ongoing",
        threat_level=6.0,
        first_seen_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        article_count=3,
        summary="Coordinated observation across Depsang sector.",
    )
    art_row = SimpleNamespace(
        id=10,
        title="Patrol verification proceeds along LAC",
        url="https://example.com/10",
        published_at=datetime.now(timezone.utc),
        source_name="The Hindu",
        ring=1,
        threat_level=6,
        sentiment="neutral",
        linked_at=datetime.now(timezone.utc),
        link_method="embedding_cosine_and_entities",
        confidence=0.89,
        is_seed=True,
        explanation="Semantic cosine 0.89; shared entity Indian Army.",
    )
    ent_row = SimpleNamespace(
        entity_type="ORGANISATION",
        entity_value="Indian Army",
        mentions=3,
        profile_id=1,
    )

    def exec_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        res = MagicMock()
        if "FROM events e" in sql:
            res.fetchall.return_value = [ev_row]
        elif "FROM events" in sql and "WHERE id = :eid" in sql:
            res.fetchone.return_value = ev_row
        elif "FROM event_articles ea" in sql:
            res.fetchall.return_value = [art_row]
        elif "FROM entities e" in sql:
            res.fetchall.return_value = [ent_row]
        return res

    mock_db.execute.side_effect = exec_side_effect
    app.dependency_overrides[events_get_db] = _override_db(mock_db)
    try:
        client = TestClient(app)
        res_list = client.get("/api/events")
        assert res_list.status_code == 200
        assert res_list.json()["total"] == 1
        assert res_list.json()["events"][0]["region"] == "LAC-Ladakh"

        res_detail = client.get("/api/events/1")
        assert res_detail.status_code == 200
        body = res_detail.json()
        assert body["event"]["id"] == 1
        assert len(body["timeline"]) == 1
        assert body["timeline"][0]["link_method"] == "embedding_cosine_and_entities"
        assert body["entities"][0]["name"] == "Indian Army"
    finally:
        app.dependency_overrides.clear()


def test_threats_and_30_day_history():
    mock_db = MagicMock()
    threat_row = SimpleNamespace(
        id=1,
        region="LAC-Ladakh",
        score=5.8,
        trend="rising",
        article_count=7,
        calculated_at=datetime.now(timezone.utc),
    )
    hist_row = SimpleNamespace(
        day=datetime.now(timezone.utc).date(),
        score=5.8,
        article_count=7,
        trend="rising",
    )

    def exec_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        res = MagicMock()
        if "DISTINCT ON (region)" in sql:
            res.fetchall.return_value = [threat_row]
        elif "WHERE LOWER(region)" in sql:
            res.fetchall.return_value = [hist_row]
        else:
            res.fetchall.return_value = []
        return res

    mock_db.execute.side_effect = exec_side_effect
    app.dependency_overrides[threats_get_db] = _override_db(mock_db)
    try:
        client = TestClient(app)
        res = client.get("/api/threats")
        assert res.status_code == 200
        assert res.json()["regions"][0]["region"] == "LAC-Ladakh"

        res_hist = client.get("/api/threats/LAC-Ladakh")
        assert res_hist.status_code == 200
        assert res_hist.json()["region"] == "LAC-Ladakh"
        assert res_hist.json()["total_points"] == 1
    finally:
        app.dependency_overrides.clear()


def test_alerts_and_watchlists():
    mock_db = MagicMock()
    alert_row = SimpleNamespace(
        id=5,
        alert_type="WATCHLIST_MATCH",
        region="LAC-Ladakh",
        description="Watchlist triggered",
        severity="high",
        is_read=False,
        triggered_at=datetime.now(timezone.utc),
        watchlist_id=1,
        source_article_ids=[12],
    )
    wl_row = SimpleNamespace(
        id=1,
        name="Ladakh Watch",
        query_type="keyword",
        query_value="Depsang",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        alert_count=1,
        last_triggered_at=datetime.now(timezone.utc),
    )

    def exec_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        res = MagicMock()
        if "COUNT(*) FROM alerts" in sql:
            res.scalar.return_value = 1
        elif "FROM alerts" in sql:
            res.fetchall.return_value = [alert_row]
        elif "UPDATE alerts SET is_read = TRUE" in sql:
            res.fetchone.return_value = SimpleNamespace(id=5, is_read=True)
        elif "FROM watchlists w" in sql:
            res.fetchall.return_value = [wl_row]
        elif "FROM articles a" in sql:
            res.fetchall.return_value = []
        return res

    mock_db.execute.side_effect = exec_side_effect
    app.dependency_overrides[alerts_get_db] = _override_db(mock_db)
    app.dependency_overrides[watchlists_get_db] = _override_db(mock_db)
    try:
        client = TestClient(app)
        res_alerts = client.get("/api/alerts")
        assert res_alerts.status_code == 200
        assert res_alerts.json()["unread_count"] == 1

        res_read = client.post("/api/alerts/5/read")
        assert res_read.status_code == 200
        assert res_read.json()["is_read"] is True

        res_wl = client.get("/api/watchlists")
        assert res_wl.status_code == 200
        assert res_wl.json()["watchlists"][0]["query_value"] == "Depsang"
    finally:
        app.dependency_overrides.clear()


def test_unified_search_includes_events():
    mock_db = MagicMock()
    evt_row = SimpleNamespace(
        id=2,
        title="Ladakh LAC Disengagement",
        region="LAC-Ladakh",
        event_type="border_incident",
        status="ongoing",
        threat_level=6.0,
        article_count=4,
        last_updated_at=datetime.now(timezone.utc),
    )

    def exec_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        res = MagicMock()
        if "FROM events" in sql:
            res.fetchall.return_value = [evt_row]
        else:
            res.fetchall.return_value = []
        return res

    mock_db.execute.side_effect = exec_side_effect
    app.dependency_overrides[search_get_db] = _override_db(mock_db)
    try:
        client = TestClient(app)
        res = client.get("/api/search?q=Ladakh")
        assert res.status_code == 200
        data = res.json()
        assert data["total_matches"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Ladakh LAC Disengagement"
    finally:
        app.dependency_overrides.clear()


def test_profile_merge_split_and_notes():
    mock_db = MagicMock()
    target_node = SimpleNamespace(
        id=1,
        name="Indian Army",
        entity_type="ORGANISATION",
        primary_ring=1,
        aliases=["IA"],
        mention_count=10,
        metadata={"analyst_notes": []},
    )
    source_node = SimpleNamespace(
        id=99,
        name="IA Ground Command",
        entity_type="ORGANISATION",
        primary_ring=1,
        aliases=["IA Command"],
        mention_count=2,
    )

    def exec_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        params = args[0] if args else kwargs
        res = MagicMock()
        if "SELECT id, name, aliases, mention_count FROM entity_nodes" in sql:
            nid = params.get("id") if isinstance(params, dict) else 1
            res.fetchone.return_value = target_node if nid == 1 else source_node
        elif "SELECT id, name, entity_type, primary_ring, aliases FROM entity_nodes" in sql:
            res.fetchone.return_value = SimpleNamespace(
                id=1, name="Indian Army", entity_type="ORGANISATION", primary_ring=1, aliases=["IA", "IA Ground Command"]
            )
        elif "INSERT INTO entity_nodes" in sql:
            res.fetchone.return_value = SimpleNamespace(id=99)
        elif "SELECT metadata FROM entity_nodes" in sql:
            res.fetchone.return_value = target_node
        return res

    mock_db.execute.side_effect = exec_side_effect
    app.dependency_overrides[profiles_get_db] = _override_db(mock_db)
    try:
        client = TestClient(app)
        res_merge = client.post("/api/profiles/1/merge", json={"source_node_id": 99, "analyst_name": "jay"})
        assert res_merge.status_code == 200
        assert res_merge.json()["merged"] is True
        assert "IA Ground Command" in res_merge.json()["aliases"]

        res_split = client.post("/api/profiles/1/split", json={"alias_to_split": "IA Ground Command", "analyst_name": "jay"})
        assert res_split.status_code == 200
        assert res_split.json()["split"] is True
        assert "IA Ground Command" not in res_split.json()["remaining_aliases"]

        res_note = client.post("/api/profiles/1/notes", json={"note": "Cross-check northern corridor patrol schedule", "analyst_name": "jay"})
        assert res_note.status_code == 200
        assert res_note.json()["note"]["note"] == "Cross-check northern corridor patrol schedule"
    finally:
        app.dependency_overrides.clear()

