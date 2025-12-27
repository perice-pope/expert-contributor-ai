# Configure Cloud CLIs for Local Emulators  

You've joined a team that runs integration tests fully offline using local emulators. The repo contains incomplete configuration scripts that have bugs preventing proper profile isolation.

## Task

Fix the CLI configuration scripts so that all three cloud tools (AWS, gcloud, Azure) can work with their respective local emulators using named profiles/configurations - without affecting existing default configurations.

**Named profiles to create:**
- AWS: `localstack`
- gcloud: `pubsub-emulator`
- Azure: `azurite`

**Emulator endpoints** (do not change these):
- LocalStack S3: `http://127.0.0.1:4566`
- Pub/Sub emulator: `http://127.0.0.1:8085/`  
- Azurite Blob: `http://127.0.0.1:10000`

## Critical Requirements

1. **Profile isolation**: Default profiles must remain untouched (tests will verify)
2. **Persistence**: Configurations must survive shell restarts (write to config files)
3. **Orchestration**: Create `/app/bin/configure_all.sh` to run all three configuration scripts
4. **Format compliance**: Each tool has specific config file format requirements (see below)

## Tool-Specific Configuration Details

### AWS (`localstack` profile)
- **Config files**: `/root/.aws/config` and `/root/.aws/credentials`
- **Format**: INI format
- **Required in credentials**: `[localstack]` section with `aws_access_key_id` and `aws_secret_access_key`
- **Required in config**: `[profile localstack]` section with `s3.endpoint_url = http://127.0.0.1:4566`

### gcloud (`pubsub-emulator` configuration)
- **Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`
- **Project name**: `tbench-local`
- **Required settings**:
  - `[core]` section with `project = tbench-local`
  - `[api_endpoint_overrides]` section with `pubsub = http://127.0.0.1:8085/`
  - `[auth]` section with `disable_credentials = true` (CRITICAL: required for offline emulator operation)
- **⚠️ DO NOT ACTIVATE**: Never run `gcloud config configurations activate pubsub-emulator`. The file `/root/.config/gcloud/active_config` must remain set to `default`. Use `--configuration pubsub-emulator` flag on gcloud commands instead.

### Azure (`azurite` profile)
- **Config file**: `/root/.azure/config`
- **Format**: INI format
- **Account**: Use Azurite's well-known development account: `devstoreaccount1`
- **Required in config**: `[azurite]` section with:
  - `account_name = devstoreaccount1`
  - `blob_endpoint = http://127.0.0.1:10000/devstoreaccount1`

## Constraints (ENFORCED BY TESTS)

⚠️ **These constraints are verified by automated tests - violations will cause failures:**

1. **Fix, don't replace**: Modify the existing scripts in `/app/bin/` to fix their bugs. Do NOT delete and rewrite them from scratch. Each script contains a `MARKER:` comment that must be preserved.

2. **Use helper utilities**: The provided utilities (`write_ini_value.py`, `ini_get.py`) must be used for INI file manipulation. Tests verify at least one script uses `write_ini_value.py`.

3. **Offline only**: No external network calls allowed. The emulators run on localhost - all operations must work without internet access.

4. **Orchestration required**: The `configure_all.sh` script must call all three individual configure scripts.

## Files

- Starter project: `/app`
- Individual configuration scripts: `/app/bin/configure_aws.sh`, `/app/bin/configure_gcloud.sh`, `/app/bin/configure_azure.sh`
- Orchestration script to create: `/app/bin/configure_all.sh` (calls all three configure scripts)
- Config file locations:
  - AWS: `/root/.aws/config` and `/root/.aws/credentials`
  - gcloud: `/root/.config/gcloud/configurations/config_pubsub-emulator`
  - Azure: `/root/.azure/config`
- Helper utilities: `/app/bin/write_ini_value.py`, `/app/bin/ini_get.py`, `/app/bin/wait_for_ports.py`
- Verification: `/app/bin/verify_all.sh`

## Outputs

The verification flow must complete and write logs:

- `/output/aws_s3_list.txt` - JSON output of `aws s3api list-buckets` with a bucket named `tbench-local-bucket`
  - Expected format: `{"Buckets": [{"Name": "tbench-local-bucket", ...}], ...}`
- `/output/gcloud_pubsub_list.txt` - Text output listing topics and subscriptions including `tbench-topic` and `tbench-sub`
- `/output/azure_blob_list.txt` - JSON array of containers including one named `tbench-container`
  - Expected format: `[{"name": "tbench-container", ...}]`

