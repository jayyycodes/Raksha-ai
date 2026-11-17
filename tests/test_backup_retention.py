"""
Tests for Database Backup & Retention Policies
Ref: docs/raksha-ai-proposal.md Section 11 & Section 17, Risk #24
"""
import gzip
import json
from pathlib import Path
from scripts.backup_db import (
    run_database_backup,
    rotate_old_backups,
    enforce_upload_retention,
    BACKUP_DIR,
)


def test_database_backup_generation():
    backup_path = run_database_backup()
    assert backup_path.exists()
    assert backup_path.name.endswith(".json.gz")
    assert backup_path.stat().st_size > 0

    # Verify content integrity
    with gzip.open(backup_path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert "created_at" in data
    assert "tables" in data
    assert "sources" in data["tables"]
    assert "audit_log" in data["tables"]


def test_rotate_and_retention_routines():
    # Should run without error
    rotate_old_backups()
    enforce_upload_retention()
