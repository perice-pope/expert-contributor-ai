#!/bin/bash
set -euo pipefail

# Install test dependencies
pip install --no-cache-dir pytest==8.4.1 >/dev/null 2>&1

mkdir -p /logs/verifier

if python3 -m pytest -q -rA /tests/test_outputs.py; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi


