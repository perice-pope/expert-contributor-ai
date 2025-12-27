#!/bin/bash
set -euo pipefail
# MARKER:AZURE_CONFIG_SCRIPT_V1 - DO NOT REMOVE THIS LINE

mkdir -p /root/.azure

# We treat "azurite" as a named profile stored in /root/.azure/config.
# The helper /app/bin/azure_profile.sh loads the values and runs az storage commands.
# FIX THE BUGS BELOW - do not rewrite this script from scratch.

AZ_PROFILE_NAME="azurite"
AZURITE_ACCOUNT_NAME="devstoreaccount1"
AZURITE_ACCOUNT_KEY="Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="

# BUG (intentional): endpoint is missing the /devstoreaccount1 suffix.
AZURITE_BLOB_ENDPOINT="http://127.0.0.1:10000"

echo "[azure] writing profile '${AZ_PROFILE_NAME}' into /root/.azure/config..."

python3 /app/bin/write_ini_value.py \
  --path /root/.azure/config \
  --section "${AZ_PROFILE_NAME}" \
  --key "account_name" \
  --value "${AZURITE_ACCOUNT_NAME}"

python3 /app/bin/write_ini_value.py \
  --path /root/.azure/config \
  --section "${AZ_PROFILE_NAME}" \
  --key "account_key" \
  --value "${AZURITE_ACCOUNT_KEY}"

python3 /app/bin/write_ini_value.py \
  --path /root/.azure/config \
  --section "${AZ_PROFILE_NAME}" \
  --key "blob_endpoint" \
  --value "${AZURITE_BLOB_ENDPOINT}"

echo "[azure] done"



