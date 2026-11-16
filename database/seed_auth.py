"""
Seed default users and workspaces for Stage 3 RBAC.
"""
from sqlalchemy import text
from common.db import get_db
from common.auth import get_password_hash
from common.audit import log_audit_event


DEFAULT_USERS = [
    {
        "email": "admin@raksha.ai",
        "full_name": "Major Gen. Jay (Admin)",
        "password": "Admin@Raksha2026",
        "role": "admin",
    },
    {
        "email": "analyst@raksha.ai",
        "full_name": "Lead Analyst Ary",
        "password": "Analyst@Raksha2026",
        "role": "analyst",
    },
    {
        "email": "viewer@raksha.ai",
        "full_name": "Observer Officer Jaish",
        "password": "Viewer@Raksha2026",
        "role": "viewer",
    },
]


def seed_auth():
    with get_db() as db:
        user_ids = {}
        for u in DEFAULT_USERS:
            pwd_hash = get_password_hash(u["password"])
            row = db.execute(
                text("""
                    INSERT INTO users (email, password_hash, full_name, role, is_active, created_at)
                    VALUES (:email, :pwd, :name, :role, TRUE, NOW())
                    ON CONFLICT (email) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        full_name = EXCLUDED.full_name,
                        role = EXCLUDED.role
                    RETURNING id
                """),
                {
                    "email": u["email"],
                    "pwd": pwd_hash,
                    "name": u["full_name"],
                    "role": u["role"],
                },
            ).fetchone()
            user_ids[u["email"]] = row[0]
            print(f"User seeded: {u['email']} (Role: {u['role']}, ID: {row[0]})")

        # Workspaces
        admin_id = user_ids["admin@raksha.ai"]
        analyst_id = user_ids["analyst@raksha.ai"]

        ws1 = db.execute(
            text("""
                INSERT INTO workspaces (name, description, owner_id, is_shared, created_at)
                SELECT 'National Strategic Command', 'Shared intelligence hub for cross-theatre defence correlation.', :owner_id, TRUE, NOW()
                WHERE NOT EXISTS (SELECT 1 FROM workspaces WHERE name = 'National Strategic Command')
                RETURNING id
            """),
            {"owner_id": admin_id},
        ).fetchone()

        ws2 = db.execute(
            text("""
                INSERT INTO workspaces (name, description, owner_id, is_shared, created_at)
                SELECT 'Northern Sector Investigation', 'Private workspace for Line-of-Control and Ladakh tactical threads.', :owner_id, FALSE, NOW()
                WHERE NOT EXISTS (SELECT 1 FROM workspaces WHERE name = 'Northern Sector Investigation')
                RETURNING id
            """),
            {"owner_id": analyst_id},
        ).fetchone()

        db.commit()
        log_audit_event(
            db,
            action="system.seed_auth",
            entity_type="system",
            details={"seeded_users": list(user_ids.keys())},
        )
        print("Auth seeding completed successfully.")


if __name__ == "__main__":
    seed_auth()
