# Configure Cloud CLIs for Local Emulators  

You've joined a team that runs integration tests fully offline using local emulators. The repo contains incomplete configuration scripts that have bugs preventing proper profile isolation.

## Task

Fix the CLI configuration scripts so that all three cloud tools (AWS, gcloud, Azure) can work with their respective local emulators using named profiles/configurations - without affecting existing default configurations.

**Named profiles to create:**
- AWS: `localstack`
- gcloud: `pubsub-emulator`
- Azure: `azurite`

**Emulator endpoints** (do not change these):
- LocalStack S3: port 4566
- Pub/Sub emulator: port 8085  
- Azurite Blob: port 10000

## Critical Requirements

1. **Profile isolation**: Default profiles must remain untouched (tests will verify)
2. **Persistence**: Configurations must survive shell restarts
3. **Orchestration**: You must coordinate all three configurations (no master script provided)
4. **Format compliance**: Each tool has specific config file format requirements

## Constraints

- Offline only (no external network)
- Fix existing scripts in `/app/bin/` - do not replace them entirely
- Use provided helper utilities appropriately
- The verification script requires all configurations working together

## Files

- Starter project: `/app`
- Individual configuration scripts exist for AWS, gcloud, and Azure under `/app/bin/`
- Config file locations:
  - AWS: `/root/.aws/config` and `/root/.aws/credentials` (INI format with specific section naming)
  - gcloud: `/root/.config/gcloud/configurations/config_<name>` (custom format)
  - Azure: `/root/.azure/config` (INI format)
- Helper utilities: `/app/bin/write_ini_value.py`, `/app/bin/ini_get.py`, `/app/bin/wait_for_ports.py`
- Verification: `/app/bin/verify_all.sh`

## Outputs

The verification flow must complete and write logs:

- `/output/aws_s3_list.txt` (text; output of listing S3 buckets via LocalStack profile)
- `/output/gcloud_pubsub_list.txt` (text; output of listing topics + subscriptions via Pub/Sub emulator config)
- `/output/azure_blob_list.txt` (text; output of listing blob containers via Azurite profile)



