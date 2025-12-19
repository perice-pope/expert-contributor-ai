# Dev tooling (task author)

## Install Harbor CLI (pinned)

From repo root:

```bash
bash dev/setup_harbor.sh
```

If `harbor` is not found afterwards, add your Python user-bin to `PATH`:

```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
```

Confirm:

```bash
harbor --help
harbor tasks --help
```

## Note on Docker

Harbor’s `tasks start-env` / `run` flows use Docker under the hood. Make sure Docker Desktop is installed and running on macOS.

Quick preflight:

```bash
bash dev/check_docker.sh
```


