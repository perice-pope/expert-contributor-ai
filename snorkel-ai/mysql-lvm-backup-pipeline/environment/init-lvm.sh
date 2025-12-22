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
modprobe loop 2>/dev/null || echo "[init] Warning: Could not load loop module"

# STEP 1: Aggressive cleanup of any existing vg_mysql BEFORE doing anything else
echo "[init] Cleaning up any existing vg_mysql..."

# Force unmount any LVM-related mounts
umount /var/lib/mysql 2>/dev/null || true
umount /mnt/lv_mysql 2>/dev/null || true  
umount /mnt/mysql_snapshot 2>/dev/null || true

# Try to remove any dm devices with vg_mysql in the name
for dm in $(dmsetup ls 2>/dev/null | grep vg_mysql | awk '{print $1}'); do
    echo "[init] Removing dm device: $dm"
    dmsetup remove "$dm" 2>/dev/null || true
done

# Try vgremove regardless of what vgs reports (it might be partially present)
echo "[init] Force removing vg_mysql..."
vgchange -an vg_mysql 2>/dev/null || true
lvremove -f vg_mysql 2>/dev/null || true
# Use --removemissing to handle orphaned VGs whose PVs are gone
vgreduce --removemissing --force vg_mysql 2>/dev/null || true
vgremove -ff vg_mysql 2>/dev/null || true

# Clean up ALL PVs on loop devices
for pv in $(pvs --noheadings -o pv_name 2>/dev/null | grep loop | tr -d ' '); do
    echo "[init] Removing PV: $pv"
    pvremove -ff "$pv" 2>/dev/null || true
done

# Detach ALL loop devices associated with lvm-backing files
for dev in $(losetup -a 2>/dev/null | grep lvm-backing | cut -d: -f1); do
    echo "[init] Detaching loop device: $dev"
    losetup -d "$dev" 2>/dev/null || true
done

# Final check - if vg_mysql still exists, scan and remove again
vgscan 2>/dev/null || true
pvscan 2>/dev/null || true
if vgs vg_mysql &>/dev/null; then
    echo "[init] vg_mysql still exists after cleanup, forcing removal..."
    vgremove -ff vg_mysql 2>/dev/null || true
fi

# Remove stale /dev/vg_mysql directory if it exists from previous runs
if [ -d "/dev/vg_mysql" ]; then
    echo "[init] Removing stale /dev/vg_mysql directory..."
    rm -rf /dev/vg_mysql 2>/dev/null || true
fi

# Remove stale dm devices if any
for dm in /dev/dm-*; do
    if [ -e "$dm" ] && ! dmsetup info "$(basename "$dm")" &>/dev/null 2>&1; then
        echo "[init] Removing stale dm device: $dm"
        rm -f "$dm" 2>/dev/null || true
    fi
done

echo "[init] Cleanup complete"

# STEP 2: Create a new backing file
# Size: Need 400MB for data LV + at least 1GB for snapshot = 1.5GB minimum
# Using 2GB to have plenty of space
# Use fixed path to ensure cleanup and persistence
LOOP_FILE="/tmp/lvm-backing-file-mysql"

# Remove old backing file if it exists
if [ -f "$LOOP_FILE" ]; then
    echo "[init] Removing old backing file: $LOOP_FILE"
    rm -f "$LOOP_FILE" || true
fi

echo "[init] Creating 2GB backing file: $LOOP_FILE"

dd if=/dev/zero of="$LOOP_FILE" bs=1M count=2048 2>&1 || {
    echo "[init] ERROR: Failed to create backing file"
    exit 1
}

# Verify the file was created with correct size (2GB = 2147483648 bytes)
FILE_SIZE=$(stat -c%s "$LOOP_FILE" 2>/dev/null || echo "0")
echo "[init] Backing file created: $FILE_SIZE bytes"
if [ "$FILE_SIZE" -lt 2147483648 ]; then
    echo "[init] ERROR: Backing file too small: $FILE_SIZE bytes (expected 2147483648)"
    exit 1
fi

# STEP 3: Find a free loop device
LOOP_DEV=$(losetup -f 2>/dev/null)
if [ -z "$LOOP_DEV" ]; then
    echo "[init] ERROR: Cannot find free loop device"
    exit 1
fi

echo "[init] Using loop device: $LOOP_DEV"

# STEP 4: Set up the loop device
if ! losetup "$LOOP_DEV" "$LOOP_FILE" 2>&1; then
    echo "[init] ERROR: Cannot set up loop device $LOOP_DEV"
    losetup -a 2>&1 | head -10 || true
    exit 1
fi

echo "[init] Loop device set up successfully"

# Wait for device to settle
sleep 1

# STEP 5: Create PV, VG, LV
echo "[init] Creating physical volume..."
pvcreate -y "$LOOP_DEV" 2>&1 || {
    echo "[init] ERROR: Failed to create PV"
    exit 1
}

echo "[init] Creating volume group..."
# Remove /dev/vg_mysql if it exists as a directory (from previous manual device node creation)
rm -rf /dev/vg_mysql 2>/dev/null || true
vgcreate -y vg_mysql "$LOOP_DEV" 2>&1 || {
    echo "[init] ERROR: Failed to create VG"
    echo "[init] Checking for /dev/vg_mysql..."
    ls -la /dev/vg_mysql 2>&1 || true
    exit 1
}

echo "[init] Creating logical volume..."

# First, test if device-mapper linear target works
echo "[init] Testing device-mapper..."
# Create a simple test dm device
TEST_DM_OUTPUT=$(echo "0 1024000 linear $LOOP_DEV 0" | dmsetup create test_dm 2>&1)
TEST_DM_RC=$?
echo "[init] dmsetup create test: rc=$TEST_DM_RC output: $TEST_DM_OUTPUT"

if [ $TEST_DM_RC -eq 0 ]; then
    echo "[init] DM test succeeded, removing test device..."
    dmsetup remove test_dm 2>&1 || true
    
    # Try lvcreate with --zero n to skip the wiping that causes "device not cleared" error
    echo "[init] Creating LV with lvcreate --zero n..."
    LVCREATE_OUTPUT=$(lvcreate -y --zero n -L 400M -n lv_mysql_data vg_mysql 2>&1)
    LVCREATE_RC=$?
    echo "[init] lvcreate output: $LVCREATE_OUTPUT"
    echo "[init] lvcreate exit code: $LVCREATE_RC"
    
    if [ $LVCREATE_RC -ne 0 ]; then
        echo "[init] lvcreate --zero n failed, trying with additional options..."
        LVCREATE_OUTPUT=$(lvcreate -y --wipesignatures n -L 400M -n lv_mysql_data vg_mysql 2>&1)
        LVCREATE_RC=$?
        echo "[init] lvcreate wipesignatures output: $LVCREATE_OUTPUT"
        echo "[init] lvcreate wipesignatures exit code: $LVCREATE_RC"
    fi
    
    if [ $LVCREATE_RC -eq 0 ]; then
        echo "[init] lvcreate succeeded!"
        # Check if device node exists
        if [ ! -e "/dev/vg_mysql/lv_mysql_data" ]; then
            echo "[init] Device node not found, creating manually..."
            # Get info and create device nodes
            DM_MAJOR=$(awk '/device-mapper/ {print $1}' /proc/devices 2>/dev/null || echo "253")
            DM_MINOR=$(dmsetup info -c -o Minor --noheadings vg_mysql-lv_mysql_data 2>/dev/null | tr -d ' ')
            
            if [ -n "$DM_MINOR" ] && [ -n "$DM_MAJOR" ]; then
                mkdir -p /dev/mapper /dev/vg_mysql
                if [ ! -e "/dev/dm-$DM_MINOR" ]; then
                    mknod "/dev/dm-$DM_MINOR" b "$DM_MAJOR" "$DM_MINOR" 2>&1 || true
                fi
                ln -sf "/dev/dm-$DM_MINOR" /dev/mapper/vg_mysql-lv_mysql_data 2>&1 || true
                ln -sf /dev/mapper/vg_mysql-lv_mysql_data /dev/vg_mysql/lv_mysql_data 2>&1 || true
            fi
        fi
    else
        echo "[init] All lvcreate attempts failed, using dmsetup fallback..."
        # Fallback to manual dmsetup creation
        SECTORS=819200
        START_SECTOR=2048
        
        MANUAL_DM_OUTPUT=$(echo "0 $SECTORS linear $LOOP_DEV $START_SECTOR" | dmsetup create vg_mysql-lv_mysql_data 2>&1)
        MANUAL_DM_RC=$?
        
        if [ $MANUAL_DM_RC -eq 0 ]; then
            DM_MAJOR=$(awk '/device-mapper/ {print $1}' /proc/devices 2>/dev/null || echo "253")
            DM_MINOR=$(dmsetup info -c -o Minor --noheadings vg_mysql-lv_mysql_data 2>/dev/null | tr -d ' ')
            
            mkdir -p /dev/mapper /dev/vg_mysql
            if [ ! -e "/dev/dm-$DM_MINOR" ]; then
                mknod "/dev/dm-$DM_MINOR" b "$DM_MAJOR" "$DM_MINOR" 2>&1 || true
            fi
            ln -sf "/dev/dm-$DM_MINOR" /dev/mapper/vg_mysql-lv_mysql_data 2>&1 || true
            ln -sf /dev/mapper/vg_mysql-lv_mysql_data /dev/vg_mysql/lv_mysql_data 2>&1 || true
        else
            echo "[init] ERROR: All methods to create LV failed"
            exit 1
        fi
    fi
else
    echo "[init] ERROR: Device-mapper linear target not working"
    echo "[init] This might indicate the dm_mod kernel module is not properly available"
    dmsetup targets 2>&1 || true
    exit 1
fi

# Verify the LV exists and is accessible
LV_DEV="/dev/vg_mysql/lv_mysql_data"
if [ ! -e "$LV_DEV" ]; then
    LV_DEV="/dev/mapper/vg_mysql-lv_mysql_data"
fi

if [ -e "$LV_DEV" ]; then
    echo "[init] LV device exists: $LV_DEV"
else
    echo "[init] ERROR: LV device not found"
    exit 1
fi

echo "[init] LV created successfully"

# STEP 6: Format as ext4 - use the verified device path
echo "[init] Formatting as ext4 using: $LV_DEV"
mkfs.ext4 -F "$LV_DEV" 2>&1 || {
    echo "[init] ERROR: Failed to format LV"
    exit 1
}

# STEP 7: Mount the logical volume - use the verified device path
echo "[init] Mounting logical volume from: $LV_DEV"
mkdir -p /mnt/lv_mysql
mount "$LV_DEV" /mnt/lv_mysql || {
    echo "[init] ERROR: Failed to mount LV"
    exit 1
}

# STEP 8: Copy MySQL data to logical volume
echo "[init] Copying MySQL data to logical volume..."
cp -a /var/lib/mysql/* /mnt/lv_mysql/ 2>/dev/null || true
chown -R mysql:mysql /mnt/lv_mysql

# STEP 9: Unmount and remount to proper location - use verified device path
echo "[init] Unmounting from /mnt/lv_mysql..."
umount /mnt/lv_mysql

# Verify device still exists after unmount
echo "[init] Checking device after unmount..."
ls -la "$LV_DEV" 2>&1 || true
ls -la /dev/vg_mysql/ 2>&1 || true
ls -la /dev/mapper/ 2>&1 | grep vg_mysql || true

# Try both device paths for final mount
if mount "$LV_DEV" /var/lib/mysql 2>&1; then
    echo "[init] Mounted $LV_DEV to /var/lib/mysql"
elif mount /dev/mapper/vg_mysql-lv_mysql_data /var/lib/mysql 2>&1; then
    echo "[init] Mounted /dev/mapper/vg_mysql-lv_mysql_data to /var/lib/mysql"
else
    echo "[init] ERROR: Failed to mount LV to /var/lib/mysql"
    exit 1
fi

echo "[init] LVM setup complete, MySQL data now on LVM"

# STEP 10: Start MySQL
echo "[init] Starting MySQL..."
mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld
chmod 755 /run/mysqld

# Start MySQL in background
nohup mysqld_safe --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock > /var/log/mysqld_safe.log 2>&1 < /dev/null &
MYSQL_PID=$!
echo "[init] Started mysqld_safe with PID: $MYSQL_PID"

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
    if mysqladmin ping --silent 2>/dev/null; then
        echo "[init] MySQL is ready and accessible"
        touch /tmp/init-complete.marker
        echo "[init] Init complete marker created"
    else
        echo "[init] WARNING: MySQL process exists but not responding to ping"
    fi
else
    echo "[init] ERROR: MySQL process not found after startup"
    exit 1
fi
