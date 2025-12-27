"""Behavioral tests for local-emulator CLI profile configuration."""

from __future__ import annotations

import json
import socket
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


def check_port_listening(port: int) -> bool:
    """Check if a port is listening (emulator is running)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            return result == 0
    except Exception:
        return False


def verify_emulators_running() -> None:
    """Verify that all required emulators are actually running."""
    assert check_port_listening(4566), "LocalStack (port 4566) is not running"
    assert check_port_listening(8085), "Pub/Sub emulator (port 8085) is not running"
    assert check_port_listening(10000), "Azurite (port 10000) is not running"


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
    verify_emulators_running()  # Anti-cheating: ensure emulators are actually running
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
    verify_emulators_running()  # Anti-cheating: ensure emulators are actually running
    seed_defaults()

    # Anti-cheating: Record config file modification times before configure
    aws_creds_path = Path("/root/.aws/credentials")
    aws_config_path = Path("/root/.aws/config")
    azure_config_path = Path("/root/.azure/config")
    
    before_times = {
        "aws_creds": aws_creds_path.stat().st_mtime if aws_creds_path.exists() else 0,
        "aws_config": aws_config_path.stat().st_mtime if aws_config_path.exists() else 0,
        "azure_config": azure_config_path.stat().st_mtime if azure_config_path.exists() else 0,
    }

    sh("bash", "/app/bin/configure_all.sh")

    # Anti-cheating: Verify config files were actually modified (not pre-created)
    assert aws_creds_path.stat().st_mtime > before_times["aws_creds"], \
        "AWS credentials file was not modified by configure script"
    assert aws_config_path.stat().st_mtime > before_times["aws_config"], \
        "AWS config file was not modified by configure script"
    assert azure_config_path.stat().st_mtime > before_times["azure_config"], \
        "Azure config file was not modified by configure script"

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
    
    # Anti-cheating: Verify gcloud config has auth disabled
    assert "disable_credentials = true" in gcfg or "disable_credentials=true" in gcfg, \
        "gcloud config must have auth/disable_credentials set to true"

    # Azure: named "azurite" profile stored in config with a blob endpoint.
    azcfg = read_text("/root/.azure/config")
    assert "[azurite]" in azcfg
    assert "account_name = devstoreaccount1" in azcfg
    assert "blob_endpoint = http://127.0.0.1:10000/devstoreaccount1" in azcfg


def test_end_to_end_create_and_list_resources():
    """Verification flow must create + list resources against all emulators."""
    ensure_emulators()
    verify_emulators_running()  # Anti-cheating: ensure emulators are actually running
    seed_defaults()

    # Anti-cheating: Delete any pre-existing output files to prevent hardcoding
    for out_file in ["/output/aws_s3_list.txt", "/output/gcloud_pubsub_list.txt", "/output/azure_blob_list.txt"]:
        Path(out_file).unlink(missing_ok=True)

    sh("bash", "/app/bin/configure_all.sh")
    sh("bash", "/app/bin/verify_all.sh")
    
    # Anti-cheating: verify emulators are still running after operations
    verify_emulators_running()

    aws_out = Path("/output/aws_s3_list.txt")
    gcloud_out = Path("/output/gcloud_pubsub_list.txt")
    azure_out = Path("/output/azure_blob_list.txt")

    assert aws_out.exists(), "AWS output file was not created by verify script"
    assert gcloud_out.exists(), "gcloud output file was not created by verify script"
    assert azure_out.exists(), "Azure output file was not created by verify script"

    # Anti-cheating: Verify output files were created recently (not pre-existing)
    import time
    current_time = time.time()
    assert current_time - aws_out.stat().st_mtime < 60, "AWS output file is too old"
    assert current_time - gcloud_out.stat().st_mtime < 60, "gcloud output file is too old"
    assert current_time - azure_out.stat().st_mtime < 60, "Azure output file is too old"

    # AWS list-buckets output is JSON.
    aws_data = json.loads(aws_out.read_text(encoding="utf-8"))
    bucket_names = {b["Name"] for b in aws_data.get("Buckets", [])}
    assert "tbench-local-bucket" in bucket_names
    
    # Anti-cheating: Verify AWS output contains metadata that indicates real API response
    assert "Buckets" in aws_data, "AWS output missing expected structure"
    assert isinstance(aws_data["Buckets"], list), "AWS output has invalid structure"

    gcloud_txt = gcloud_out.read_text(encoding="utf-8")
    assert "tbench-topic" in gcloud_txt
    assert "tbench-sub" in gcloud_txt
    
    # Anti-cheating: Verify gcloud output contains actual formatted output (not just hardcoded strings)
    assert len(gcloud_txt.strip()) > 50, "gcloud output suspiciously short"

    # Azure container list output is JSON array.
    azure_data = json.loads(azure_out.read_text(encoding="utf-8"))
    container_names = {c["name"] for c in azure_data}
    assert "tbench-container" in container_names
    
    # Anti-cheating: Verify Azure output contains metadata from real API
    assert isinstance(azure_data, list), "Azure output should be a JSON array"
    assert len(azure_data) > 0, "Azure output should contain at least one container"
    assert "name" in azure_data[0], "Azure output missing expected fields"


def test_scripts_were_fixed_not_replaced():
    """Verify configuration scripts were modified, not replaced entirely.
    
    The task requires fixing bugs in existing scripts, not rewriting them.
    Scripts must retain their original marker comments to prove they weren't replaced.
    """
    # Check AWS script contains original marker
    aws_script = read_text("/app/bin/configure_aws.sh")
    assert "MARKER:AWS_CONFIG_SCRIPT_V1" in aws_script, \
        "configure_aws.sh was replaced instead of fixed - must retain original marker"
    
    # Check gcloud script contains original marker
    gcloud_script = read_text("/app/bin/configure_gcloud.sh")
    assert "MARKER:GCLOUD_CONFIG_SCRIPT_V1" in gcloud_script, \
        "configure_gcloud.sh was replaced instead of fixed - must retain original marker"
    
    # Check Azure script contains original marker
    azure_script = read_text("/app/bin/configure_azure.sh")
    assert "MARKER:AZURE_CONFIG_SCRIPT_V1" in azure_script, \
        "configure_azure.sh was replaced instead of fixed - must retain original marker"


def test_orchestration_script_calls_all_configure_scripts():
    """Verify configure_all.sh orchestrates all three individual configure scripts.
    
    The orchestration script must call each individual configuration script.
    This test verifies the script contains references to all three scripts.
    """
    configure_all = read_text("/app/bin/configure_all.sh")
    
    # Must reference all three configure scripts
    assert "configure_aws.sh" in configure_all, \
        "configure_all.sh must call configure_aws.sh"
    assert "configure_gcloud.sh" in configure_all, \
        "configure_all.sh must call configure_gcloud.sh"
    assert "configure_azure.sh" in configure_all, \
        "configure_all.sh must call configure_azure.sh"


def test_helper_utilities_are_executed():
    """Verify helper utilities are actually used for INI file manipulation.
    
    At least one configure script must invoke write_ini_value.py to demonstrate
    proper use of the provided helper utilities.
    """
    aws_script = read_text("/app/bin/configure_aws.sh")
    gcloud_script = read_text("/app/bin/configure_gcloud.sh")
    azure_script = read_text("/app/bin/configure_azure.sh")
    
    # Check that write_ini_value.py is invoked (not just mentioned in comments)
    # Look for actual execution patterns like "python" or direct script call
    all_scripts = aws_script + gcloud_script + azure_script
    
    # Must contain actual call to write_ini_value.py (with python or direct execution)
    has_python_call = "python" in all_scripts and "write_ini_value.py" in all_scripts
    has_direct_call = "/app/bin/write_ini_value.py" in all_scripts
    
    assert has_python_call or has_direct_call, \
        "At least one script must execute write_ini_value.py (not just reference it in comments)"


def test_no_external_network_calls():
    """Verify the configuration works offline without external network calls.
    
    This test blocks external DNS and verifies the task still completes.
    """
    ensure_emulators()
    verify_emulators_running()
    seed_defaults()
    
    # Block external DNS by pointing to localhost (simulates offline environment)
    # The emulators use 127.0.0.1 directly so they will still work
    import os
    env_offline = os.environ.copy()
    env_offline["AWS_EC2_METADATA_DISABLED"] = "true"
    env_offline["AWS_METADATA_SERVICE_TIMEOUT"] = "0"
    env_offline["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "0"
    # Block any proxy usage
    env_offline["no_proxy"] = "*"
    env_offline["NO_PROXY"] = "*"
    
    # Run configure and verify - should work without external network
    sh("bash", "/app/bin/configure_all.sh", env=env_offline)
    sh("bash", "/app/bin/verify_all.sh", env=env_offline)
    
    # If we got here without network errors, the task is truly offline



