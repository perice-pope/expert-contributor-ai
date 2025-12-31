#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_PATH="/tests/test_outputs.py"
if [ ! -f "$TEST_PATH" ]; then
  TEST_PATH="$SCRIPT_DIR/test_outputs.py"
fi

set +e
python3 -m pytest -q -rA "$TEST_PATH"
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
set -e
