#!/bin/bash
set -euo pipefail

# This is intentionally lightweight: Azurite doesn't require an Azure login.
# Instead we persist a named profile section in /root/.azure/config and read it here.

AZ_PROFILE_NAME="${1:-azurite}"
shift || true

AZ_CONFIG="/root/.azure/config"

account_name="$(
  python3 /app/bin/ini_get.py --path "${AZ_CONFIG}" --section "${AZ_PROFILE_NAME}" --key "account_name"
)"
account_key="$(
  python3 /app/bin/ini_get.py --path "${AZ_CONFIG}" --section "${AZ_PROFILE_NAME}" --key "account_key"
)"
blob_endpoint="$(
  python3 /app/bin/ini_get.py --path "${AZ_CONFIG}" --section "${AZ_PROFILE_NAME}" --key "blob_endpoint"
)"

exec az storage "$@" \
  --account-name "${account_name}" \
  --account-key "${account_key}" \
  --blob-endpoint "${blob_endpoint}"



