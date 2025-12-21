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

# Ensure MySQL socket directory exists
mkdir -p /run/mysqld
chown mysql:mysql /run/mysqld 2>/dev/null || true
chmod 755 /run/mysqld

# Check if MySQL is running, start if not
# Harbor verifier might run in different context where init-lvm.sh MySQL isn't accessible
if ! mysqladmin ping --silent 2>/dev/null; then
    echo "MySQL not accessible, starting..." >&2
    
    # Check if MySQL data directory exists and is initialized
    if [ ! -d "/var/lib/mysql/mysql" ]; then
        echo "Initializing MySQL data directory..." >&2
        mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db
    fi
    
    # Start MySQL - use nohup and disown to keep it running
    nohup mysqld_safe --user=mysql --datadir=/var/lib/mysql --socket=/run/mysqld/mysqld.sock > /var/log/mysqld_safe.log 2>&1 &
    MYSQL_PID=$!
    echo "MySQL started with PID: $MYSQL_PID" >&2
    disown $MYSQL_PID 2>/dev/null || true
    
    # Wait for MySQL to initialize
    sleep 10
fi

# Wait for MySQL to be ready (with timeout)
echo "Waiting for MySQL to be ready..." >&2
for i in {1..90}; do
    if mysqladmin ping --silent 2>/dev/null; then
        echo "MySQL is ready!" >&2
        break
    fi
    if [ $i -eq 90 ]; then
        echo "ERROR: MySQL not ready after 90 seconds" >&2
        echo "Checking MySQL process..." >&2
        ps aux | grep -i mysql >&2 || true
        echo "Checking MySQL logs..." >&2
        tail -30 /var/log/mysqld_safe.log >&2 || true
        echo 0 > /logs/verifier/reward.txt
        exit 1
    fi
    sleep 1
done

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
