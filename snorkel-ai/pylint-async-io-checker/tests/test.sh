#!/bin/bash

# Install curl
apt-get update
apt-get install -y curl

# Install uv
curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh
source $HOME/.local/bin/env 2>/dev/null || true

# Check if we're in a valid working directory
if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    exit 1
fi

# Run tests
python3 -m pytest /tests/test_outputs.py -rA
TEST_EXIT=$?

# Write reward based on test result
mkdir -p /logs/verifier
if [ $TEST_EXIT -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

# Ensure file is synced
sync
