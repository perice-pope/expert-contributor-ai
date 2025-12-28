# Configure Cloud CLIs for Local Emulators (Profiles + Endpoints)

You’ve joined a team that runs integration tests **fully offline** using local emulators instead of real cloud services. The repo already contains scripts for configuring the CLIs — but they’re currently misconfigured and the verification flow fails.

## Requirements

1. **AWS CLI (LocalStack)**: Configure a named AWS profile called `localstack` that can create and list an S3 bucket via the LocalStack endpoint.
2. **gcloud (Pub/Sub emulator)**: Configure a named gcloud configuration called `pubsub-emulator` that can create and list a Pub/Sub topic and subscription against the emulator.
3. **Azure CLI (Azurite)**: Configure a named Azure “profile” called `azurite` (see `/app/bin/azure_profile.sh`) that can create and list a Blob container against Azurite.
4. **Persistence**: The settings must be persisted in the standard config locations so that a new shell can reuse them:
   - AWS: `/root/.aws/config` and `/root/.aws/credentials`
   - gcloud: `/root/.config/gcloud/configurations/config_pubsub-emulator`
   - Azure: `/root/.azure/config`
5. **Profile isolation**: Switching between profiles/configurations must not clobber the default configuration (tests will assert the defaults remain untouched).

## Configuration Details

### AWS (`localstack` profile)
- **Config files**: `/root/.aws/config` and `/root/.aws/credentials`
- **Format**: INI format
- **Required in credentials file**: Named profile `[localstack]` with `aws_access_key_id` and `aws_secret_access_key`
- **Required in config file**: Named profile `[profile localstack]` with `s3.endpoint_url` set to `http://127.0.0.1:4566`
- **⚠️ CRITICAL - Profile isolation**: 
  - **Always use `--profile localstack` flag** when using `aws configure set` commands
  - **Do NOT use** `aws configure set` without `--profile localstack` - this will modify the `[default]` profile instead
  - Example: `aws configure set aws_access_key_id "test" --profile localstack`
  - The default profile in both `/root/.aws/credentials` and `/root/.aws/config` must remain unchanged

### gcloud (`pubsub-emulator` configuration)
- **Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`
- **Project name**: `tbench-local`
- **Required settings**:
  - Project must be set to `tbench-local`
  - Pub/Sub API endpoint must be overridden to `http://127.0.0.1:8085/`
  - Authentication must be disabled for offline emulator operation: `auth/disable_credentials = true`
- **⚠️ CRITICAL - DO NOT ACTIVATE**: 
  - **Never run** `gcloud config configurations activate pubsub-emulator`
  - The file `/root/.config/gcloud/active_config` must remain set to `default`
  - **How to configure without activating**: 
    1. Create the configuration: `gcloud config configurations create pubsub-emulator --no-activate` (the `--no-activate` flag prevents automatic activation)
    2. Set configuration values using the `--configuration` flag: `gcloud --configuration pubsub-emulator config set <property> <value>`
    3. **Do NOT use** `gcloud config configurations activate` - this will change the active configuration
    4. **Do NOT use** `gcloud config set` without `--configuration` flag - this modifies the active configuration
    5. Verify `/root/.config/gcloud/active_config` remains `default` after all configuration steps
  - **How to use**: Always use `--configuration pubsub-emulator` flag on all gcloud commands (e.g., `gcloud --configuration pubsub-emulator pubsub topics list`)

### Azure (`azurite` profile)
- **Config file**: `/root/.azure/config`
- **Format**: INI format
- **Account**: Use Azurite's well-known development account: `devstoreaccount1`
- **Required settings**:
  - Named profile `azurite` must be created in `/root/.azure/config`
  - `account_name` must be set to `devstoreaccount1`
  - `blob_endpoint` must be set to `http://127.0.0.1:10000/devstoreaccount1` (note: must include the `/devstoreaccount1` path segment)
  - `account_key` must also be set (see `/app/bin/configure_azure.sh` for the well-known key value)

## Constraints

- **No external network calls**. Everything must work offline inside the container.
- **Do not change the emulator ports**. The environment assumes:
  - LocalStack: `http://127.0.0.1:4566`
  - Pub/Sub emulator: `127.0.0.1:8085`
  - Azurite Blob: `http://127.0.0.1:10000/devstoreaccount1`
- **Do not hardcode "pass" outputs**. Fix the configuration/scripts so the real CLI calls succeed.
- **Fix, don't replace**: Modify the existing scripts in `/app/bin/` to fix their bugs. Do NOT delete and rewrite them from scratch. If scripts contain `MARKER:` comments, these must be preserved to prove scripts were fixed, not replaced.
- **Use helper utilities**: The provided utilities (`write_ini_value.py`, `ini_get.py`) **MUST** be used for INI file manipulation. These utilities are located in `/app/bin/` and **MUST** be executed (not just referenced in comments) when manipulating INI-format configuration files. Tests verify that these utilities are actually executed during configuration.

## Files

- Starter project: `/app`
- AWS config files: `/root/.aws/config`, `/root/.aws/credentials`
- gcloud config directory: `/root/.config/gcloud/`
- Azure config file: `/root/.azure/config`
- Helper scripts:
  - `/app/bin/start_emulators.sh`
  - `/app/bin/configure_all.sh`
  - `/app/bin/verify_all.sh`
  - `/app/bin/azure_profile.sh`
- Helper utilities (must be used for INI file manipulation):
  - `/app/bin/write_ini_value.py` - for writing values to INI files
  - `/app/bin/ini_get.py` - for reading values from INI files
  - `/app/bin/wait_for_ports.py` - for waiting for emulator ports to be ready

## Execution Order

The emulators must be running and ready BEFORE any CLI commands are executed against them:

1. **Start emulators first**: Run `/app/bin/start_emulators.sh` 
2. **Wait for readiness**: Use `/app/bin/wait_for_ports.py` to ensure ports are listening:
   ```bash
   python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000
   ```
3. **Then configure**: Only run configuration scripts after emulators are ready
4. **Then verify**: Run verification after configuration is complete

⚠️ **CRITICAL REQUIREMENT**: The `verify_all.sh` script **MUST** call `wait_for_ports.py` to ensure emulators are ready before executing CLI commands. Even though `start_emulators.sh` starts the emulators, they may not be immediately ready to accept connections. 

**Required implementation in `verify_all.sh`**:
- After calling `/app/bin/start_emulators.sh`, you **MUST** call `wait_for_ports.py` before executing any CLI commands
- The call must use the correct syntax: `python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000`
- This waiting logic is **REQUIRED** and will be verified by tests - the script must actually execute `wait_for_ports.py` (not just reference it in comments)

## Outputs

The verification flow must complete and write logs:

- `/output/aws_s3_list.txt` (text; output of listing S3 buckets via LocalStack profile)
- `/output/gcloud_pubsub_list.txt` (text; output of listing topics + subscriptions via Pub/Sub emulator config)
- `/output/azure_blob_list.txt` (text; output of listing blob containers via Azurite profile)



