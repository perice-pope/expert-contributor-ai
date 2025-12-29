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

# Also persist region into config file (required for proper profile isolation).
# Region must be in BOTH credentials (via aws configure set) AND config (via write_ini_value.py).
if 'region' not in txt or 'write_ini_value.py' not in txt.split('s3.endpoint_url')[1] or 'region' not in txt.split('s3.endpoint_url')[1]:
    insert = (
        'python3 /app/bin/write_ini_value.py \\\n'
        '  --path /root/.aws/config \\\n'
        '  --section "profile ${AWS_PROFILE_NAME}" \\\n'
        '  --key "region" \\\n'
        '  --value "${AWS_REGION}"\n\n'
    )
    # Insert after the endpoint write_ini_value call
    txt = txt.replace(
        'echo "[aws] wrote endpoint into /root/.aws/config"\n',
        'echo "[aws] wrote endpoint into /root/.aws/config"\n' + insert
    )

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
# Use --no-activate when creating configuration
txt = re.sub(r'gcloud config configurations create "\$\{GCLOUD_CONFIG_NAME\}"',
             'gcloud config configurations create "${GCLOUD_CONFIG_NAME}" --no-activate',
             txt)
txt = re.sub(r'gcloud config set project "\$\{GCLOUD_PROJECT\}".*\n',
             'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set project "${GCLOUD_PROJECT}" >/dev/null\n',
             txt)
txt = re.sub(r'gcloud config set api_endpoint_overrides/pubsub "\$\{PUBSUB_ENDPOINT\}".*\n',
             'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set api_endpoint_overrides/pubsub "${PUBSUB_ENDPOINT}" >/dev/null\n',
             txt)
# Add auth/disable_credentials setting (required for offline emulator operation)
if 'auth/disable_credentials' not in txt:
    insert = 'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set auth/disable_credentials true >/dev/null\n'
    txt = txt.replace('echo "[gcloud] done"', insert + 'echo "[gcloud] done"')

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Fixing verify_all.sh to include emulator readiness wait..."
python3 - <<'PY'
from pathlib import Path

path = Path("/app/bin/verify_all.sh")
txt = path.read_text(encoding="utf-8")

# Add wait_for_ports.py call after start_emulators.sh
if 'wait_for_ports.py' not in txt:
    wait_code = 'python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000 --timeout-sec 60 || echo "[verify] warning: some emulators may not be ready, continuing anyway..."\n\n'
    txt = txt.replace(
        '/app/bin/start_emulators.sh >/dev/null\n',
        '/app/bin/start_emulators.sh >/dev/null\n' + wait_code
    )

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Running configuration + end-to-end verification..."
bash /app/bin/configure_all.sh
bash /app/bin/verify_all.sh

echo "[oracle] Done. Outputs:"
ls -la /output



