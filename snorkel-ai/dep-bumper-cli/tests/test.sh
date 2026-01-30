#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Install pytest into system Python (which has pip-tools from Dockerfile)
pip install --no-cache-dir pytest==8.4.1

TEST_DIR="${TEST_DIR:-/tests}"

set +e
python3 -m pytest "$TEST_DIR/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
