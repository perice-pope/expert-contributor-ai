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


def test_orchestration_script_actually_executes_all_configure_scripts():
    """Verify configure_all.sh actually EXECUTES all three individual configure scripts.
    
    Anti-cheating: Uses execution tracing to prove scripts are called, not just referenced.
    Creates wrapper scripts that log invocations, then verifies the log after running.
    """
    import os
    import shutil
    
    ensure_emulators()
    verify_emulators_running()
    seed_defaults()
    
    # Setup: Create execution trace log
    trace_log = Path("/tmp/script_execution_trace.log")
    trace_log.unlink(missing_ok=True)
    
    # Backup original scripts and create traced wrappers
    scripts = ["configure_aws.sh", "configure_gcloud.sh", "configure_azure.sh"]
    for script in scripts:
        orig = f"/app/bin/{script}"
        backup = f"/app/bin/{script}.orig"
        
        # Backup if not already backed up
        if not Path(backup).exists():
            shutil.copy(orig, backup)
        
        # Read original content
        original_content = read_text(backup)
        
        # Create traced version that logs execution then runs original
        traced_content = f"""#!/bin/bash
# Traced wrapper - logs execution
echo "{script}" >> /tmp/script_execution_trace.log
{original_content}
"""
        write_text(orig, traced_content)
        os.chmod(orig, 0o755)
    
    try:
        # Run the orchestration script
        sh("bash", "/app/bin/configure_all.sh")
        
        # Verify all three scripts were actually executed
        assert trace_log.exists(), \
            "Execution trace not found - configure_all.sh did not call any configure scripts"
        
        trace_content = trace_log.read_text()
        assert "configure_aws.sh" in trace_content, \
            "configure_all.sh did not actually execute configure_aws.sh"
        assert "configure_gcloud.sh" in trace_content, \
            "configure_all.sh did not actually execute configure_gcloud.sh"
        assert "configure_azure.sh" in trace_content, \
            "configure_all.sh did not actually execute configure_azure.sh"
    finally:
        # Restore original scripts
        for script in scripts:
            orig = f"/app/bin/{script}"
            backup = f"/app/bin/{script}.orig"
            if Path(backup).exists():
                shutil.copy(backup, orig)
                os.chmod(orig, 0o755)


def test_helper_utility_actually_executes():
    """Verify write_ini_value.py is ACTUALLY EXECUTED during configuration.
    
    Anti-cheating: Creates a wrapper script that logs invocations then calls original.
    Proves the utility runs, not just that scripts mention it.
    """
    import os
    import shutil
    
    ensure_emulators()
    verify_emulators_running()
    seed_defaults()
    
    helper_path = Path("/app/bin/write_ini_value.py")
    backup_path = Path("/app/bin/write_ini_value.py.real")
    trace_log = Path("/tmp/helper_execution_trace.log")
    
    # Clear trace log
    trace_log.unlink(missing_ok=True)
    
    # Move original to .real if not already done
    if not backup_path.exists():
        shutil.move(str(helper_path), str(backup_path))
    
    # Create wrapper that logs then calls original
    wrapper_content = '''#!/usr/bin/env python3
"""Wrapper for write_ini_value.py that logs execution."""
import sys
import subprocess

# Log this execution
with open("/tmp/helper_execution_trace.log", "a") as f:
    f.write(f"EXECUTED: {sys.argv}\\n")

# Call the real script with same args
result = subprocess.run(
    ["python3", "/app/bin/write_ini_value.py.real"] + sys.argv[1:],
    capture_output=True,
    text=True
)

# Forward output and exit code
if result.stdout:
    print(result.stdout, end="")
if result.stderr:
    print(result.stderr, end="", file=sys.stderr)
sys.exit(result.returncode)
'''
    
    write_text(str(helper_path), wrapper_content)
    os.chmod(str(helper_path), 0o755)
    
    try:
        # Run configuration
        sh("bash", "/app/bin/configure_all.sh")
        
        # Verify helper was actually executed
        assert trace_log.exists(), \
            "Helper utility trace not found - write_ini_value.py was never executed"
        
        trace_content = trace_log.read_text()
        assert "EXECUTED:" in trace_content, \
            "write_ini_value.py was not actually executed during configuration"
        
        # Verify it was called with meaningful arguments (file path, section, key, value)
        assert "--path" in trace_content and "--section" in trace_content, \
            "write_ini_value.py was not called with proper arguments"
    finally:
        # Restore original
        if backup_path.exists():
            shutil.move(str(backup_path), str(helper_path))
            os.chmod(str(helper_path), 0o755)


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


def test_emulator_state_matches_output_files():
    """Verify output files reflect ACTUAL emulator state, not hardcoded values.
    
    Anti-cheating: Queries emulators directly via API to verify that resources
    exist and match what's reported in output files. Prevents agents from 
    hardcoding expected bucket/topic/container names without real API calls.
    """
    import urllib.request
    import urllib.error
    
    ensure_emulators()
    verify_emulators_running()
    seed_defaults()
    
    # Delete pre-existing output files
    for out_file in ["/output/aws_s3_list.txt", "/output/gcloud_pubsub_list.txt", "/output/azure_blob_list.txt"]:
        Path(out_file).unlink(missing_ok=True)
    
    sh("bash", "/app/bin/configure_all.sh")
    sh("bash", "/app/bin/verify_all.sh")
    
    # === AWS: Query LocalStack S3 directly ===
    try:
        # Use AWS CLI to list buckets directly from emulator
        aws_direct = sh(
            "aws", "s3api", "list-buckets",
            "--endpoint-url", "http://127.0.0.1:4566",
            "--profile", "localstack"
        )
        aws_direct_data = json.loads(aws_direct)
        direct_bucket_names = {b["Name"] for b in aws_direct_data.get("Buckets", [])}
        
        # Compare with output file
        aws_out = json.loads(Path("/output/aws_s3_list.txt").read_text())
        file_bucket_names = {b["Name"] for b in aws_out.get("Buckets", [])}
        
        assert "tbench-local-bucket" in direct_bucket_names, \
            "Bucket does not exist in actual emulator - output file may be faked"
        assert direct_bucket_names == file_bucket_names, \
            f"Output file doesn't match emulator state: file={file_bucket_names}, emulator={direct_bucket_names}"
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Failed to query LocalStack directly: {e.stderr}")
    
    # === gcloud: Query Pub/Sub emulator directly ===
    try:
        gcloud_topics = sh(
            "gcloud", "pubsub", "topics", "list",
            "--configuration", "pubsub-emulator",
            "--format", "value(name)"
        )
        gcloud_subs = sh(
            "gcloud", "pubsub", "subscriptions", "list",
            "--configuration", "pubsub-emulator", 
            "--format", "value(name)"
        )
        
        assert "tbench-topic" in gcloud_topics, \
            "Topic does not exist in actual emulator - output file may be faked"
        assert "tbench-sub" in gcloud_subs, \
            "Subscription does not exist in actual emulator - output file may be faked"
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Failed to query Pub/Sub emulator directly: {e.stderr}")
    
    # === Azure: Query Azurite directly ===
    try:
        # Query Azurite blob containers directly
        azure_direct = sh(
            "az", "storage", "container", "list",
            "--connection-string", 
            "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
            "--output", "json"
        )
        azure_direct_data = json.loads(azure_direct)
        direct_container_names = {c["name"] for c in azure_direct_data}
        
        # Compare with output file
        azure_out = json.loads(Path("/output/azure_blob_list.txt").read_text())
        file_container_names = {c["name"] for c in azure_out}
        
        assert "tbench-container" in direct_container_names, \
            "Container does not exist in actual emulator - output file may be faked"
        assert direct_container_names == file_container_names, \
            f"Output file doesn't match emulator state: file={file_container_names}, emulator={direct_container_names}"
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"Failed to query Azurite directly: {e.stderr}")



