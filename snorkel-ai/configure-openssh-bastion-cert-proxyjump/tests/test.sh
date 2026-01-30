#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Install pytest into system Python
pip install --no-cache-dir pytest==8.3.3

TEST_DIR="${TEST_DIR:-/tests}"

set +e
python3 -m pytest "$TEST_DIR/test_outputs.py" -rA -v
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
