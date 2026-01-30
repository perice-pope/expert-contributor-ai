#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Write default reward file
echo 0 > /logs/verifier/reward.txt

# Install pytest into system Python
pip install --no-cache-dir pytest==8.4.1

TEST_DIR="${TEST_DIR:-/tests}"

set +e
python3 -m pytest "$TEST_DIR/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
