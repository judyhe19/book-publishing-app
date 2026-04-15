# Booksite Backup Admin Guide

This document explains how to:
- Set up the backup system from scratch
- Run and verify backups
- Restore from any backup snapshot
- Validate backups

This guide assumes:
- One **production VM** (runs app + DB)
- One **backup VM** (stores backups via restic)
- Docker Compose is used for deployment

---

# Overview

Backup system design:
- Push-based backups from production → backup VM
- Uses:
  - PostgreSQL dump (`pg_dump`)
  - Static files archive (cover images, logo images)
  - restic for versioned storage + retention
- Retention policy:
  - 7 daily
  - 4 weekly
  - 12 monthly
- Alerts via Discord webhook

---

# 1. Initial Setup

## 1.1 Create Backup VM + User

On backup VM:

```bash
sudo adduser --disabled-password --gecos "" backupuser
```

Create directories:

```bash
sudo mkdir -p /srv/restic/booksite-repo
sudo mkdir -p /srv/restic/incoming

sudo chown -R backupuser:backupuser /srv/restic
sudo chmod 700 /srv/restic/booksite-repo
sudo chmod 700 /srv/restic/incoming
```

## 1.2 Install restic

```bash
sudo apt update
sudo apt install -y restic
```

## 1.3 Configure restic password

```bash
sudo -u backupuser bash -c 'umask 077 && cat > /home/backupuser/.restic-pass'
```

Set password: example

```bash
sudo chmod 600 /home/backupuser/.restic-pass
```

## 1.4 Initialize Backup Repository

```bash
sudo -u backupuser restic \
  --repo /srv/restic/booksite-repo \
  --password-file /home/backupuser/.restic-pass \
  init
```

# 2. SSH Setup (Production -> Backup)

On production VM:

```bash
sudo mkdir -p /srv/booksite/book_ssh
chmod 700 /srv/booksite/book_ssh

ssh-keygen -t ed25519 \
  -f /srv/booksite/book_ssh/backup_vcm_ed25519 \
  -N ""

sudo chown -R rlt42:rlt42 /srv/booksite
```

Copy public key to backup VM:

```bash
sudo -u backupuser mkdir -p /home/backupuser/.ssh
sudo -u backupuser chmod 700 /home/backupuser/.ssh

sudo -u backupuser bash -c 'cat >> /home/backupuser/.ssh/authorized_keys'
sudo chmod 600 /home/backupuser/.ssh/authorized_keys
```

# 3. Backup Script Setup (Production VM)

## 3.1 Create config file

```bash
sudo mkdir -p /opt/booksite-backup
sudo chmod 700 /opt/booksite-backup

sudo nano /opt/booksite-backup/backup.env
```

A backup env example has been provided [.env.backup.example](../backups/.env.backup.example)

```bash
sudo chmod 600 /opt/booksite-backup/backup.env
```

## 3.2 Backup script

Create:


```bash
sudo nano /opt/booksite-backup/backup.sh
```

Use the script [provided](../backups/backup.sh.reference)

```bash
sudo chmod 700 /opt/booksite-backup/backup.sh
```

## 3.3 Test by running manually

```bash
sudo /opt/booksite-backup/backup.sh
```

# 4. Scheduling (Daily Backups)

```bash
sudo nano /etc/systemd/system/booksite-backup.service
```

```ini
[Unit]
Description=Booksite backup job
After=docker.service network-online.target

[Service]
Type=oneshot
ExecStart=/opt/booksite-backup/backup.sh
```

Create timer:

```bash
sudo nano /etc/systemd/system/booksite-backup.timer
```

```ini
[Unit]
Description=Run Booksite backup daily

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now booksite-backup.timer
```

Check:

```bash
systemctl list-timers | grep booksite-backup
```



