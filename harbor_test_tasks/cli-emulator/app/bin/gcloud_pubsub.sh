#!/bin/bash
set -euo pipefail

# Wrapper that:
# - forces the named configuration
# - exports PUBSUB_EMULATOR_HOST derived from the configuration

GCLOUD_CONFIG_NAME="pubsub-emulator"
GCLOUD_CONFIG_FILE="/root/.config/gcloud/configurations/config_${GCLOUD_CONFIG_NAME}"

endpoint="$(
  python3 /app/bin/ini_get.py \
    --path "${GCLOUD_CONFIG_FILE}" \
    --section "api_endpoint_overrides" \
    --key "pubsub"
)"

project="$(
  python3 /app/bin/ini_get.py \
    --path "${GCLOUD_CONFIG_FILE}" \
    --section "core" \
    --key "project"
)"

# The emulator uses host:port (no scheme).
export PUBSUB_EMULATOR_HOST="${endpoint#http://}"
export PUBSUB_EMULATOR_HOST="${PUBSUB_EMULATOR_HOST%/}"

exec gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" --project "${project}" pubsub "$@"



