#!/bin/bash
# Note: Not using set -e because we want to continue even if some commands fail
# This allows the script to be called from solve.sh without killing the container

# Initialize LVM setup for MySQL backup task
# This script creates a loop device, volume group, and logical volume
# Then moves MySQL data to the logical volume

echo "[init] Setting up LVM for MySQL backup task..."

# Try to load device-mapper snapshot module (needed for LVM snapshots)
echo "[init] Loading dm-snapshot kernel module..."
modprobe dm-snapshot 2>/dev/null || echo "[init] Warning: Could not load dm-snapshot module"

# Create a loop device with a file - use unique name to avoid conflicts
LOOP_FILE="/tmp/lvm-backing-file-$$"
LOOP_SIZE=500M
echo "[init] Creating backing file: $LOOP_FILE"

# Reduced from 5GB to 500MB for low-memory systems
dd if=/dev/zero of=$LOOP_FILE bs=1M count=500 2>/dev/null

# Ensure loop device kernel module is loaded
modprobe loop 2>/dev/null || echo "[init] Warning: Could not load loop module"

# Find a free loop device or detach an orphaned one
LOOP_DEV=""
for i in $(seq 0 255); do
    DEV="/dev/loop$i"
    if [ -e "$DEV" ]; then
        # Check if this loop device is free
        if ! losetup "$DEV" 2>/dev/null | grep -q .; then
            LOOP_DEV="$DEV"
            break
        fi
        # Check if backing file no longer exists (orphaned)
        BACKING=$(losetup "$DEV" 2>/dev/null | awk '{print $6}' | tr -d '()')
        if [ -n "$BACKING" ] && [ ! -f "$BACKING" ]; then
            echo "[init] Detaching orphaned loop device $DEV (backing file gone)"
            losetup -d "$DEV" 2>/dev/null || true
            LOOP_DEV="$DEV"
            break
        fi
    fi
done

if [ -z "$LOOP_DEV" ]; then
    # Try losetup -f as fallback
    LOOP_DEV=$(losetup -f 2>/dev/null)
fi

if [ -z "$LOOP_DEV" ]; then
    echo "[init] ERROR: Cannot find loop device. All loop devices may be in use."
    exit 1
fi

echo "[init] Using loop device: $LOOP_DEV"

# Create the loop device node if it doesn't exist
if [ ! -e "$LOOP_DEV" ]; then
    LOOP_NUM=$(echo "$LOOP_DEV" | grep -o '[0-9]*$')
    echo "[init] Creating loop device node: $LOOP_DEV"
    mknod "$LOOP_DEV" b 7 "$LOOP_NUM" 2>/dev/null || true
fi

if ! losetup "$LOOP_DEV" "$LOOP_FILE" 2>&1; then
    echo "[init] ERROR: Cannot set up loop device $LOOP_DEV"
    echo "[init] Checking loop device status..."
    losetup -a 2>&1 | head -10 || true
    exit 1
fi

# Clean up any existing vg_mysql volume group from previous runs
if vgs vg_mysql &>/dev/null; then
    echo "[init] Cleaning up existing vg_mysql volume group..."
    # Unmount any mounted LV
    umount /var/lib/mysql 2>/dev/null || true
    umount /mnt/lv_mysql 2>/dev/null || true
    # Remove snapshots first
    lvremove -f vg_mysql/mysql_snapshot 2>/dev/null || true
    # Remove the main LV
    lvremove -f vg_mysql/lv_mysql_data 2>/dev/null || true
    # Remove the VG
    vgremove -f vg_mysql 2>/dev/null || true
fi

# Create physical volume
pvcreate -y $LOOP_DEV

# Create volume group
vgcreate -y vg_mysql $LOOP_DEV

# Create logical volume (400MB for MySQL data - reduced for low-memory systems)
lvcreate -y -L 400M -n lv_mysql_data vg_mysql

# Format as ext4
mkfs.ext4 -F /dev/vg_mysql/lv_mysql_data

# Mount the logical volume
mkdir -p /mnt/lv_mysql
mount /dev/vg_mysql/lv_mysql_data /mnt/lv_mysql

# Copy MySQL data to logical volume
echo "[init] Copying MySQL data to logical volume..."
cp -a /var/lib/mysql/* /mnt/lv_mysql/ 2>/dev/null || true
chown -R mysql:mysql /mnt/lv_mysql

# Unmount and remount to proper location
umount /mnt/lv_mysql
mount /dev/vg_mysql/lv_mysql_data /var/lib/mysql

# Start MySQL (MariaDB uses mysqld_safe or systemctl, but in container we use mysqld_safe)
echo "[init] Starting MySQL..."
# Ensure socket directory exists (MariaDB default is /run/mysqld/mysqld.sock)
mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld
chmod 755 /run/mysqld

# Start MySQL in background - mysqld_safe will keep it running
# mysqld_safe handles restarts automatically
# Use nohup and redirect stdin to ensure it persists across script exits
nohup mysqld_safe --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock > /var/log/mysqld_safe.log 2>&1 < /dev/null &
MYSQL_PID=$!
echo "[init] Started mysqld_safe with PID: $MYSQL_PID"
sleep 5  # Give mysqld_safe more time to start

# Wait for MySQL to be ready
echo "[init] Waiting for MySQL to start..."
for i in {1..60}; do
    if mysqladmin ping --silent 2>/dev/null; then
        echo "[init] MySQL is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "[init] ERROR: MySQL failed to start after 60 seconds"
        exit 1
    fi
    sleep 1
done

# Create a test database and table
echo "[init] Creating test database..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS testdb;
USE testdb;
CREATE TABLE IF NOT EXISTS test_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    value INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO test_table (name, value) VALUES 
    ('sample1', 100),
    ('sample2', 200),
    ('sample3', 300);
EOF

echo "[init] LVM and MySQL setup complete!"
MYSQL_PID=$(pgrep -f mysqld_safe || echo "")
if [ -n "$MYSQL_PID" ]; then
    echo "[init] MySQL is running (PID: $MYSQL_PID)"
    # Verify MySQL is accessible
    if mysqladmin ping --silent 2>/dev/null; then
        echo "[init] MySQL is ready and accessible"
        # Create a marker file to indicate init is complete and MySQL is ready
        touch /tmp/init-complete.marker
        echo "[init] Init complete marker created"
    else
        echo "[init] WARNING: MySQL process exists but not responding to ping"
    fi
else
    echo "[init] ERROR: MySQL process not found after startup"
    exit 1
fi




