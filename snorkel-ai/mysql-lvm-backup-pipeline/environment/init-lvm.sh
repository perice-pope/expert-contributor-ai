#!/bin/bash
set -euo pipefail

# Initialize LVM setup for MySQL backup task
# This script creates a loop device, volume group, and logical volume
# Then moves MySQL data to the logical volume

echo "[init] Setting up LVM for MySQL backup task..."

# Create a loop device with a file
LOOP_FILE=/tmp/lvm-backing-file
LOOP_SIZE=500M
# Reduced from 5GB to 500MB for low-memory systems
dd if=/dev/zero of=$LOOP_FILE bs=1M count=500 2>/dev/null

# Find next available loop device
LOOP_DEV=$(losetup -f)
losetup $LOOP_DEV $LOOP_FILE

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
mysqld_safe --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock > /var/log/mysqld_safe.log 2>&1 &
MYSQL_PID=$!
sleep 3  # Give mysqld_safe time to start

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
    else
        echo "[init] WARNING: MySQL process exists but not responding to ping"
    fi
else
    echo "[init] ERROR: MySQL process not found after startup"
    exit 1
fi




