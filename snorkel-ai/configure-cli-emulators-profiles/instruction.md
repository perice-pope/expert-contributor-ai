# Configure Cloud CLIs for Local Emulators (Profiles + Endpoints)

You've joined a team that runs integration tests **fully offline** using local emulators instead of real cloud services. The repo already contains scripts for configuring the CLIs — but they're currently misconfigured and the verification flow fails.

## Requirements

1. **AWS CLI (LocalStack)**: Configure a named AWS profile called `localstack` that can create and list an S3 bucket via the LocalStack endpoint.
2. **gcloud (Pub/Sub emulator)**: Configure a named gcloud configuration called `pubsub-emulator` that can create and list a Pub/Sub topic and subscription against the emulator.
3. **Azure CLI (Azurite)**: Configure a named Azure "profile" called `azurite` (see `/app/bin/azure_profile.sh`) that can create and list a Blob container against Azurite.
4. **Persistence**: The settings must be persisted in the standard config locations so that a new shell can reuse them:
   - AWS: `/root/.aws/config` and `/root/.aws/credentials`
   - gcloud: `/root/.config/gcloud/configurations/config_pubsub-emulator`
   - Azure: `/root/.azure/config`
5. **Profile isolation**: Switching between profiles/configurations must not clobber the default configuration (tests will assert the defaults remain untouched).

## Configuration Details

### AWS (`localstack` profile)

**Config files**: `/root/.aws/config` and `/root/.aws/credentials` (both files are required)

**Required configuration**:

The `localstack` profile must be configured with the following settings:

1. **Credentials in `/root/.aws/credentials`**:
   - Section `[localstack]` must contain:
     - `aws_access_key_id = test`
     - `aws_secret_access_key = test`
     - `region = us-east-1`

2. **Configuration in `/root/.aws/config`**:
   - Section `[profile localstack]` must contain:
     - `s3.endpoint_url = http://127.0.0.1:4566`
     - `region = us-east-1`

3. **CRITICAL - Region must be in BOTH files**:
   - Region `us-east-1` must exist in `/root/.aws/credentials` under `[localstack]` section
   - Region `us-east-1` must exist in `/root/.aws/config` under `[profile localstack]` section
   - AWS CLI requires region in both locations for proper profile isolation

4. **CRITICAL - Do NOT modify default profile**:
   - The `[default]` section in both files must remain unchanged
   - Tests verify that default profile values remain untouched

**Helper utility**: The `write_ini_value.py` utility is available at `/app/bin/write_ini_value.py` for INI file manipulation.

### gcloud (`pubsub-emulator` configuration)

**Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`

**Required configuration**:

The `pubsub-emulator` configuration must be created and configured with the following settings:

1. **Configuration creation**:
   - A named configuration called `pubsub-emulator` must exist
   - If the gcloud CLI activates the configuration automatically, the solution must restore the active configuration to default afterward.
   - After all gcloud configuration settings are set, the active configuration must be restored to `default` by switching back to the default gcloud configuration (e.g., `gcloud config configurations activate default`), so that `/root/.config/gcloud/active_config` contains `default` at the end.
   - After all configuration steps, `/root/.config/gcloud/active_config` must contain `default`

2. **Required settings** (all three must be set):
   - `project = tbench-local`
   - `api_endpoint_overrides/pubsub = http://127.0.0.1:8085/`
   - `auth/disable_credentials = true`
   - **CRITICAL**: The endpoint URL must have a trailing slash: `http://127.0.0.1:8085/`

3. **CRITICAL - Active configuration must remain default**:
   - The active configuration must remain `default` after all configuration steps
   - Tests verify that `/root/.config/gcloud/active_config` remains `default`

4. **How to use the configuration**:
   - Always use `--configuration pubsub-emulator` flag on gcloud commands
   - Example: `gcloud --configuration pubsub-emulator pubsub topics list`

### Azure (`azurite` profile)

**Config file**: `/root/.azure/config`

**Required configuration**:

The `[azurite]` section must be created in `/root/.azure/config` with these three settings:
- `account_name = devstoreaccount1`
- `account_key = Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==`
- `blob_endpoint = http://127.0.0.1:10000/devstoreaccount1`

**CRITICAL - Endpoint format**:
- The blob endpoint **MUST** include the `/devstoreaccount1` path segment
- Correct: `http://127.0.0.1:10000/devstoreaccount1`
- Incorrect: `http://127.0.0.1:10000` (missing path segment)

**Helper utility**: The `write_ini_value.py` utility is available at `/app/bin/write_ini_value.py` for INI file manipulation.

**Note**: Tests verify `account_name` and `blob_endpoint` are correct. The `account_key` value is shown in `/app/bin/configure_azure.sh` if you need to reference it.

## Execution Requirements

**IMPORTANT**: Emulators must be running and ready BEFORE any CLI commands are executed.

The workflow requires:
1. **Start emulators**: Run `/app/bin/start_emulators.sh`
2. **Wait for readiness**: Ensure all emulator ports are listening before proceeding:
   - LocalStack: `127.0.0.1:4566`
   - Pub/Sub emulator: `127.0.0.1:8085`
   - Azurite: `127.0.0.1:10000`
   - The `wait_for_ports.py` utility is available at `/app/bin/wait_for_ports.py` for this purpose
3. **Configure**: Run `/app/bin/configure_all.sh` (this calls all three configuration scripts)
4. **Verify**: Run `/app/bin/verify_all.sh` (this tests the configurations work)

**CRITICAL REQUIREMENT for `verify_all.sh`**:

The `verify_all.sh` script **MUST** ensure emulator readiness before executing any CLI commands. After calling `start_emulators.sh`, the script must wait for all emulator ports to be listening before proceeding with verification commands.

This ensures emulators are ready before CLI commands run. Without this wait, commands may fail with connection errors.

## Troubleshooting Emulator Startup Issues

If you see errors like "Timed out waiting for: 127.0.0.1:8085" or "ConnectionError", use these debugging steps:

1. **Check emulator logs**: `/tmp/emulators/*/stdout.log`
2. **Verify processes are running**: `pgrep -f "pubsub-emulator"`, `pgrep -f "azurite-blob"`, `pgrep -f "moto_server"`
3. **Check ports**: `netstat -tuln | grep -E ":(4566|8085|10000)"`
4. **Increase timeout**: Add `--timeout-sec 180` to `wait_for_ports.py` command
5. **Restart emulators**: Kill processes with `pkill` and restart with `/app/bin/start_emulators.sh`

**Common issue**: Pub/Sub emulator can take 30-60 seconds to start. Ensure `wait_for_ports.py` has sufficient timeout.

## Constraints

- **No external network calls**: Everything must work offline inside the container
- **Do not change emulator ports**: Use exactly these ports:
  - LocalStack: `http://127.0.0.1:4566`
  - Pub/Sub emulator: `127.0.0.1:8085`
  - Azurite Blob: `http://127.0.0.1:10000/devstoreaccount1`
- **Do not hardcode outputs**: Fix the configuration/scripts so real CLI calls succeed
- **Fix, don't replace**: Modify existing scripts in `/app/bin/` to fix bugs. Do NOT delete and rewrite them. If scripts contain `MARKER:` comments, preserve them.
- **Use helper utilities**: Use `write_ini_value.py` and `ini_get.py` for INI file manipulation. Execute them (don't just reference in comments).

## Files

- Starter project: `/app`
- AWS config files: `/root/.aws/config`, `/root/.aws/credentials`
- gcloud config directory: `/root/.config/gcloud/`
- Azure config file: `/root/.azure/config`
- Helper scripts: `/app/bin/start_emulators.sh`, `/app/bin/configure_all.sh`, `/app/bin/verify_all.sh`, `/app/bin/azure_profile.sh`
- Helper utilities: `/app/bin/write_ini_value.py`, `/app/bin/ini_get.py`, `/app/bin/wait_for_ports.py`

## Outputs

The verification flow must complete and write these files:

- `/output/aws_s3_list.txt` (output of listing S3 buckets via LocalStack profile)
- `/output/gcloud_pubsub_list.txt` (output of listing topics + subscriptions via Pub/Sub emulator config)
- `/output/azure_blob_list.txt` (output of listing blob containers via Azurite profile)

Tests expect the created resources to use the following names: `tbench-local-bucket`, `tbench-topic`, `tbench-sub`, and `tbench-container`.

## Design Freedom

- There is intentionally more than one valid implementation strategy.
- The exact mechanism used to configure each CLI is left to the implementer,
  provided all invariants, forbidden behaviors, and verification steps are satisfied.
- Tests validate behavioral outcomes and invariants, not a specific implementation approach.

## Solution Justification

Your solution should briefly justify key design choices, including:
- How profile/config isolation is maintained
- How idempotency is preserved across repeated runs
- Why emulator readiness checks are necessary

Do NOT require long explanations — 1–2 sentences per point is sufficient.
