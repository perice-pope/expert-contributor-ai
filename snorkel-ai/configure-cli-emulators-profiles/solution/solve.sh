#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

# Start emulators first (so we can validate quickly after each tweak).
bash /app/bin/start_emulators.sh >/dev/null

echo "[oracle] Fixing AWS CLI profile isolation (stop mutating default)..."
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/app/bin/configure_aws.sh")
txt = path.read_text(encoding="utf-8")

# Add --profile localstack to all aws configure set calls.
txt = re.sub(r'aws configure set aws_access_key_id "?\$\{AWS_ACCESS_KEY_ID\}"?\n',
             'aws configure set aws_access_key_id "${AWS_ACCESS_KEY_ID}" --profile "${AWS_PROFILE_NAME}"\n',
             txt)
txt = re.sub(r'aws configure set aws_secret_access_key "?\$\{AWS_SECRET_ACCESS_KEY\}"?\n',
             'aws configure set aws_secret_access_key "${AWS_SECRET_ACCESS_KEY}" --profile "${AWS_PROFILE_NAME}"\n',
             txt)
txt = re.sub(r'aws configure set region "?\$\{AWS_REGION\}"?\n',
             'aws configure set region "${AWS_REGION}" --profile "${AWS_PROFILE_NAME}"\n',
             txt)

# Also persist region into config for completeness (idempotent).
if 'write_ini_value.py \\\n+  --path /root/.aws/config' in txt and 'region' not in txt.split('s3.endpoint_url')[0]:
    insert = (
        'python3 /app/bin/write_ini_value.py \\\n'
        '  --path /root/.aws/config \\\n'
        '  --section "profile ${AWS_PROFILE_NAME}" \\\n'
        '  --key "region" \\\n'
        '  --value "${AWS_REGION}"\n\n'
    )
    txt = txt.replace('echo "[aws] wrote endpoint into /root/.aws/config"\n', insert + 'echo "[aws] wrote endpoint into /root/.aws/config"\n')

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Fixing Azurite endpoint persistence..."
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/app/bin/configure_azure.sh")
txt = path.read_text(encoding="utf-8")
txt = re.sub(r'AZURITE_BLOB_ENDPOINT="http://127\.0\.0\.1:10000"\n',
             'AZURITE_BLOB_ENDPOINT="http://127.0.0.1:10000/devstoreaccount1"\n',
             txt)
path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Fixing gcloud configuration isolation (do not change active_config)..."
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/app/bin/configure_gcloud.sh")
txt = path.read_text(encoding="utf-8")

# Remove activation step and use --configuration scoped commands.
txt = re.sub(r'gcloud config configurations activate "\$\{GCLOUD_CONFIG_NAME\}".*\n', '', txt)
txt = re.sub(r'gcloud config set project "\$\{GCLOUD_PROJECT\}".*\n',
             'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set project "${GCLOUD_PROJECT}" >/dev/null\n',
             txt)
txt = re.sub(r'gcloud config set api_endpoint_overrides/pubsub "\$\{PUBSUB_ENDPOINT\}".*\n',
             'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set api_endpoint_overrides/pubsub "${PUBSUB_ENDPOINT}" >/dev/null\n',
             txt)

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Running configuration + end-to-end verification..."
bash /app/bin/configure_all.sh
bash /app/bin/verify_all.sh

echo "[oracle] Done. Outputs:"
ls -la /output



