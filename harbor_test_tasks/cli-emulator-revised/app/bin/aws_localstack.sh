#!/bin/bash
set -euo pipefail

AWS_PROFILE_NAME="localstack"
AWS_CONFIG="/root/.aws/config"

endpoint="$(
  python3 /app/bin/ini_get.py \
    --path "${AWS_CONFIG}" \
    --section "profile ${AWS_PROFILE_NAME}" \
    --key "s3.endpoint_url"
)"

exec aws --profile "${AWS_PROFILE_NAME}" --endpoint-url "${endpoint}" "$@"



