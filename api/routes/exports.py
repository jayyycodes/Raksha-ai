"""
Export API Routes for SitReps, Entity Profiles, and Intelligence Dossiers (Stage 3 Solid - Milestone M9b).
Owner: Jaish (Data Expansion, Intelligence & Grounding)

Supports multi-format exports:
- CSV: standard RFC 4180 format for analytical tools
- JSON: structured schema for external think-tank interoperability
- PDF/HTML: formatted printable brief for defence command circulation
"""
import csv
import io
import json
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import text

from common.db import get_db as _get_db
from api.routes.sitrep import get_sitrep_by_date, get_latest_sitrep

router = APIRouter(prefix="/exports", tags=["Exports"])


def get_db():
    with _get_db() as db:
        yield db


@router.get("/sitrep/{report_date}")
@router.get("/sitrep/today")
def export_sitrep(
    report_date: Optional[str] = None,
    format: str = Query("json", pattern="^(json|csv|html)$"),
    db=Depends(get_db),
):
    """
    Export Situation Report in JSON, CSV, or formatted HTML/PDF.
    """
    if not report_date or report_date in ("today", "latest"):
        sitrep_data = get_latest_sitrep(db)
        target_date = sitrep_data.get("report_date", date.today().isoformat())
    else:
        sitrep_data = get_sitrep_by_date(report_date, db)
        target_date = report_date

    if format == "json":
        return sitrep_data

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Header info
        writer.writerow(["RAKSHA AI - NATIONAL SECURITY SITUATION REPORT (SITREP)"])
        writer.writerow(["Date", target_date])
        writer.writerow(["Status", sitrep_data.get("status", "draft")])
        writer.writerow(["Approved By", sitrep_data.get("approved_by", "Unapproved")])
        writer.writerow([])

        # Executive Summary
        writer.writerow(["EXECUTIVE SUMMARY"])
        writer.writerow([sitrep_data.get("executive_summary", "")])
        writer.writerow([])

        # Regional Threat Assessments
        writer.writerow(["REGIONAL THEATRE ASSESSMENTS"])
        writer.writerow(["Theatre", "Status", "Threat Level", "Operational Summary"])
        for t in sitrep_data.get("theatre_assessments", []):
            writer.writerow([t.get("theatre"), t.get("status"), t.get("threat_level"), t.get("summary")])
        writer.writerow([])

        # Top Threats
        writer.writerow(["TOP THREAT VECTORS"])
        writer.writerow(["Theatre", "Score", "Trend", "Primary Concern"])
        for th in sitrep_data.get("top_threats", []):
            writer.writerow([th.get("theatre"), th.get("score"), th.get("trend"), th.get("primary_concern")])
        writer.writerow([])

        # Citations
        writer.writerow(["CITATIONS & ATTRIBUTIONS"])
        writer.writerow(["Citation ID", "Article ID", "Source Name", "Ring", "Threat Level", "Headline"])
        for c in sitrep_data.get("citations", []):
            writer.writerow([
                c.get("citation_id"),
                c.get("article_id"),
                c.get("source_name"),
                c.get("ring"),
                c.get("threat_level"),
                c.get("title"),
            ])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="sitrep_{target_date}.csv"'},
        )

    elif format == "html":
        # Formatted printable briefing document
        theatres_html = "".join(
            f"""
            <div style="margin-bottom: 12px; border-left: 3px solid #1E293B; padding-left: 8px;">
                <strong>{t.get('theatre')}</strong> [Threat Level: {t.get('threat_level')}/10]<br/>
                <span style="font-size: 11px; color: #475569;">STATUS: {t.get('status')}</span>
                <p style="font-size: 13px; margin: 4px 0;">{t.get('summary')}</p>
            </div>
            """
            for t in sitrep_data.get("theatre_assessments", [])
        )

        citations_html = "".join(
            f"<li><strong>{c.get('citation_id')}</strong> [{c.get('source_name')} - Ring {c.get('ring')}]: {c.get('title')}</li>"
            for c in sitrep_data.get("citations", [])
        )

        html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SitRep - {target_date}</title>
            <style>
                body {{ font-family: 'Times New Roman', serif; padding: 40px; color: #0F172A; max-width: 800px; margin: auto; }}
                h1 {{ font-size: 22px; border-bottom: 2px solid #0F172A; padding-bottom: 8px; }}
                .meta {{ font-size: 12px; color: #64748B; margin-bottom: 20px; }}
                .box {{ background: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 6px; margin-bottom: 20px; }}
                h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.05em; color: #334155; margin-top: 24px; }}
            </style>
        </head>
        <body>
            <h1>RAKSHA AI — NATIONAL SECURITY SITUATION REPORT</h1>
            <div class="meta">
                Date: {target_date} &bull; Status: {sitrep_data.get('status', 'draft').upper()} &bull;
                Verified by: {sitrep_data.get('approved_by') or 'Intelligence Analyst Desk'}
            </div>
            <div class="box">
                <strong>Executive Summary:</strong>
                <p style="font-size: 14px; line-height: 1.5;">{sitrep_data.get('executive_summary')}</p>
            </div>
            <h2>Regional Operational Theatres</h2>
            {theatres_html}
            <h2>Attributed Source Citations</h2>
            <ol style="font-size: 12px; line-height: 1.6;">
                {citations_html}
            </ol>
            <div style="margin-top: 40px; border-top: 1px solid #E2E8F0; font-size: 10px; color: #94A3B8; text-align: center;">
                CONFIDENTIAL &bull; OPEN-SOURCE INTELLIGENCE WORKBENCH &bull; RAKSHA AI
            </div>
        </body>
        </html>
        """
        return Response(
            content=html_doc,
            media_type="text/html",
            headers={"Content-Disposition": f'inline; filename="sitrep_{target_date}.html"'},
        )


@router.get("/profile/{profile_id}")
def export_entity_profile(
    profile_id: int,
    format: str = Query("json", pattern="^(json|csv)$"),
    db=Depends(get_db),
):
    """
    Export an entity profile dossier in JSON or CSV format.
    """
    node = db.execute(
        text("SELECT * FROM entity_nodes WHERE id = :id"),
        {"id": profile_id},
    ).fetchone()

    if not node:
        raise HTTPException(status_code=404, detail="Entity profile not found")

    node_dict = dict(node._mapping)

    # Fetch associated facts
    facts = db.execute(
        text("SELECT * FROM entity_facts WHERE entity_id = :id"),
        {"id": profile_id},
    ).fetchall()

    facts_list = [dict(f._mapping) for f in facts]

    if format == "json":
        return {
            "entity": node_dict,
            "facts": facts_list,
        }
    else:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ENTITY PROFILE DOSSIER"])
        writer.writerow(["ID", node_dict.get("id")])
        writer.writerow(["Name", node_dict.get("canonical_name")])
        writer.writerow(["Type", node_dict.get("entity_type")])
        writer.writerow(["Primary Ring", node_dict.get("primary_ring")])
        writer.writerow([])
        writer.writerow(["FACTS & ATTRIBUTED CLAIMS"])
        writer.writerow(["Fact ID", "Statement", "Source Citation", "Confidence", "Claim Status"])
        for f in facts_list:
            writer.writerow([
                f.get("id"),
                f.get("fact_text"),
                f.get("source_citation"),
                f.get("confidence"),
                f.get("claim_status"),
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="entity_{profile_id}.csv"'},
        )
