#!/bin/bash

# Write default reward file IMMEDIATELY 
# This ensures a reward file exists even if script is killed
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

# Check if we're in a valid working directory
if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    exit 1
fi

# Debug: Show mount status
echo "DEBUG: Checking mount status..." >&2
mount | grep mysql >&2 || echo "No mysql mounts found" >&2
echo "DEBUG: Checking LVM status..." >&2
lvs 2>&1 | head -5 >&2 || echo "LVM not available" >&2
echo "DEBUG: Checking MySQL data dir..." >&2
ls -la /var/lib/mysql/ 2>&1 | head -5 >&2 || echo "MySQL data dir not accessible" >&2

# Check if LVM and MySQL are set up
# The init-lvm.sh should have run at container start; if MySQL data exists, we can proceed
if ! mount | grep -q "vg_mysql"; then
    echo "LVM not mounted, trying to set up..." >&2
    
    # Check if LVM volume exists
    if lvs vg_mysql/lv_mysql_data &>/dev/null; then
        echo "LVM volume exists, mounting..." >&2
        mount /dev/vg_mysql/lv_mysql_data /var/lib/mysql 2>&1 >&2 || true
    else
        echo "LVM volume not found, trying init-lvm.sh..." >&2
        if [ -x /usr/local/bin/init-lvm.sh ]; then
            /usr/local/bin/init-lvm.sh 2>&1 >&2 || echo "init-lvm.sh failed" >&2
        fi
    fi
fi

# Show final mount status
echo "DEBUG: Final mount status..." >&2
mount | grep -E "mysql|vg_mysql" >&2 || echo "Still no mysql/LVM mounts" >&2

# Ensure MySQL socket directory exists
mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld 2>/dev/null || true
chmod 755 /run/mysqld

# MySQL may have died between agent and verifier phases - restart it if needed
if ! mysqladmin ping --silent 2>/dev/null; then
    echo "MySQL not running, attempting to start it..." >&2
    
    # Start MySQL in background
    mysqld_safe --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock > /var/log/mysqld_safe.log 2>&1 &
    
    # Wait for MySQL to be ready (up to 60 seconds)
    for i in {1..60}; do
        if mysqladmin ping --silent 2>/dev/null; then
            echo "MySQL started successfully (attempt $i)" >&2
            break
        fi
        if [ $i -eq 60 ]; then
            echo "ERROR: MySQL failed to start after 60 seconds" >&2
            echo "Checking MySQL process..." >&2
            ps aux | grep -i mysql | grep -v grep >&2 || echo "No MySQL process found" >&2
            echo "Checking MySQL socket..." >&2
            ls -la /run/mysqld/ >&2 || true
            echo "Checking MySQL logs..." >&2
            tail -50 /var/log/mysqld_safe.log >&2 || true
            exit 1
        fi
        sleep 1
    done
fi

echo "MySQL is ready, proceeding with tests..." >&2

# pytest and pytest-json-ctrf are pre-installed in Dockerfile
# Run pytest directly
echo "Running pytest..." >&2
python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -v 2>&1
PYTEST_EXIT=$?
echo "Pytest exit code: $PYTEST_EXIT" >&2

if [ $PYTEST_EXIT -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
  echo "Tests passed, reward set to 1" >&2
else
  echo 0 > /logs/verifier/reward.txt
  echo "Tests failed, reward set to 0" >&2
fi

# Ensure files are synced to disk before container exits
sync
sleep 1
