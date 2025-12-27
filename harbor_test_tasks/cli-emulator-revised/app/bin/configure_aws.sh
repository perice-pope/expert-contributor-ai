#!/bin/bash
set -euo pipefail
# MARKER:AWS_CONFIG_SCRIPT_V1 - DO NOT REMOVE THIS LINE

mkdir -p /root/.aws

# NOTE: This script is *intended* to create a named profile called "localstack".
# Right now it "mostly works" but something is off — see tests/instructions.
# FIX THE BUGS BELOW - do not rewrite this script from scratch.

AWS_PROFILE_NAME="localstack"
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="test"
AWS_SECRET_ACCESS_KEY="test"
AWS_S3_ENDPOINT="http://127.0.0.1:4566"

echo "[aws] configuring profile '${AWS_PROFILE_NAME}'..."

# BUG (intentional): these calls omit --profile, so they mutate [default].
aws configure set aws_access_key_id "${AWS_ACCESS_KEY_ID}"
aws configure set aws_secret_access_key "${AWS_SECRET_ACCESS_KEY}"
aws configure set region "${AWS_REGION}"

# Persist our custom endpoint so wrappers can discover it.
# (AWS CLI doesn't universally read this automatically for all commands.)
python3 /app/bin/write_ini_value.py \
  --path /root/.aws/config \
  --section "profile ${AWS_PROFILE_NAME}" \
  --key "s3.endpoint_url" \
  --value "${AWS_S3_ENDPOINT}"

echo "[aws] wrote endpoint into /root/.aws/config"



