#!/bin/bash

# Write default reward file IMMEDIATELY 
# This ensures a reward file exists even if script is killed
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

# curl and uv are pre-installed in Dockerfile - just source uv env
source $HOME/.local/bin/env 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

# Check if we're in a valid working directory
if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    exit 1
fi

# Don't change anything below this line
echo "About to run pytest with uvx..."
uvx \
  -p 3.11 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA 2>&1
PYTEST_EXIT=$?

echo "Pytest exit code: $PYTEST_EXIT"

if [ $PYTEST_EXIT -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
  echo "Tests passed, reward set to 1"
else
  echo 0 > /logs/verifier/reward.txt
  echo "Tests failed, reward set to 0"
fi

# Ensure files are synced to disk before container exits
sync
sleep 1
