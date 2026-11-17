"""
Database Backup, Retention & Disaster Recovery Script — Raksha AI Stage 3 Solid
Owner: Jay (Platform & Engineering Lead)
Ref: docs/raksha-ai-proposal.md (Section 11 & Section 17, Risk #24)

Capabilities:
1. Automated PostgreSQL schema & table dump to compressed SQL/JSON archive.
2. Backup rotation policy (retains last 7 days of daily snapshots, purges older).
3. Data retention enforcement for sandboxed upload files older than 30 days.
4. Documented disaster recovery restore function.
"""
import os
import sys
import json
import gzip
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.db import get_db
from common.logger import get_logger

logger = get_logger(__name__)

BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
BACKUP_RETENTION_DAYS = 7
UPLOAD_RETENTION_DAYS = 30


def run_database_backup() -> Path:
    """Export snapshot of critical intelligence tables into timestamped gzip archive."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"raksha_backup_{timestamp}.json.gz"

    tables = [
        "sources",
        "articles",
        "entity_nodes",
        "entity_links",
        "events",
        "threat_scores",
        "sitreps",
        "users",
        "workspaces",
        "audit_log",
        "cases",
        "case_items",
        "case_notes",
        "uploads",
        "correction_requests",
    ]

    snapshot = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tables": {},
    }

    with get_db() as db:
        for t in tables:
            try:
                rows = db.execute(text(f"SELECT * FROM {t}")).fetchall()
                snapshot["tables"][t] = [dict(r._mapping) for r in rows]
                # Serialize datetimes and non-serializable objects to ISO strings
                for row in snapshot["tables"][t]:
                    for k, v in row.items():
                        if isinstance(v, (datetime,)):
                            row[k] = v.isoformat()
                        elif isinstance(v, bytes):
                            row[k] = v.hex()
            except Exception as e:
                logger.warning(f"Skipping table '{t}' in backup: {e}")

    # Write compressed archive
    with gzip.open(backup_file, "wt", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, default=str)

    size_kb = backup_file.stat().st_size / 1024
    logger.info(f"Database backup created: {backup_file.name} ({size_kb:.1f} KB)")
    print(f"✅ Database backup created: {backup_file.name} ({size_kb:.1f} KB)")
    return backup_file


def rotate_old_backups():
    """Remove backup archives older than BACKUP_RETENTION_DAYS."""
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=BACKUP_RETENTION_DAYS)
    purged = 0

    for f in BACKUP_DIR.glob("raksha_backup_*.json.gz"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            f.unlink()
            purged += 1

    if purged:
        logger.info(f"Purged {purged} backup snapshots older than {BACKUP_RETENTION_DAYS} days")
        print(f"🧹 Purged {purged} old backup snapshots (> {BACKUP_RETENTION_DAYS} days)")


def enforce_upload_retention():
    """Purge sandboxed files and temporary upload artifacts older than UPLOAD_RETENTION_DAYS."""
    upload_root = PROJECT_ROOT / "data" / "uploads" / "sandboxed"
    if not upload_root.exists():
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=UPLOAD_RETENTION_DAYS)
    purged_files = 0

    for f in upload_root.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                f.unlink()
                purged_files += 1

    if purged_files:
        logger.info(f"Enforced upload retention: deleted {purged_files} files older than {UPLOAD_RETENTION_DAYS} days")
        print(f"🧹 Enforced upload retention: purged {purged_files} files (> {UPLOAD_RETENTION_DAYS} days)")


def restore_backup(backup_path: Path):
    """Restore database state from a compressed backup archive."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    print(f"Restoring database from {backup_path.name} ...")
    with gzip.open(backup_path, "rt", encoding="utf-8") as f:
        snapshot = json.load(f)

    with get_db() as db:
        for t, rows in snapshot.get("tables", {}).items():
            if not rows:
                continue
            cols = list(rows[0].keys())
            cols_str = ", ".join(cols)
            vals_str = ", ".join([f":{c}" for c in cols])
            insert_sql = f"INSERT INTO {t} ({cols_str}) VALUES ({vals_str}) ON CONFLICT DO NOTHING"
            
            for r in rows:
                try:
                    db.execute(text(insert_sql), r)
                except Exception as e:
                    logger.debug(f"Row restore warning in {t}: {e}")
        db.commit()

    print("✅ Database restore completed.")


if __name__ == "__main__":
    b_file = run_database_backup()
    rotate_old_backups()
    enforce_upload_retention()
