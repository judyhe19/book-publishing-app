# Booksite Restore & Backup Validation Guide

This document explains:
- How to restore the system from any backup snapshot
- How to verify that a backup is valid

Assumptions:
- Backup VM stores restic repo
- Production VM runs Docker Compose app
- SSH key already configured

# Restore Process

## 1. Select a backup

Run on backup VM:

```bash
restic --repo /srv/restic/booksite-repo snapshots
```

You will need to input the restic password that you configured

Pick a snapshot ID (or use "latest")

## 2. Verify backup integrity 

Run on the backup VM to ensure the backup data is not corrupted:

```bash
restic --repo /srv/restic/booksite-repo check
```

## 3. Restore snapshot to backup VM

First clear backup directory:

```bash
rm -rf /tmp/restore
```

Restore snapshot:

```bash
restic \
  --repo /srv/restic/booksite-repo \
  --password-file /home/backupuser/.restic-pass \
  restore <SNAPSHOT_ID_OR_latest> \
  --target /tmp/restore
```

Expected output structure:
- /tmp/restore/.../backup_<timestamp>/db.sql
- /tmp/restore/.../backup_<timestamp>/covers.tar.gz
- /tmp/restore/.../backup_<timestamp>/metadata.json


## 4. Copy backup to production VM

It is strongly recommended to first perform this restore on a test environment to verify that the selected backup is correct and up to date. Proceed on production only after validation, or continue at your own risk.


Run on production VM:

```bash
scp -i /srv/booksite/book_ssh/backup_vcm_ed25519 -r \
  backupuser@vcm-52662.vm.duke.edu:/tmp/restore/srv/restic/incoming/backup_* \
  /tmp/restore
```

## 5. Stop Application

```bash
cd /home/rlt42/book-app-deployment
docker compose down
```

## 6. Restore database

Start DB:

```bash
docker compose up -d db
sleep 5
```

Drop + recreate DB:

```bash
docker compose exec -T db psql -U judy -d postgres \
  -c 'DROP DATABASE IF EXISTS "book-app";'

docker compose exec -T db psql -U judy -d postgres \
  -c 'CREATE DATABASE "book-app";'
```

Load data:

```bash
cat /tmp/restore/db.sql | \
  docker compose exec -T db psql -U judy -d "book-app"
```

## 7. Restore static files (covers)

Start backend:

```bash
docker compose up -d backend
sleep 5
```

Get container:

```bash
BACKEND_CONTAINER=$(docker compose ps -q backend)
```

Clear existing files:

```bash
docker exec "$BACKEND_CONTAINER" mkdir -p /app/static/img/covers
docker exec "$BACKEND_CONTAINER" sh -c 'rm -rf /app/static/img/covers/*'
```

Extract + copy:

```bash
mkdir -p /tmp/covers-restore
tar -xzf /tmp/restore/covers.tar.gz -C /tmp/covers-restore

docker cp /tmp/covers-restore/. \
  "$BACKEND_CONTAINER":/app/static/img/covers/
```

## 8. Restart application

```bash
docker compose up -d
```

Clear sessions:

```bash
docker compose exec -T db psql -U judy -d "book-app" \
  -c 'TRUNCATE TABLE django_session;'

docker compose restart backend frontend
```

# Backup Validation (Required)

A backup is only valid if it can be restored and used.

## Quick validation (recommended)

After restore:

- App loads successfully
- No DB errors in logs
- Data appears in UI
- Cover images load correctly

## Full validation (best practice)

Perform restore into a temporary environment:

- Use a separate VM or temp directory
- Run same restore steps
- Start app
- Verify:
  - DB integrity (tables populated)
  - Images exist
  - No crashes

## Manual integrity checks

After restore:

Check DB tables:

```bash
docker compose exec -T db psql -U judy -d "book-app" -c '\dt'
```

Check row counts:

```bash
docker compose exec -T db psql -U judy -d "book-app" -c 'SELECT COUNT(*) FROM book;'
```

Check files:

```bash
docker exec "$BACKEND_CONTAINER" ls /app/static/img/covers
```

## Optional: restic integrity check

Run on backup VM:

```bash
restic --repo /srv/restic/booksite-repo check
```

# Notes

- Restore overwrites ALL production data
- Always verify snapshot before restoring
- Do not restore while app is running
- Covers + DB must both be restored for consistency

# End
