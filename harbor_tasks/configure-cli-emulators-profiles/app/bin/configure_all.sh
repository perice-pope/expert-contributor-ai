#!/bin/bash
set -euo pipefail

echo "[configure] setting up all CLI profiles/configurations..."

/app/bin/configure_aws.sh
/app/bin/configure_gcloud.sh
/app/bin/configure_azure.sh

echo "[configure] done"



