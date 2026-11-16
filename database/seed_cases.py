"""
Seed initial investigation cases and evidence for Stage 3 M9b.
"""
from sqlalchemy import text
from common.db import get_db
from common.audit import log_audit_event


def seed_cases():
    with get_db() as db:
        # Get analyst user ID
        analyst = db.execute(text("SELECT id FROM users WHERE role = 'analyst' LIMIT 1")).fetchone()
        analyst_id = analyst[0] if analyst else 1

        ws = db.execute(text("SELECT id FROM workspaces WHERE is_shared = TRUE LIMIT 1")).fetchone()
        ws_id = ws[0] if ws else 1

        # Check if already seeded
        existing = db.execute(text("SELECT COUNT(*) FROM cases")).scalar() or 0
        if existing > 0:
            print(f"Cases already seeded ({existing} cases exist).")
            return

        # Case 1
        c1 = db.execute(
            text("""
                INSERT INTO cases (title, description, status, priority, classification, lead_analyst_id, workspace_id, tags, created_at, updated_at)
                VALUES (
                    'Eastern Ladakh Disengagement & Buffer Zone Monitoring',
                    'Tracking military disengagement and verification patrolling protocols across Depsang Plains and Demchok sectors following diplomatic bilateral accord.',
                    'active', 'high', 'restricted', :analyst_id, :ws_id,
                    ARRAY['LAC', 'Ladakh', 'Depsang', 'Disengagement', 'PLA'],
                    NOW() - INTERVAL '3 days', NOW()
                ) RETURNING id
            """),
            {"analyst_id": analyst_id, "ws_id": ws_id},
        ).fetchone()[0]

        # Case 1 Items
        # Find 2 relevant articles
        articles = db.execute(text("SELECT id, title FROM articles WHERE title ILIKE '%ladakh%' OR title ILIKE '%china%' LIMIT 2")).fetchall()
        for a in articles:
            db.execute(
                text("""
                    INSERT INTO case_items (case_id, item_type, item_id, title, analyst_notes, added_by, added_at)
                    VALUES (:cid, 'article', :aid, :title, 'Corroborates tactical troop repositioning in northern sector.', :uid, NOW())
                """),
                {"cid": c1, "aid": str(a.id), "title": a.title, "uid": analyst_id},
            )

        db.execute(
            text("""
                INSERT INTO case_notes (case_id, analyst_id, note_text, hypothesis, created_at)
                VALUES (:cid, :uid, 'Buffer zone patrolling protocols verified in Depsang. Mutual liaison officers conducted hotline check at Chushul-Moldo.', 'Status-quo stabilization holding; tactical air reconnaissance should continue on weekly cycle.', NOW() - INTERVAL '1 day')
            """),
            {"cid": c1, "uid": analyst_id},
        )

        # Case 2
        c2 = db.execute(
            text("""
                INSERT INTO cases (title, description, status, priority, classification, lead_analyst_id, workspace_id, tags, created_at, updated_at)
                VALUES (
                    'Gwadar Port Maritime Infrastructure & Dual-Use Activity',
                    'Observation of high-tonnage docking operations, submarine presence indicators, and naval intelligence facilities in Balochistan coastline.',
                    'active', 'critical', 'confidential', :analyst_id, :ws_id,
                    ARRAY['Gwadar', 'PLAN', 'Pakistan Navy', 'IOR', 'CPEC'],
                    NOW() - INTERVAL '7 days', NOW()
                ) RETURNING id
            """),
            {"analyst_id": analyst_id, "ws_id": ws_id},
        ).fetchone()[0]

        # Case 3
        c3 = db.execute(
            text("""
                INSERT INTO cases (title, description, status, priority, classification, lead_analyst_id, workspace_id, tags, created_at, updated_at)
                VALUES (
                    'Cross-Border Tunneling & Counter-Infiltration Probing',
                    'Tracking kinetic encounters and ground surveillance radar triggers along Pir Panjal and Jammu international border sector.',
                    'in_review', 'medium', 'restricted', :analyst_id, :ws_id,
                    ARRAY['LoC', 'Jammu', 'Infiltration', 'Internal-Security'],
                    NOW() - INTERVAL '10 days', NOW()
                ) RETURNING id
            """),
            {"analyst_id": analyst_id, "ws_id": ws_id},
        ).fetchone()[0]

        db.commit()
        log_audit_event(
            db,
            action="case.seed_initial",
            user_id=analyst_id,
            entity_type="case",
            entity_id=str(c1),
            details={"seeded_cases": [c1, c2, c3]},
        )
        print(f"Cases seeded successfully: IDs [{c1}, {c2}, {c3}]")


if __name__ == "__main__":
    seed_cases()
