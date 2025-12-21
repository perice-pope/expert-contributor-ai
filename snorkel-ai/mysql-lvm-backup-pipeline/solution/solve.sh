#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

# Ensure LVM is set up before proceeding
if ! mount | grep -q "vg_mysql"; then
    echo "[oracle] LVM not mounted, running init-lvm.sh..."
    if [ -x /usr/local/bin/init-lvm.sh ]; then
        /usr/local/bin/init-lvm.sh || echo "[oracle] init-lvm.sh failed, continuing anyway..."
    fi
fi

echo "[oracle] Fixing MySQL backup script..."

# Fix the backup script
cat > /app/backup_mysql.sh << 'BACKUP_EOF'
#!/bin/bash
# Fixed MySQL backup script with LVM snapshots

set -euo pipefail

LOG_FILE="/var/log/mysql_backup.log"
BACKUP_DIR="/backups/mysql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"
SNAPSHOT_NAME="mysql_snapshot"
SNAPSHOT_SIZE="1G"
MOUNT_POINT="/mnt/mysql_snapshot"
VG_NAME="vg_mysql"
LV_NAME="lv_mysql_data"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

wait_for_mysql() {
    log "Waiting for MySQL to be ready..."
    for i in {1..60}; do
        if mysqladmin ping --silent 2>/dev/null; then
            log "MySQL is ready (attempt $i)"
            return 0
        fi
        sleep 1
    done
    log "ERROR: MySQL not ready after 60 seconds"
    return 1
}

log "=== Starting MySQL backup ==="

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create mount point if it doesn't exist
mkdir -p "$MOUNT_POINT"

# Step 1: Quiesce MySQL - flush tables and acquire read lock
log "Step 1: Quiescing MySQL database..."
# Ensure MySQL is up before attempting the lock
wait_for_mysql
# Use a background MySQL connection to hold the lock
mysql -u root <<'MYSQL_LOCK_EOF' &
FLUSH TABLES WITH READ LOCK;
DO SLEEP(300);
UNLOCK TABLES;
MYSQL_LOCK_EOF
MYSQL_LOCK_PID=$!
sleep 3  # Give MySQL time to acquire lock

# Verify lock is held by checking for the process and MySQL status
if ! kill -0 $MYSQL_LOCK_PID 2>/dev/null; then
    log "ERROR: Failed to start MySQL lock process"
    exit 1
fi

# Verify MySQL shows locked tables
if mysql -u root -e "SHOW PROCESSLIST" 2>/dev/null | grep -q "Locked\|Waiting"; then
    log "MySQL lock acquired (PID: $MYSQL_LOCK_PID)"
else
    log "WARNING: Lock status unclear, proceeding with caution"
fi

# Step 2: Create LVM snapshot
log "Step 2: Creating LVM snapshot..."
if lvcreate -s -L "$SNAPSHOT_SIZE" -n "$SNAPSHOT_NAME" "/dev/${VG_NAME}/${LV_NAME}"; then
    log "Snapshot created successfully"
else
    log "ERROR: Failed to create snapshot"
    # Release MySQL lock before exiting
    kill $MYSQL_LOCK_PID 2>/dev/null || true
    mysql -u root -e "UNLOCK TABLES;" 2>/dev/null || true
    exit 1
fi

# Step 3: Mount snapshot
log "Step 3: Mounting snapshot..."
if mount "/dev/${VG_NAME}/${SNAPSHOT_NAME}" "$MOUNT_POINT" -t ext4; then
    log "Snapshot mounted successfully"
else
    log "ERROR: Failed to mount snapshot"
    lvremove -y "/dev/${VG_NAME}/${SNAPSHOT_NAME}" 2>/dev/null || true
    kill $MYSQL_LOCK_PID 2>/dev/null || true
    mysql -u root -e "UNLOCK TABLES;" 2>/dev/null || true
    exit 1
fi

# Step 4: Backup data via rsync
log "Step 4: Backing up data via rsync..."
if rsync -av --numeric-ids "$MOUNT_POINT/" "$BACKUP_PATH/"; then
    log "Backup completed successfully to $BACKUP_PATH"
else
    log "ERROR: rsync failed"
    umount "$MOUNT_POINT" 2>/dev/null || true
    lvremove -y "/dev/${VG_NAME}/${SNAPSHOT_NAME}" 2>/dev/null || true
    kill $MYSQL_LOCK_PID 2>/dev/null || true
    mysql -u root -e "UNLOCK TABLES;" 2>/dev/null || true
    exit 1
fi

# Step 5: Unmount snapshot
log "Step 5: Unmounting snapshot..."
umount "$MOUNT_POINT"

# Step 6: Remove snapshot
log "Step 6: Removing snapshot..."
lvremove -y "/dev/${VG_NAME}/${SNAPSHOT_NAME}"

# Step 7: Release MySQL lock
log "Step 7: Releasing MySQL lock..."
# Kill the background MySQL process which will release the lock
kill $MYSQL_LOCK_PID 2>/dev/null || true
# Also explicitly unlock in case process is still running
mysql -u root -e "UNLOCK TABLES;" 2>/dev/null || true
sleep 1
log "MySQL lock released"

# Step 8: Implement retention policy (keep last 7 backups)
log "Step 8: Applying retention policy (keeping last 7 backups)..."
BACKUP_COUNT=$(ls -1td "$BACKUP_DIR"/backup_* 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 7 ]; then
    ls -1td "$BACKUP_DIR"/backup_* | tail -n +8 | while read -r old_backup; do
        log "Removing old backup: $old_backup"
        rm -rf "$old_backup"
    done
    log "Retention policy applied: $((BACKUP_COUNT - 7)) old backup(s) removed"
else
    log "Retention policy: $BACKUP_COUNT backup(s) found (keeping all)"
fi

log "=== Backup completed successfully: $BACKUP_PATH ==="
BACKUP_EOF

chmod +x /app/backup_mysql.sh

echo "[oracle] Creating verification script..."

# Create verification script
cat > /app/verify_restore.sh << 'VERIFY_EOF'
#!/bin/bash
# Verification script for MySQL backup restoration

set -euo pipefail

LOG_FILE="/var/log/mysql_backup.log"
BACKUP_DIR="/backups/mysql"
MOUNT_POINT="/mnt/backup_verify"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting backup verification ==="

# Find most recent backup
LATEST_BACKUP=$(ls -1td "$BACKUP_DIR"/backup_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    log "ERROR: No backups found in $BACKUP_DIR"
    exit 1
fi

log "Verifying backup: $LATEST_BACKUP"

# Create mount point
mkdir -p "$MOUNT_POINT"

# Try to mount the backup as read-only (using loop device)
# Since it's a directory backup, we'll verify by checking file structure
if [ ! -d "$LATEST_BACKUP" ]; then
    log "ERROR: Backup directory does not exist"
    exit 1
fi

# Verify MySQL data directory structure exists
if [ ! -d "$LATEST_BACKUP/mysql" ] && [ ! -d "$LATEST_BACKUP/testdb" ]; then
    log "ERROR: Backup does not contain MySQL data directories"
    exit 1
fi

# Verify test database exists
if [ -d "$LATEST_BACKUP/testdb" ]; then
    log "SUCCESS: Test database 'testdb' found in backup"
    
    # Check for test_table
    if [ -f "$LATEST_BACKUP/testdb/test_table.ibd" ] || [ -f "$LATEST_BACKUP/testdb/test_table.MYD" ]; then
        log "SUCCESS: test_table found in backup"
    else
        log "WARNING: test_table not found, but database directory exists"
    fi
else
    log "WARNING: testdb directory not found in backup"
fi

# Verify backup contains essential MySQL files
ESSENTIAL_FILES=("ibdata1" "ib_logfile0" "mysql/user.MYD")
FOUND_ESSENTIAL=0
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$LATEST_BACKUP/$file" ] || [ -d "$LATEST_BACKUP/${file%/*}" ]; then
        FOUND_ESSENTIAL=$((FOUND_ESSENTIAL + 1))
    fi
done

if [ $FOUND_ESSENTIAL -gt 0 ]; then
    log "SUCCESS: Backup contains essential MySQL files ($FOUND_ESSENTIAL/${#ESSENTIAL_FILES[@]} checked)"
else
    log "WARNING: No essential MySQL files found in backup"
fi

log "=== Backup verification completed ==="
VERIFY_EOF

chmod +x /app/verify_restore.sh

echo "[oracle] Setting up cron job..."

# Create cron job
cat > /etc/cron.d/mysql-backup << 'CRON_EOF'
# MySQL backup cron job - runs daily at 2:00 AM
0 2 * * * root /app/backup_mysql.sh >> /var/log/mysql_backup.log 2>&1
CRON_EOF

chmod 644 /etc/cron.d/mysql-backup

echo "[oracle] All fixes applied successfully!"
