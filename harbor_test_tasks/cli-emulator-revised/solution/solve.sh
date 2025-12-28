#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

bash /app/bin/start_emulators.sh >/dev/null

echo "[oracle] Creating orchestration script (removed for difficulty)..."
cat > /app/bin/configure_all.sh <<'MASTER'
#!/bin/bash
set -euo pipefail
echo "[configure] setting up all CLI profiles/configurations..."
/app/bin/configure_aws.sh
/app/bin/configure_gcloud.sh
/app/bin/configure_azure.sh
echo "[configure] done"
MASTER
chmod +x /app/bin/configure_all.sh

echo "[oracle] Fixing AWS profile isolation..."
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/app/bin/configure_aws.sh")
txt = path.read_text(encoding="utf-8")

txt = re.sub(
    r'aws configure set aws_access_key_id "\$\{AWS_ACCESS_KEY_ID\}"',
    r'aws configure set aws_access_key_id "${AWS_ACCESS_KEY_ID}" --profile "${AWS_PROFILE_NAME}"',
    txt
)
txt = re.sub(
    r'aws configure set aws_secret_access_key "\$\{AWS_SECRET_ACCESS_KEY\}"',
    r'aws configure set aws_secret_access_key "${AWS_SECRET_ACCESS_KEY}" --profile "${AWS_PROFILE_NAME}"',
    txt
)
txt = re.sub(
    r'aws configure set region "\$\{AWS_REGION\}"',
    r'aws configure set region "${AWS_REGION}" --profile "${AWS_PROFILE_NAME}"',
    txt
)

# Add region to config file persistence
if 'write_ini_value.py' in txt and 's3.endpoint_url' in txt and '--key "region"' not in txt:
    insert = '''python3 /app/bin/write_ini_value.py \\
  --path /root/.aws/config \\
  --section "profile ${AWS_PROFILE_NAME}" \\
  --key "region" \\
  --value "${AWS_REGION}"

'''
    txt = txt.replace('echo "[aws] wrote endpoint into /root/.aws/config"', insert + 'echo "[aws] wrote endpoint into /root/.aws/config"')

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Fixing Azure endpoint..."
python3 - <<'PY'
from pathlib import Path

path = Path("/app/bin/configure_azure.sh")
txt = path.read_text(encoding="utf-8")

txt = txt.replace(
    'AZURITE_BLOB_ENDPOINT="http://127.0.0.1:10000"',
    'AZURITE_BLOB_ENDPOINT="http://127.0.0.1:10000/devstoreaccount1"'
)

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Fixing gcloud isolation and auth..."
python3 - <<'PY'
from pathlib import Path
import re

path = Path("/app/bin/configure_gcloud.sh")
txt = path.read_text(encoding="utf-8")

# Remove activation
txt = re.sub(
    r'gcloud config configurations activate "\$\{GCLOUD_CONFIG_NAME\}".*\n',
    '',
    txt
)

# Use scoped commands
txt = re.sub(
    r'gcloud config set project "\$\{GCLOUD_PROJECT\}".*\n',
    r'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set project "${GCLOUD_PROJECT}" >/dev/null\n',
    txt
)
txt = re.sub(
    r'gcloud config set api_endpoint_overrides/pubsub "\$\{PUBSUB_ENDPOINT\}".*\n',
    r'gcloud --quiet --configuration "${GCLOUD_CONFIG_NAME}" config set api_endpoint_overrides/pubsub "${PUBSUB_ENDPOINT}" >/dev/null\n',
    txt
)

# Add auth bypass
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
    wait_code = '''python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000 --timeout-sec 60 || echo "[verify] warning: some emulators may not be ready, continuing anyway..."

'''
    txt = txt.replace(
        '/app/bin/start_emulators.sh >/dev/null\n',
        '/app/bin/start_emulators.sh >/dev/null\n' + wait_code
    )

path.write_text(txt, encoding="utf-8")
PY

echo "[oracle] Running configuration and verification..."
bash /app/bin/configure_all.sh
bash /app/bin/verify_all.sh

echo "[oracle] Done:"
ls -la /output
