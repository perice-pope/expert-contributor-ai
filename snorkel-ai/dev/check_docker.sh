#!/bin/bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  cat <<'EOF'
Docker CLI not found on PATH.

Harbor uses Docker to build/run task environments.

Install Docker Desktop (macOS) or Docker Engine (Linux), then re-run:
  docker --version
  docker info
EOF
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  cat <<'EOF'
Docker is installed, but the daemon is not reachable.

Common fixes:
- macOS: start Docker Desktop and wait for it to finish starting
- Linux: start the docker service (e.g. `sudo systemctl start docker`)
EOF
  exit 2
fi

echo "Docker OK: $(docker --version)"



