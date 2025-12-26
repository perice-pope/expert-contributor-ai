# Local Cloud CLI Profiles (Starter Project)

This repo is meant to run **offline** against local emulators:

- LocalStack (S3): `http://127.0.0.1:4566`
- Pub/Sub emulator: `127.0.0.1:8085`
- Azurite (Blob): `http://127.0.0.1:10000/devstoreaccount1`

The expected workflow is:

1. Start emulators:
   - `/app/bin/start_emulators.sh`
2. Configure profiles/configurations:
   - `/app/bin/configure_all.sh`
3. Validate by creating + listing resources (writes to `/output/*.txt`):
   - `/app/bin/verify_all.sh`

If something fails, your best friend is: `bash -x /app/bin/verify_all.sh`



