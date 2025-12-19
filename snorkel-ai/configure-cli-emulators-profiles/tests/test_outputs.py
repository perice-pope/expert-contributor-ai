"""Behavioral tests for local-emulator CLI profile configuration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def sh(*cmd: str, env: dict[str, str] | None = None) -> str:
    """Run a command and return stdout (raises on failure)."""
    p = subprocess.run(
        list(cmd),
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return p.stdout


def write_text(path: str, content: str) -> None:
    """Write file content, creating parent dirs."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_text(path: str) -> str:
    """Read file content (utf-8)."""
    return Path(path).read_text(encoding="utf-8")


def ensure_emulators() -> None:
    """Start emulators with bounded waits (idempotent)."""
    sh("bash", "/app/bin/start_emulators.sh")


def seed_defaults() -> None:
    """Create sentinel defaults that must not be modified by the task."""
    # AWS defaults
    write_text(
        "/root/.aws/credentials",
        "[default]\naws_access_key_id = defaultkey\naws_secret_access_key = defaultsecret\n",
    )
    write_text(
        "/root/.aws/config",
        "[default]\nregion = us-west-2\noutput = json\n",
    )

    # gcloud defaults
    Path("/root/.config/gcloud/configurations").mkdir(parents=True, exist_ok=True)
    write_text(
        "/root/.config/gcloud/configurations/config_default",
        "[core]\nproject = default-project\n",
    )
    write_text("/root/.config/gcloud/active_config", "default\n")

    # Azure defaults
    write_text("/root/.azure/config", "[core]\nfoo = bar\n")


def test_profiles_do_not_clobber_defaults():
    """Named profiles/configs must be created without mutating defaults."""
    ensure_emulators()
    seed_defaults()

    sh("bash", "/app/bin/configure_all.sh")

    # AWS default should be unchanged.
    assert "aws_access_key_id = defaultkey" in read_text("/root/.aws/credentials")
    assert "region = us-west-2" in read_text("/root/.aws/config")

    # gcloud default should be unchanged, and active config must remain default.
    assert "project = default-project" in read_text(
        "/root/.config/gcloud/configurations/config_default"
    )
    assert read_text("/root/.config/gcloud/active_config").strip() == "default"

    # Azure default section should be unchanged.
    assert "foo = bar" in read_text("/root/.azure/config")


def test_persisted_config_files_exist_and_look_right():
    """The required standard config files must exist and include required values."""
    ensure_emulators()
    seed_defaults()

    sh("bash", "/app/bin/configure_all.sh")

    # AWS: credentials for named profile + custom endpoint in config.
    creds = read_text("/root/.aws/credentials")
    assert "[localstack]" in creds
    assert "aws_access_key_id" in creds
    assert "aws_secret_access_key" in creds

    cfg = read_text("/root/.aws/config")
    assert "profile localstack" in cfg
    assert "s3.endpoint_url" in cfg
    assert "127.0.0.1:4566" in cfg

    # gcloud: named configuration file exists with project + endpoint override.
    gcfg = read_text("/root/.config/gcloud/configurations/config_pubsub-emulator")
    assert "project = tbench-local" in gcfg
    # gcloud stores api_endpoint_overrides/pubsub as [api_endpoint_overrides] section with pubsub key
    assert "[api_endpoint_overrides]" in gcfg
    assert "pubsub = http://127.0.0.1:8085/" in gcfg

    # Azure: named "azurite" profile stored in config with a blob endpoint.
    azcfg = read_text("/root/.azure/config")
    assert "[azurite]" in azcfg
    assert "account_name = devstoreaccount1" in azcfg
    assert "blob_endpoint = http://127.0.0.1:10000/devstoreaccount1" in azcfg


def test_end_to_end_create_and_list_resources():
    """Verification flow must create + list resources against all emulators."""
    ensure_emulators()
    seed_defaults()

    sh("bash", "/app/bin/configure_all.sh")
    sh("bash", "/app/bin/verify_all.sh")

    aws_out = Path("/output/aws_s3_list.txt")
    gcloud_out = Path("/output/gcloud_pubsub_list.txt")
    azure_out = Path("/output/azure_blob_list.txt")

    assert aws_out.exists()
    assert gcloud_out.exists()
    assert azure_out.exists()

    # AWS list-buckets output is JSON.
    aws_data = json.loads(aws_out.read_text(encoding="utf-8"))
    bucket_names = {b["Name"] for b in aws_data.get("Buckets", [])}
    assert "tbench-local-bucket" in bucket_names

    gcloud_txt = gcloud_out.read_text(encoding="utf-8")
    assert "tbench-topic" in gcloud_txt
    assert "tbench-sub" in gcloud_txt

    # Azure container list output is JSON array.
    azure_data = json.loads(azure_out.read_text(encoding="utf-8"))
    container_names = {c["name"] for c in azure_data}
    assert "tbench-container" in container_names



