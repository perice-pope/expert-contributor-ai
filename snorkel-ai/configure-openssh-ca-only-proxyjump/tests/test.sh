#!/bin/bash
set -uo pipefail

# Install test dependencies (per benchmark guidelines, test deps should not pollute production image)
pip3 install --no-cache-dir --break-system-packages pytest==8.3.3

mkdir -p /logs/verifier

python3 -m pytest -q -rA /tests/test_outputs.py
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
