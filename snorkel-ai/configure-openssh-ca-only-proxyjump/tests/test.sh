#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

# Install test dependencies
pip3 install --no-cache-dir --break-system-packages pytest==8.3.3 >/dev/null 2>&1

set +e
python3 -m pytest -q -rA /tests/test_outputs.py
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
