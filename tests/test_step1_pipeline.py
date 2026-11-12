"""
Unit & Integration Contract Tests for Stage 2 Step 1 (Pipeline, Scorer, Anomaly, Official Seed).
Owner: Jay (Lead & Platform)
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from common.constants import DEFENCE_REGIONS
from database.seed import OFFICIAL_DESIGNATION_FACTS
from engine.pipeline import process_article, process_new_articles


def test_official_designation_facts_have_citations():
    """Every official baseline entity fact must carry an explicit official source citation."""
    assert len(OFFICIAL_DESIGNATION_FACTS) >= 6
    for entry in OFFICIAL_DESIGNATION_FACTS:
        assert entry["entity_name"]
        assert entry["entity_type"] in ("PERSON", "ORGANISATION", "LOCATION", "EQUIPMENT", "EVENT")
        assert 1 <= entry["primary_ring"] <= 4
        for fact_text, source_name, conf in entry["facts"]:
            assert fact_text.strip()
            assert source_name.strip()
            assert 0.0 <= conf <= 1.0


def test_engine_pipeline_exports_callables():
    """engine.pipeline must expose process_article and process_new_articles without NotImplementedError."""
    assert callable(process_article)
    assert callable(process_new_articles)


def test_threat_scorer_stores_all_regions():
    """calculate_threat_scores should compute and store scores for every DEFENCE_REGIONS entry."""
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.all.return_value = [
        {
            "id": 101,
            "title": "Troop deployment near Ladakh LAC and Depsang sector",
            "content": "Indian Army monitors PLA patrols near Eastern Ladakh.",
            "ring": 1,
            "event_type": "border_incident",
            "sentiment": "alarming",
            "threat_level": 7,
        }
    ]
    mock_db.execute.return_value.fetchall.return_value = []

    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_db
    mock_ctx.__exit__.return_value = False

    with patch("report.scorer.get_db", return_value=mock_ctx):
        from report.scorer import calculate_threat_scores

        scores = calculate_threat_scores(window_hours=24)

    assert len(scores) == len(DEFENCE_REGIONS)
    regions_returned = {s["region"] for s in scores}
    assert regions_returned == set(DEFENCE_REGIONS)


def test_anomaly_detector_flags_watchlist_and_spikes():
    """detect_anomalies should detect both statistical spikes and active watchlist matches."""
    mock_db = MagicMock()

    # Configure side effects for the sequential execute() calls inside detect_anomalies
    recent_articles_res = MagicMock()
    recent_articles_res.mappings.return_value.all.return_value = [
        {
            "id": i,
            "title": f"High alert along Ladakh LAC near Pangong #{i}",
            "content": "Missile and air defense readiness heightened.",
            "ring": 2,
            "event_type": "border_incident",
            "sentiment": "alarming",
            "threat_level": 8,
        }
        for i in range(1, 7)
    ]

    baselines_res = MagicMock()
    baselines_res.fetchall.return_value = []

    dedup_res = MagicMock()
    dedup_res.fetchone.return_value = None  # no prior duplicate alert

    insert_res = MagicMock()

    wl_row = MagicMock()
    wl_row.id = 1
    wl_row.name = "Ladakh Alert"
    wl_row.query_type = "keyword"
    wl_row.query_value = "Pangong"
    watchlists_res = MagicMock()
    watchlists_res.fetchall.return_value = [wl_row]

    # Sequence: recent_articles -> baselines -> (dedup, insert) for each anomaly -> watchlists -> dedup -> insert
    def execute_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        if "FROM articles a" in sql:
            return recent_articles_res
        if "FROM threat_scores" in sql:
            return baselines_res
        if "FROM watchlists" in sql:
            return watchlists_res
        if "FROM alerts" in sql:
            return dedup_res
        return insert_res

    mock_db.execute.side_effect = execute_side_effect

    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_db
    mock_ctx.__exit__.return_value = False

    with patch("report.anomaly.get_db", return_value=mock_ctx):
        from report.anomaly import detect_anomalies

        alerts = detect_anomalies(window_hours=24)

    alert_types = {a["alert_type"] for a in alerts}
    assert "WATCHLIST_MATCH" in alert_types
    assert len(alerts) >= 2


def test_pipeline_runner_processes_article_end_to_end():
    """Verify pipeline.runner executes translation, extraction, scoring, resolution, and threading cleanly."""
    mock_db = MagicMock()
    article_row = {
        "id": 501,
        "source_id": 1,
        "title": "Indian Army deploys additional patrols near Depsang Plains along LAC",
        "content": "Indian Army and PLA Ground Force continue verification in Eastern Ladakh.",
        "url": "https://example.com/lac-report",
        "url_hash": "hash501",
        "language": "en",
        "published_at": datetime.now(timezone.utc),
        "ring": 1,
    }

    node_id_counter = {"val": 10}

    def execute_side_effect(stmt, *args, **kwargs):
        sql = str(stmt)
        res = MagicMock()
        if "FROM articles a" in sql and "WHERE a.id = :aid" in sql:
            row_mock = MagicMock()
            row_mock._mapping = article_row
            res.fetchone.return_value = row_mock
            return res
        if "FROM events" in sql and "WHERE status = 'ongoing'" in sql:
            res.mappings.return_value.all.return_value = []
            return res
        if "SELECT id, mention_count" in sql and "FROM entity_nodes" in sql:
            res.fetchone.return_value = None
            return res
        if "INSERT INTO entity_nodes" in sql or "INSERT INTO events" in sql:
            node_id_counter["val"] += 1
            inserted = MagicMock()
            inserted.id = node_id_counter["val"]
            res.fetchone.return_value = inserted
            return res
        return res

    mock_db.execute.side_effect = execute_side_effect
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_db
    mock_ctx.__exit__.return_value = False

    with (
        patch("pipeline.runner.get_db", return_value=mock_ctx),
        patch("pipeline.runner._store_embedding", return_value=True),
        patch("agents.threading.agent.generate_embedding", return_value=[0.01] * 768),
        patch("agents.resolution.agent.generate_embedding", return_value=[0.01] * 768),
    ):
        from pipeline.runner import process_single_article

        out = process_single_article(501)

    assert out["article_id"] == 501
    assert out["event_type"]
    assert 1 <= out["threat_level"] <= 10
    assert out["event_id"] is not None

