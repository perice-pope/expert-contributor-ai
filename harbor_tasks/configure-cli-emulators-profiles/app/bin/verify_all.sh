#!/bin/bash
set -euo pipefail

mkdir -p /output

echo "[verify] ensuring emulators are running..."
/app/bin/start_emulators.sh >/dev/null

bucket="tbench-local-bucket"
topic="tbench-topic"
sub="tbench-sub"
container="tbench-container"

echo "[verify] AWS (LocalStack S3) ..."
if ! /app/bin/aws_localstack.sh s3api head-bucket --bucket "${bucket}" >/dev/null 2>&1; then
  /app/bin/aws_localstack.sh s3api create-bucket --bucket "${bucket}" >/dev/null
fi
/app/bin/aws_localstack.sh s3api list-buckets > /output/aws_s3_list.txt

echo "[verify] gcloud (Pub/Sub emulator) ..."
if ! /app/bin/gcloud_pubsub.sh topics describe "${topic}" >/dev/null 2>&1; then
  /app/bin/gcloud_pubsub.sh topics create "${topic}" >/dev/null
fi
if ! /app/bin/gcloud_pubsub.sh subscriptions describe "${sub}" >/dev/null 2>&1; then
  /app/bin/gcloud_pubsub.sh subscriptions create "${sub}" --topic "${topic}" >/dev/null
fi
{
  echo "== topics =="
  /app/bin/gcloud_pubsub.sh topics list
  echo
  echo "== subscriptions =="
  /app/bin/gcloud_pubsub.sh subscriptions list
} > /output/gcloud_pubsub_list.txt

echo "[verify] Azure (Azurite Blob) ..."
/app/bin/azure_profile.sh azurite container create --name "${container}" >/dev/null
/app/bin/azure_profile.sh azurite container list > /output/azure_blob_list.txt

echo "[verify] done"



