#!/bin/bash
set -euo pipefail

mkdir -p /root/.aws

# NOTE: This script is *intended* to create a named profile called "localstack".
# Right now it "mostly works" but something is off — see tests/instructions.

AWS_PROFILE_NAME="localstack"
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="test"
AWS_SECRET_ACCESS_KEY="test"
AWS_S3_ENDPOINT="http://127.0.0.1:4566"

echo "[aws] configuring profile '${AWS_PROFILE_NAME}'..."

# CRITICAL: Use --profile flag on all aws configure set commands to avoid modifying [default]
aws configure set aws_access_key_id "${AWS_ACCESS_KEY_ID}" --profile "${AWS_PROFILE_NAME}"
aws configure set aws_secret_access_key "${AWS_SECRET_ACCESS_KEY}" --profile "${AWS_PROFILE_NAME}"
aws configure set region "${AWS_REGION}" --profile "${AWS_PROFILE_NAME}"

# Persist our custom endpoint so wrappers can discover it.
# (AWS CLI doesn't universally read this automatically for all commands.)
python3 /app/bin/write_ini_value.py \
  --path /root/.aws/config \
  --section "profile ${AWS_PROFILE_NAME}" \
  --key "s3.endpoint_url" \
  --value "${AWS_S3_ENDPOINT}"

# CRITICAL: Region must be in BOTH credentials (via aws configure set above) AND config file.
# AWS CLI requires region in config file for proper profile isolation.
python3 /app/bin/write_ini_value.py \
  --path /root/.aws/config \
  --section "profile ${AWS_PROFILE_NAME}" \
  --key "region" \
  --value "${AWS_REGION}"

echo "[aws] wrote endpoint and region into /root/.aws/config"



