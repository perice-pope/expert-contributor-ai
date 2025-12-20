#!/bin/bash
# Broken MySQL backup script - contains multiple bugs
# DO NOT FIX THIS - only solution/solve.sh should fix it

set -euo pipefail

LOG_FILE="/var/log/mysql_backup.log"
BACKUP_DIR="/backups/mysql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting MySQL backup..."

# Bug 1: Missing MySQL lock - should use FLUSH TABLES WITH READ LOCK
# Bug 2: No lock maintenance mechanism

# Bug 3: Wrong snapshot command - missing size specification
lvcreate -s -n mysql_snapshot /dev/vg_mysql/lv_mysql_data

# Bug 4: Missing mount point creation check
mount /dev/vg_mysql/mysql_snapshot /mnt/mysql_snapshot

# Bug 5: Wrong source path - should be from snapshot, not original
rsync -av /var/lib/mysql/ "$BACKUP_PATH/"

# Bug 6: Missing retention policy - no cleanup of old backups

# Bug 7: Unmount before releasing lock (order is wrong)
umount /mnt/mysql_snapshot
lvremove -y /dev/vg_mysql/mysql_snapshot

# Bug 8: No MySQL unlock command

log "Backup completed: $BACKUP_PATH"

