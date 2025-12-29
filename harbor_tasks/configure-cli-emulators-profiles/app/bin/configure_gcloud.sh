#!/bin/bash
set -euo pipefail

mkdir -p /root/.config/gcloud/configurations

# NOTE: Intended behavior:
# - create a named configuration "pubsub-emulator"
# - persist a project + an emulator endpoint override in that configuration

GCLOUD_CONFIG_NAME="pubsub-emulator"
GCLOUD_PROJECT="tbench-local"
PUBSUB_ENDPOINT="http://127.0.0.1:8085/"

echo "[gcloud] configuring configuration '${GCLOUD_CONFIG_NAME}'..."

# CRITICAL: Use --no-activate to avoid changing active_config (must remain 'default')
if ! gcloud config configurations describe "${GCLOUD_CONFIG_NAME}" >/dev/null 2>&1; then
  gcloud config configurations create "${GCLOUD_CONFIG_NAME}" --no-activate --quiet >/dev/null
fi

# CRITICAL: Use --configuration flag on all config set commands to avoid modifying default configuration
gcloud --configuration "${GCLOUD_CONFIG_NAME}" config set project "${GCLOUD_PROJECT}" --quiet >/dev/null

# Persist a Pub/Sub endpoint override (used by our verification wrapper).
# CRITICAL: Endpoint must have trailing slash: http://127.0.0.1:8085/
gcloud --configuration "${GCLOUD_CONFIG_NAME}" config set api_endpoint_overrides/pubsub "${PUBSUB_ENDPOINT}" --quiet >/dev/null

# CRITICAL: Disable credentials for offline emulator operation
gcloud --configuration "${GCLOUD_CONFIG_NAME}" config set auth/disable_credentials true --quiet >/dev/null

echo "[gcloud] done"



