"""
Unit & Integration Tests for Safe Upload Parsers & Exports (Stage 3 Solid - Milestones M9b & M9c).
Owner: Jaish (Data Expansion, Intelligence & Grounding)
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from pipeline.upload_parsers import SafeUploadParser, UploadParserError
from api.main import app


def test_csv_parser_with_automatic_headers():
    """CSV parser detects column names dynamically and extracts valid articles."""
    parser = SafeUploadParser()
    csv_content = """title,content,source,date
Border Security Update,Patrols report peaceful sector status along northern border,Northern Command,2026-11-16
Naval Drill,Joint offshore exercises conducted in Arabian Sea,Western Naval Command,2026-11-15
"""
    articles = parser.parse_csv(csv_content.encode("utf-8"), "intel_brief.csv")
    assert len(articles) == 2
    assert articles[0].title == "Border Security Update"
    assert articles[0].source_name == "Northern Command"
    assert articles[0].source_type == "user_upload"
    assert articles[1].title == "Naval Drill"


def test_txt_parser_splits_sections():
    """TXT parser splits distinct narrative blocks and assigns provenance."""
    parser = SafeUploadParser()
    txt_content = """SITUATION REPORT: NORTHERN FRONTIER
Aerial surveillance indicates regular logistics patrol along the high-altitude observation line.
Troop garrisons report zero unauthorized airspace crossings.

WESTERN SECTOR RADAR SURVEILLANCE
Forward air defense radar suites remain active in sector 4.
Counter-measures telemetry reports normal ambient RF spectrum.
"""
    articles = parser.parse_txt(txt_content.encode("utf-8"), "frontline.txt")
    assert len(articles) == 2
    assert "NORTHERN FRONTIER" in articles[0].title
    assert "RADAR SURVEILLANCE" in articles[1].title
    assert articles[0].source_type == "user_upload"


def test_pdf_parser_extracts_pages():
    """PDF parser extracts pages into indexed articles and enforces limits."""
    parser = SafeUploadParser()

    # Generate a lightweight in-memory PDF using pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    pdf_bytes = io.BytesIO()
    writer.write(pdf_bytes)

    # Empty/blank page returns 0 articles (content < 30 chars)
    articles = parser.parse_pdf(pdf_bytes.getvalue(), "blank.pdf")
    assert len(articles) == 0


def test_upload_parser_enforces_size_limit():
    """Files exceeding 15MB are rejected before parsing."""
    parser = SafeUploadParser()
    oversized = b"0" * (16 * 1024 * 1024)
    with pytest.raises(UploadParserError, match="exceeds the 15 MB limit"):
        parser.parse_file(oversized, "giant.csv")


def test_export_sitrep_json_and_csv():
    """SitRep export endpoint serves structured JSON and RFC 4180 CSV."""
    client = TestClient(app)

    mock_sitrep = {
        "report_date": "2026-11-16",
        "status": "approved",
        "approved_by": "Lead Analyst",
        "executive_summary": "Frontier security operations stable.",
        "theatre_assessments": [
            {"theatre": "Northern Sector", "status": "Vigilance", "threat_level": 5, "summary": "Normal patrols."}
        ],
        "top_threats": [
            {"theatre": "Northern Sector", "score": 5.0, "trend": "stable", "primary_concern": "Weather"}
        ],
        "citations": [
            {"citation_id": "[1]", "article_id": 101, "source_name": "PIB", "ring": 1, "threat_level": 5, "title": "Patrol Update"}
        ],
    }

    with patch("api.routes.exports.get_latest_sitrep", return_value=mock_sitrep):
        # Test JSON export
        res_json = client.get("/api/exports/sitrep/today?format=json")
        assert res_json.status_code == 200
        assert "executive_summary" in res_json.json()

        # Test CSV export
        res_csv = client.get("/api/exports/sitrep/today?format=csv")
        assert res_csv.status_code == 200
        assert res_csv.headers["content-type"].startswith("text/csv")
        assert "NATIONAL SECURITY SITUATION REPORT" in res_csv.text

        # Test HTML/PDF export
        res_html = client.get("/api/exports/sitrep/today?format=html")
        assert res_html.status_code == 200
        assert res_html.headers["content-type"].startswith("text/html")
        assert "RAKSHA AI" in res_html.text


def test_upload_api_parse_endpoint():
    """POST /api/uploads/parse parses multi-format files safely."""
    client = TestClient(app)

    csv_data = b"headline,text\nTest Headline,Sample operational intelligence text for analyst workspace."
    files = {"file": ("desk_intel.csv", csv_data, "text/csv")}
    res = client.post("/api/uploads/parse", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_parsed"] == 1
    assert data["articles"][0]["title"] == "Test Headline"
