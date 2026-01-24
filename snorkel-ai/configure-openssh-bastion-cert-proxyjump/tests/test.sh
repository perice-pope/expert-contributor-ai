#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

apt-get update
apt-get install -y --no-install-recommends curl
rm -rf /var/lib/apt/lists/*

curl -LsSf https://astral.sh/uv/0.7.13/install.sh | sh
source "$HOME/.local/bin/env"

TEST_DIR="${TEST_DIR:-/tests}"

uv venv .tbench-testing
source .tbench-testing/bin/activate

uv pip install pytest==8.3.3

set +e
uv run pytest "$TEST_DIR/test_outputs.py" -rA -v
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
