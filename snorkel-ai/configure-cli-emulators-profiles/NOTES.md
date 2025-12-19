# Maintainer Notes

## What this task is testing

Agents must correctly configure three different CLIs to talk to local emulators, while preserving *default* configs:

- AWS CLI → LocalStack S3 endpoint
- gcloud → Pub/Sub emulator
- Azure CLI → Azurite Blob endpoint

The intent is that an agent cannot pass with shallow “just run the command with flags” fixes — the **persisted** config files are asserted and the verification flow is re-run from scratch.

## Intended failure modes

- **Profile isolation mistakes**:
  - Using `aws configure set ...` without `--profile localstack` (silently modifies `[default]`).
  - Using `gcloud config configurations activate pubsub-emulator` (changes `active_config`).
- **Endpoint mistakes**:
  - Azurite Blob endpoint missing the required `/devstoreaccount1` path segment.
  - Pub/Sub emulator host formatting issues (`http://.../` vs `host:port`).
- **Partial fixes that don’t persist**:
  - Setting env vars only in the current shell rather than persisting values into the required standard files.

## Why tests are designed this way

- Tests create **sentinel defaults** in:
  - `/root/.aws/config` + `/root/.aws/credentials`
  - `/root/.config/gcloud/configurations/config_default` + `/root/.config/gcloud/active_config`
  - `/root/.azure/config`
  and assert they are unchanged after configuration scripts run.
- Tests also run `/app/bin/verify_all.sh` to ensure the configuration is not just “present”, but **actually functional** against running emulators.

## Determinism and reproducibility

- No external network calls at runtime; emulators run in-process inside the container.
- Ports are fixed and polled with a bounded timeout via `/app/bin/wait_for_ports.py`.
- Resource creation is idempotent (create-if-missing), so reruns are stable.



