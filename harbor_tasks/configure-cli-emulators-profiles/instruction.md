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

**Step-by-step configuration process**:

1. **Set credentials in `/root/.aws/credentials`**:
   - Create section `[localstack]` with these three lines:
     - `aws_access_key_id = test`
     - `aws_secret_access_key = test`
     - `region = us-east-1`
   - **Method**: Use `aws configure set` commands with `--profile localstack` flag:
     ```bash
     aws configure set aws_access_key_id "test" --profile localstack
     aws configure set aws_secret_access_key "test" --profile localstack
     aws configure set region "us-east-1" --profile localstack
     ```
   - **CRITICAL**: You **MUST** include `--profile localstack` on every `aws configure set` command. Without this flag, the command modifies `[default]` instead of `[localstack]`.

2. **Set configuration in `/root/.aws/config`**:
   - Create section `[profile localstack]` with these two settings:
     - `s3.endpoint_url = http://127.0.0.1:4566`
     - `region = us-east-1`
   - **Method**: Use `write_ini_value.py` utility:
     ```bash
     python3 /app/bin/write_ini_value.py --path /root/.aws/config --section "profile localstack" --key "s3.endpoint_url" --value "http://127.0.0.1:4566"
     python3 /app/bin/write_ini_value.py --path /root/.aws/config --section "profile localstack" --key "region" --value "us-east-1"
     ```

3. **CRITICAL - Region must be in BOTH files**:
   - Region `us-east-1` must exist in `/root/.aws/credentials` under `[localstack]` section
   - Region `us-east-1` must exist in `/root/.aws/config` under `[profile localstack]` section
   - AWS CLI requires region in both locations for proper profile isolation

4. **CRITICAL - Do NOT modify default profile**:
   - The `[default]` section in both files must remain unchanged
   - Never run `aws configure set` without the `--profile localstack` flag
   - Tests verify that default profile values remain untouched

### gcloud (`pubsub-emulator` configuration)

**Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`

**Step-by-step configuration process**:

1. **Create the configuration** (do NOT activate it):
   ```bash
   gcloud config configurations create pubsub-emulator --no-activate
   ```
   - The `--no-activate` flag is **REQUIRED** - without it, the new configuration becomes active and changes `/root/.config/gcloud/active_config`
   - After creation, verify `/root/.config/gcloud/active_config` still contains `default`

2. **Set all three required settings** (use `--configuration` flag on every command):
   ```bash
   gcloud --configuration pubsub-emulator config set project tbench-local
   gcloud --configuration pubsub-emulator config set api_endpoint_overrides/pubsub http://127.0.0.1:8085/
   gcloud --configuration pubsub-emulator config set auth/disable_credentials true
   ```
   - **CRITICAL**: You **MUST** set all three settings. Missing any one will cause failures.
   - **CRITICAL**: You **MUST** use `--configuration pubsub-emulator` flag on every `gcloud config set` command
   - **CRITICAL**: The endpoint URL must have a trailing slash: `http://127.0.0.1:8085/`

3. **Verify active configuration remains default**:
   - After all configuration steps, check: `cat /root/.config/gcloud/active_config`
   - This file must contain exactly: `default`
   - If it contains `pubsub-emulator`, you activated the configuration (this is wrong)

4. **CRITICAL - Never activate the configuration**:
   - **DO NOT** run: `gcloud config configurations activate pubsub-emulator`
   - **DO NOT** use `gcloud config set` without `--configuration` flag
   - Tests verify that `/root/.config/gcloud/active_config` remains `default`

5. **How to use the configuration**:
   - Always use `--configuration pubsub-emulator` flag on gcloud commands
   - Example: `gcloud --configuration pubsub-emulator pubsub topics list`

### Azure (`azurite` profile)

**Config file**: `/root/.azure/config`

**Step-by-step configuration process**:

1. **Create the `[azurite]` section** in `/root/.azure/config` with these three settings:
   - `account_name = devstoreaccount1`
   - `account_key = Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==`
   - `blob_endpoint = http://127.0.0.1:10000/devstoreaccount1`

2. **Method**: Use `write_ini_value.py` utility for each setting:
   ```bash
   python3 /app/bin/write_ini_value.py --path /root/.azure/config --section "azurite" --key "account_name" --value "devstoreaccount1"
   python3 /app/bin/write_ini_value.py --path /root/.azure/config --section "azurite" --key "account_key" --value "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
   python3 /app/bin/write_ini_value.py --path /root/.azure/config --section "azurite" --key "blob_endpoint" --value "http://127.0.0.1:10000/devstoreaccount1"
   ```

3. **CRITICAL - Endpoint format**:
   - The blob endpoint **MUST** include the `/devstoreaccount1` path segment
   - Correct: `http://127.0.0.1:10000/devstoreaccount1`
   - Incorrect: `http://127.0.0.1:10000` (missing path segment)

4. **Note**: Tests verify `account_name` and `blob_endpoint` are correct. The `account_key` value is shown in `/app/bin/configure_azure.sh` if you need to reference it.

## Execution Order

**IMPORTANT**: Emulators must be running and ready BEFORE any CLI commands are executed.

1. **Start emulators**: Run `/app/bin/start_emulators.sh`
2. **Wait for readiness**: Run `wait_for_ports.py` to ensure all ports are listening:
   ```bash
   python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000
   ```
3. **Configure**: Run `/app/bin/configure_all.sh` (this calls all three configuration scripts)
4. **Verify**: Run `/app/bin/verify_all.sh` (this tests the configurations work)

**CRITICAL REQUIREMENT for `verify_all.sh`**:

The `verify_all.sh` script **MUST** call `wait_for_ports.py` after starting emulators and before executing any CLI commands. Add this code after the line that calls `start_emulators.sh`:

```bash
/app/bin/start_emulators.sh >/dev/null
python3 /app/bin/wait_for_ports.py --tcp 127.0.0.1:4566 --tcp 127.0.0.1:8085 --tcp 127.0.0.1:10000 --timeout-sec 60 || echo "[verify] warning: some emulators may not be ready, continuing anyway..."
```

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
