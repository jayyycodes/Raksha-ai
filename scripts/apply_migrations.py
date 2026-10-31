"""
Apply all SQL migration files from database/migrations/ in order.
Usage:
    python -m scripts.apply_migrations
    py scripts\apply_migrations.py
"""
import sys
from pathlib import Path

# Ensure the project root is on the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.db import engine  # noqa: E402

MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"


def apply_migration(sql_path: Path) -> None:
    print(f"Applying migration: {sql_path.name} ...", end=" ")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql_path.read_text(encoding="utf-8"))
    print("✅ done")


if __name__ == "__main__":
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        sys.exit(0)

    for sql_file in migration_files:
        apply_migration(sql_file)

    print(f"\n✅ All {len(migration_files)} migration(s) applied.")
