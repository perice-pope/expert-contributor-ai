#!/bin/bash
set -euo pipefail

# Initialize LVM setup for MySQL backup task
# This script creates a loop device, volume group, and logical volume
# Then moves MySQL data to the logical volume

echo "[init] Setting up LVM for MySQL backup task..."

# Create a loop device with a file
LOOP_FILE=/tmp/lvm-backing-file
LOOP_SIZE=5G
dd if=/dev/zero of=$LOOP_FILE bs=1M count=5120 2>/dev/null

# Find next available loop device
LOOP_DEV=$(losetup -f)
losetup $LOOP_DEV $LOOP_FILE

# Create physical volume
pvcreate -y $LOOP_DEV

# Create volume group
vgcreate -y vg_mysql $LOOP_DEV

# Create logical volume (4GB for MySQL data)
lvcreate -y -L 4G -n lv_mysql_data vg_mysql

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

# Start MySQL
echo "[init] Starting MySQL..."
mysqld_safe --user=mysql --datadir=/var/lib/mysql &
MYSQL_PID=$!

# Wait for MySQL to be ready
for i in {1..30}; do
    if mysqladmin ping --silent 2>/dev/null; then
        break
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

