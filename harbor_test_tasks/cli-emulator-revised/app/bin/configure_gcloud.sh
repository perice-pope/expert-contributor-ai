#!/bin/bash
set -euo pipefail
# MARKER:GCLOUD_CONFIG_SCRIPT_V1 - DO NOT REMOVE THIS LINE

mkdir -p /root/.config/gcloud/configurations

# NOTE: Intended behavior:
# - create a named configuration "pubsub-emulator"
# - persist a project + an emulator endpoint override in that configuration
# FIX THE BUGS BELOW - do not rewrite this script from scratch.

GCLOUD_CONFIG_NAME="pubsub-emulator"
GCLOUD_PROJECT="tbench-local"
PUBSUB_ENDPOINT="http://127.0.0.1:8085/"

echo "[gcloud] configuring configuration '${GCLOUD_CONFIG_NAME}'..."

if ! gcloud config configurations describe "${GCLOUD_CONFIG_NAME}" >/dev/null 2>&1; then
  gcloud config configurations create "${GCLOUD_CONFIG_NAME}" --quiet >/dev/null
fi

# BUG (intentional): activates the config but then uses commands that can stomp defaults
# in surprising ways when CLOUDSDK_CONFIG is shared.
gcloud config configurations activate "${GCLOUD_CONFIG_NAME}" --quiet >/dev/null
gcloud config set project "${GCLOUD_PROJECT}" --quiet >/dev/null

# Persist a Pub/Sub endpoint override (used by our verification wrapper).
gcloud config set api_endpoint_overrides/pubsub "${PUBSUB_ENDPOINT}" --quiet >/dev/null

echo "[gcloud] done"



