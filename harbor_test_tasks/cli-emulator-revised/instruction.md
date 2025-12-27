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
3. **Orchestration**: Create `/app/bin/configure_all.sh` to run all three configuration scripts in sequence
4. **Format compliance**: Each tool has specific config file format requirements (see below)
5. **Idempotency**: Configuration scripts should be safe to run multiple times - they must not fail if profiles already exist or if emulators are already running

## Tool-Specific Configuration Details

### AWS (`localstack` profile)
- **Config files**: `/root/.aws/config` and `/root/.aws/credentials`
- **Format**: INI format
- **Required in credentials**: Named profile `localstack` with access key and secret key
- **Required in config**: Named profile `localstack` with S3 endpoint URL set to `http://127.0.0.1:4566`

### gcloud (`pubsub-emulator` configuration)
- **Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`
- **Project name**: `tbench-local`
- **Required settings**:
  - Project must be set to `tbench-local`
  - Pub/Sub API endpoint must be overridden to `http://127.0.0.1:8085/`
  - Authentication must be disabled for offline emulator operation (set `auth/disable_credentials = true`)
- **⚠️ DO NOT ACTIVATE**: Never run `gcloud config configurations activate pubsub-emulator`. The file `/root/.config/gcloud/active_config` must remain set to `default`. Use `--configuration pubsub-emulator` flag on gcloud commands instead.

### Azure (`azurite` profile)
- **Config file**: `/root/.azure/config`
- **Format**: INI format
- **Account**: Use Azurite's well-known development account: `devstoreaccount1`
- **Required in config**: Named profile `azurite` with account name and blob endpoint configured for `http://127.0.0.1:10000/devstoreaccount1`

## Execution Order (CRITICAL)

The emulators must be running and ready BEFORE any CLI commands are executed against them:

1. **Start emulators first**: Run `/app/bin/start_emulators.sh` 
2. **Wait for readiness**: Use `/app/bin/wait_for_ports.py` to ensure ports are listening:
   ```bash
   python /app/bin/wait_for_ports.py 4566 8085 10000
   ```
3. **Then configure**: Only run configuration scripts after emulators are ready
4. **Then verify**: Run verification after configuration is complete

⚠️ **IMPORTANT**: The `verify_all.sh` script must ensure emulators are ready before executing CLI commands. Even though `start_emulators.sh` starts the emulators, they may not be immediately ready to accept connections. You must add appropriate waiting logic using the provided `wait_for_ports.py` utility to prevent connection errors.

If you see `ConnectionError` or `HTTPConnectionPool` errors like "Max retries exceeded", the emulator wasn't ready when the command ran. This waiting logic is **required** in verification scripts.

## Constraints (ENFORCED BY TESTS)

⚠️ **These constraints are verified by automated tests - violations will cause failures:**

1. **Fix, don't replace**: Modify the existing scripts in `/app/bin/` to fix their bugs. Do NOT delete and rewrite them from scratch. Each script contains a `MARKER:` comment that must be preserved.

2. **Use helper utilities**: The provided utilities (`write_ini_value.py`, `ini_get.py`) must be used for INI file manipulation. Tests verify the helper is actually executed (not just referenced).

3. **Offline only**: No external network calls allowed. The emulators run on localhost - all operations must work without internet access.

4. **Orchestration required**: The `configure_all.sh` script must actually call (execute) all three individual configure scripts. Tests verify execution via tracing.

## Files

- Starter project: `/app`
- Individual configuration scripts: `/app/bin/configure_aws.sh`, `/app/bin/configure_gcloud.sh`, `/app/bin/configure_azure.sh`
- Orchestration script to create: `/app/bin/configure_all.sh` (must execute all three individual configuration scripts)
- Config file locations:
  - AWS: `/root/.aws/config` and `/root/.aws/credentials`
  - gcloud: `/root/.config/gcloud/configurations/config_pubsub-emulator`
  - Azure: `/root/.azure/config`
- Helper utilities: `/app/bin/write_ini_value.py`, `/app/bin/ini_get.py`, `/app/bin/wait_for_ports.py`
- Verification: `/app/bin/verify_all.sh` (must include emulator readiness wait - see Execution Order section)

## Outputs

The verification flow must complete and write logs:

- `/output/aws_s3_list.txt` - JSON output of `aws s3api list-buckets` with a bucket named `tbench-local-bucket`
  - Expected format: `{"Buckets": [{"Name": "tbench-local-bucket", ...}], ...}`
- `/output/gcloud_pubsub_list.txt` - Text output listing topics and subscriptions including `tbench-topic` and `tbench-sub`
- `/output/azure_blob_list.txt` - JSON array of containers including one named `tbench-container`
  - Expected format: `[{"name": "tbench-container", ...}]`

