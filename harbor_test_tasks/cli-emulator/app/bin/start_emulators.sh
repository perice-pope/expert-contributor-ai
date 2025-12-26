#!/bin/bash
set -euo pipefail

mkdir -p /tmp/emulators /output

echo "[emulators] starting azurite (blob only)..."
if pgrep -f "azurite-blob" >/dev/null 2>&1; then
  echo "[emulators] azurite already running"
else
  mkdir -p /tmp/emulators/azurite
  nohup azurite-blob \
    --silent \
    --location /tmp/emulators/azurite \
    --debug /tmp/emulators/azurite/debug.log \
    --blobHost 127.0.0.1 \
    --blobPort 10000 \
    >/tmp/emulators/azurite/stdout.log 2>&1 &
fi

echo "[emulators] starting pubsub emulator..."
if pgrep -f "pubsub-emulator" >/dev/null 2>&1; then
  echo "[emulators] pubsub emulator already running"
else
  mkdir -p /tmp/emulators/pubsub
  # Runs a local gRPC endpoint on 127.0.0.1:8085.
  nohup gcloud beta emulators pubsub start \
    --host-port=127.0.0.1:8085 \
    --data-dir=/tmp/emulators/pubsub \
    --quiet \
    >/tmp/emulators/pubsub/stdout.log 2>&1 &
fi

echo "[emulators] starting moto s3 server..."
if pgrep -f "moto_server" >/dev/null 2>&1; then
  echo "[emulators] moto already running"
else
  mkdir -p /tmp/emulators/moto
  # moto_server provides an S3-compatible endpoint (lighter than LocalStack).
  nohup moto_server -H 127.0.0.1 -p 4566 \
    >/tmp/emulators/moto/stdout.log 2>&1 &
fi

python3 /app/bin/wait_for_ports.py \
  --tcp 127.0.0.1:10000 \
  --tcp 127.0.0.1:4566 \
  --tcp 127.0.0.1:8085 \
  --timeout-sec 120 \
|| {
  echo "[emulators] startup timed out; dumping emulator logs for debugging:" >&2
  for log in /tmp/emulators/*/stdout.log; do
    [ -f "$log" ] && { echo "=== $log ==="; tail -50 "$log"; } >&2 || true
  done
  exit 1
}

echo "[emulators] ready"


