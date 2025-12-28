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

### gcloud (`pubsub-emulator` configuration)
- **Config file**: `/root/.config/gcloud/configurations/config_pubsub-emulator`
- **Project name**: `tbench-local`
- **Required settings**:
  - Project must be set to `tbench-local`
  - Pub/Sub API endpoint must be overridden to `http://127.0.0.1:8085/`
- **⚠️ CRITICAL - DO NOT ACTIVATE**: 
  - **Never run** `gcloud config configurations activate pubsub-emulator`
  - The file `/root/.config/gcloud/active_config` must remain set to `default`
  - **How to configure without activating**: 
    1. Create the configuration: `gcloud config configurations create pubsub-emulator` (this does NOT activate by default)
    2. Set configuration values using the `--configuration` flag: `gcloud --configuration pubsub-emulator config set <property> <value>`
    3. **Do NOT use** `gcloud config configurations activate` - this will change the active configuration
    4. **Do NOT use** `gcloud config set` without `--configuration` flag - this modifies the active configuration
    5. Verify `/root/.config/gcloud/active_config` remains `default` after all configuration steps
  - **How to use**: Always use `--configuration pubsub-emulator` flag on all gcloud commands (e.g., `gcloud --configuration pubsub-emulator pubsub topics list`)

## Constraints

- **No external network calls**. Everything must work offline inside the container.
- **Do not change the emulator ports**. The environment assumes:
  - LocalStack: `http://127.0.0.1:4566`
  - Pub/Sub emulator: `127.0.0.1:8085`
  - Azurite Blob: `http://127.0.0.1:10000/devstoreaccount1`
- **Do not hardcode “pass” outputs**. Fix the configuration/scripts so the real CLI calls succeed.

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

## Outputs

The verification flow must complete and write logs:

- `/output/aws_s3_list.txt` (text; output of listing S3 buckets via LocalStack profile)
- `/output/gcloud_pubsub_list.txt` (text; output of listing topics + subscriptions via Pub/Sub emulator config)
- `/output/azure_blob_list.txt` (text; output of listing blob containers via Azurite profile)



