# Raksha AI — Database Backup, Retention & Disaster Recovery Procedure
**Owner:** Jay (Platform & Engineering Lead)  
**Classification:** PUBLIC // OPEN SOURCE INTELLIGENCE PLATFORM  
**Reference:** [docs/raksha-ai-proposal.md](file:///c:/Development/raksha-ai/docs/raksha-ai-proposal.md) (Section 11 & Section 17, Risk #24)

---

### 1. Overview
Raksha AI implements automated snapshotting, backup rotation, and data retention policies to guarantee zero data loss and compliance with defence-grade operational standards.

### 2. Automated Daily Snapshotting
The backup utility ([scripts/backup_db.py](file:///c:/Development/raksha-ai/scripts/backup_db.py)) creates compressed Gzip archives containing the complete state of the PostgreSQL database:
- Monitored sources & active articles
- Entity Knowledge Graph (nodes & links)
- Threaded Events & Timeline records
- Weighted Regional Threat indices
- User profiles & role-based permissions (`admin`, `analyst`, `viewer`)
- Append-only immutable `audit_log`
- Cases & Dossier investigation items
- User upload metadata & DPDP Act correction requests

#### Running a Manual Backup
```bash
python -m scripts.backup_db
```
The snapshot is saved to `data/backups/raksha_backup_<YYYYMMDD_HHMMSS>.json.gz`.

---

### 3. Backup Retention & Rotation Policy
- **Database Snapshots:** Daily snapshots are rotated automatically. The system retains the last **7 days** of daily snapshots, purging older archives to conserve disk resources.
- **Sandboxed Uploads Retention:** Temporary and unprocessed sandboxed files older than **30 days** are purged automatically unless pinned to an active Case investigation.

---

### 4. Disaster Recovery & Restoration Procedure
To restore the platform from an existing backup snapshot:
```bash
python -c "
from pathlib import Path
from scripts.backup_db import restore_backup
restore_backup(Path('data/backups/raksha_backup_<filename>.json.gz'))
"
```
Once restored, apply any pending migrations:
```bash
python -m scripts.apply_migrations
```
And verify system health:
```bash
pytest tests/ -v
```
