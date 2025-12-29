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
    
    # Capture initial state to verify changes were made
    initial_creds = read_text("/root/.aws/credentials")
    initial_config = read_text("/root/.aws/config")
    initial_gcloud_active = read_text("/root/.config/gcloud/active_config").strip()

    # Note: configure_all.sh may have already been run by the agent (Oracle runs it)
    # But for NOP agent, scripts remain buggy. The test_anti_cheating_scripts_were_fixed()
    # test will catch if scripts weren't fixed by the agent.
    sh("bash", "/app/bin/configure_all.sh")
    
    # Verify files were actually modified (anti-cheating: ensure work was done)
    final_creds = read_text("/root/.aws/credentials")
    final_config = read_text("/root/.aws/config")
    assert final_creds != initial_creds, "AWS credentials must be modified (profile created)"
    assert final_config != initial_config, "AWS config must be modified (profile created)"

    # AWS default should be unchanged.
    # CRITICAL: Check that [default] section specifically has defaultkey (not just that string exists anywhere)
    creds_content = read_text("/root/.aws/credentials")
    # Parse to verify [default] section specifically
    in_default_section = False
    default_has_correct_key = False
    for line in creds_content.split('\n'):
        line = line.strip()
        if line == '[default]':
            in_default_section = True
        elif line.startswith('[') and line.endswith(']'):
            in_default_section = False
        elif in_default_section and line.startswith('aws_access_key_id'):
            if 'defaultkey' in line:
                default_has_correct_key = True
            else:
                # Default section was modified - this is the bug!
                assert False, f"Default AWS profile was modified! Found '{line}' in [default] section, expected 'aws_access_key_id = defaultkey'"
    assert default_has_correct_key, "Default AWS profile [default] section must contain 'aws_access_key_id = defaultkey'"
    
    # Also verify [localstack] section exists (anti-cheating: ensure named profile was created)
    assert "[localstack]" in creds_content, "Named profile [localstack] must exist in credentials file"
    
    config_content = read_text("/root/.aws/config")
    assert "region = us-west-2" in config_content, "Default AWS config must not be modified"
    # Verify [default] section in config is unchanged
    in_default_config = False
    for line in config_content.split('\n'):
        line = line.strip()
        if line == '[default]':
            in_default_config = True
        elif line.startswith('[') and line.endswith(']'):
            in_default_config = False
        elif in_default_config and 'region' in line.lower():
            assert 'us-west-2' in line, f"Default config region was modified! Found '{line}', expected 'region = us-west-2'"

    # gcloud default should be unchanged, and active config must remain default.
    final_gcloud_active = read_text("/root/.config/gcloud/active_config").strip()
    assert final_gcloud_active == "default", f"Active gcloud config must remain 'default', got '{final_gcloud_active}'"
    assert final_gcloud_active == initial_gcloud_active, "Active gcloud config must not change"
    assert "project = default-project" in read_text(
        "/root/.config/gcloud/configurations/config_default"
    ), "Default gcloud configuration must not be modified"

    # Azure default section should be unchanged.
    final_azure = read_text("/root/.azure/config")
    assert "foo = bar" in final_azure, "Azure default section must not be modified"
    # Verify [core] section still exists and wasn't replaced
    assert "[core]" in final_azure, "Azure [core] section must still exist"


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
    # Region must be in config file for proper profile isolation (not just in credentials)
    # Check that region exists in the localstack profile section (can be in various formats)
    assert "region" in cfg, "Region must be set in config file for localstack profile"
    # Region value should be us-east-1 (the configured region)
    region_found = False
    for line in cfg.split('\n'):
        if 'region' in line.lower() and 'us-east-1' in line:
            region_found = True
            break
    assert region_found, "Region must be set to us-east-1 in config file for localstack profile"

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


def test_verify_all_sh_invokes_wait_for_ports():
    """verify_all.sh MUST call wait_for_ports.py after starting emulators."""
    verify_script = read_text("/app/bin/verify_all.sh")
    
    # Must call wait_for_ports.py after start_emulators.sh
    assert "wait_for_ports.py" in verify_script, "verify_all.sh must call wait_for_ports.py"
    assert "start_emulators.sh" in verify_script, "verify_all.sh must call start_emulators.sh"
    
    # Verify the order: start_emulators.sh should come before wait_for_ports.py
    start_pos = verify_script.find("start_emulators.sh")
    wait_pos = verify_script.find("wait_for_ports.py")
    assert start_pos < wait_pos, "wait_for_ports.py must be called after start_emulators.sh"
    
    # Verify it checks the correct ports
    assert "127.0.0.1:4566" in verify_script, "Must wait for LocalStack port 4566"
    assert "127.0.0.1:8085" in verify_script, "Must wait for Pub/Sub emulator port 8085"
    assert "127.0.0.1:10000" in verify_script, "Must wait for Azurite port 10000"
    
    # Anti-cheating: Verify wait_for_ports.py is actually executed (not just in a comment)
    # Check that it's on a line that would be executed (not commented out)
    lines = verify_script.split('\n')
    wait_line_found = False
    for i, line in enumerate(lines):
        if 'wait_for_ports.py' in line and not line.strip().startswith('#'):
            # Check it's part of an executable command (python3, bash, etc.)
            if any(cmd in line for cmd in ['python3', 'bash', 'sh', 'exec']):
                wait_line_found = True
                break
    assert wait_line_found, "wait_for_ports.py must be in an executable command, not just a comment"


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


def test_anti_cheating_wrapper_scripts_actually_used():
    """Anti-cheating: Verify wrapper scripts are used (they read config files)."""
    ensure_emulators()
    seed_defaults()
    sh("bash", "/app/bin/configure_all.sh")
    
    # Verify wrapper scripts exist and are executable
    assert Path("/app/bin/aws_localstack.sh").exists()
    assert Path("/app/bin/gcloud_pubsub.sh").exists()
    assert Path("/app/bin/azure_profile.sh").exists()
    
    # Verify wrapper scripts read from config files (not hardcoded)
    aws_wrapper = read_text("/app/bin/aws_localstack.sh")
    assert "ini_get.py" in aws_wrapper, "aws_localstack.sh must read config via ini_get.py"
    assert "profile ${AWS_PROFILE_NAME}" in aws_wrapper or "profile localstack" in aws_wrapper
    
    gcloud_wrapper = read_text("/app/bin/gcloud_pubsub.sh")
    assert "ini_get.py" in gcloud_wrapper, "gcloud_pubsub.sh must read config via ini_get.py"
    
    azure_wrapper = read_text("/app/bin/azure_profile.sh")
    assert "ini_get.py" in azure_wrapper, "azure_profile.sh must read config via ini_get.py"


def test_anti_cheating_emulators_actually_used():
    """Anti-cheating: Verify emulators are running and CLI commands actually work."""
    ensure_emulators()
    seed_defaults()
    sh("bash", "/app/bin/configure_all.sh")
    
    # Verify emulators are actually running
    result = subprocess.run(
        ["pgrep", "-f", "moto_server"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "LocalStack (moto_server) must be running"
    
    result = subprocess.run(
        ["pgrep", "-f", "pubsub-emulator"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Pub/Sub emulator must be running"
    
    result = subprocess.run(
        ["pgrep", "-f", "azurite-blob"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "Azurite must be running"
    
    # Verify ports are actually listening (use socket check)
    def is_port_listening(host: str, port: int) -> bool:
        """Check if a port is listening."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    assert is_port_listening("127.0.0.1", 4566), "Port 4566 (LocalStack) must be listening"
    assert is_port_listening("127.0.0.1", 8085), "Port 8085 (Pub/Sub) must be listening"
    assert is_port_listening("127.0.0.1", 10000), "Port 10000 (Azurite) must be listening"
    
    # Verify CLI commands actually work (not just file contents)
    # Test AWS CLI with wrapper
    result = subprocess.run(
        ["bash", "/app/bin/aws_localstack.sh", "s3api", "list-buckets"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "AWS CLI wrapper must work with emulator"
    assert "Buckets" in result.stdout or "[]" in result.stdout, "AWS CLI must return valid JSON"
    
    # Test gcloud CLI with wrapper
    result = subprocess.run(
        ["bash", "/app/bin/gcloud_pubsub.sh", "topics", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "gcloud CLI wrapper must work with emulator"
    
    # Test Azure CLI with wrapper
    result = subprocess.run(
        ["bash", "/app/bin/azure_profile.sh", "azurite", "container", "list"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, "Azure CLI wrapper must work with emulator"
    # Azure returns JSON array
    try:
        azure_data = json.loads(result.stdout)
        assert isinstance(azure_data, list), "Azure CLI must return JSON array"
    except json.JSONDecodeError:
        # Empty output is also valid
        assert result.stdout.strip() == "[]" or result.stdout.strip() == "", "Azure CLI must return valid JSON or empty array"


def test_anti_cheating_no_hardcoded_outputs():
    """Anti-cheating: Verify output files are generated by CLI commands, not hardcoded."""
    ensure_emulators()
    seed_defaults()
    sh("bash", "/app/bin/configure_all.sh")
    
    # Remove output files to ensure fresh generation (not pre-written)
    output_dir = Path("/output")
    if output_dir.exists():
        for output_file in output_dir.glob("*.txt"):
            output_file.unlink()
    output_dir.mkdir(exist_ok=True)
    
    # Verify output files don't exist before running verify_all.sh
    aws_out = Path("/output/aws_s3_list.txt")
    gcloud_out = Path("/output/gcloud_pubsub_list.txt")
    azure_out = Path("/output/azure_blob_list.txt")
    assert not aws_out.exists(), "AWS output must not exist before verify_all.sh"
    assert not gcloud_out.exists(), "gcloud output must not exist before verify_all.sh"
    assert not azure_out.exists(), "Azure output must not exist before verify_all.sh"
    
    # Run verify_all.sh - it should generate outputs via CLI commands
    sh("bash", "/app/bin/verify_all.sh")
    
    # Verify outputs exist and have correct structure (generated by CLI, not hardcoded)
    assert aws_out.exists(), "AWS output must be generated by CLI command"
    aws_data = json.loads(aws_out.read_text(encoding="utf-8"))
    assert "Buckets" in aws_data, "AWS output must be valid AWS CLI JSON response"
    
    assert gcloud_out.exists(), "gcloud output must be generated by CLI command"
    gcloud_txt = gcloud_out.read_text(encoding="utf-8")
    assert "topics" in gcloud_txt.lower() or "subscriptions" in gcloud_txt.lower(), "gcloud output must contain topic/subscription listing from CLI"
    
    assert azure_out.exists(), "Azure output must be generated by CLI command"
    azure_data = json.loads(azure_out.read_text(encoding="utf-8"))
    assert isinstance(azure_data, list), "Azure output must be JSON array from CLI"


def test_configuration_uses_helper_utilities():
    """Verify configuration scripts use helper utilities (write_ini_value.py, ini_get.py)."""
    # Check that configure scripts use write_ini_value.py
    aws_script = read_text("/app/bin/configure_aws.sh")
    assert "write_ini_value.py" in aws_script, "configure_aws.sh must use write_ini_value.py"
    
    azure_script = read_text("/app/bin/configure_azure.sh")
    assert "write_ini_value.py" in azure_script, "configure_azure.sh must use write_ini_value.py"
    
    # Check that wrapper scripts use ini_get.py
    aws_wrapper = read_text("/app/bin/aws_localstack.sh")
    assert "ini_get.py" in aws_wrapper, "aws_localstack.sh must use ini_get.py"
    
    gcloud_wrapper = read_text("/app/bin/gcloud_pubsub.sh")
    assert "ini_get.py" in gcloud_wrapper, "gcloud_pubsub.sh must use ini_get.py"
    
    azure_wrapper = read_text("/app/bin/azure_profile.sh")
    assert "ini_get.py" in azure_wrapper, "azure_profile.sh must use ini_get.py"


def test_anti_cheating_scripts_were_fixed():
    """Anti-cheating: Verify that scripts were actually fixed by the agent (not just that output is correct).
    
    This test ensures the agent actually modified the buggy starter scripts.
    The starter scripts have bugs that must be fixed:
    - AWS: Missing --profile flag (modifies [default] instead of [localstack])
    - AWS: Missing region in config file
    - gcloud: Activates config (changes active_config from 'default')
    - gcloud: Missing --configuration flag (modifies default config)
    - gcloud: Missing auth/disable_credentials
    - Azure: Missing /devstoreaccount1 in endpoint
    - verify_all.sh: Missing wait_for_ports.py call
    
    CRITICAL: This test checks the scripts BEFORE configure_all.sh runs.
    If NOP agent (does nothing) is used, scripts remain buggy and this test fails.
    If Oracle/real agent fixes scripts, this test passes.
    """
    # Check scripts BEFORE configure_all.sh runs (agent should have fixed them)
    # If scripts are still buggy, this test will fail (preventing NOP from passing)
    
    # Check that AWS script uses --profile flag (was buggy without it)
    aws_script = read_text("/app/bin/configure_aws.sh")
    # The fixed script should have --profile on all aws configure set commands
    # Find lines with 'aws configure set' that don't have --profile and aren't comments
    aws_configure_lines = []
    for line in aws_script.split('\n'):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith('#'):
            continue
        # Check for aws configure set without --profile
        if 'aws configure set' in line and '--profile' not in line:
            # This is a buggy line - add it to the list
            aws_configure_lines.append(line.strip())
    
    assert len(aws_configure_lines) == 0, f"AWS script must use --profile flag on all aws configure set commands. Found buggy lines without --profile: {aws_configure_lines[:3]}"
    
    # Check that AWS script sets region in config file (was buggy - missing)
    # The buggy script only sets region in credentials via aws configure set
    # The fixed script must also write region to config file using write_ini_value.py
    # Count write_ini_value calls for config file - buggy has 1 (endpoint), fixed has 2+ (endpoint + region)
    write_ini_calls_to_config = []
    lines = aws_script.split('\n')
    for i, line in enumerate(lines):
        if 'write_ini_value.py' in line.lower():
            # Check if this call is for config file (look at continuation lines)
            call_lines = lines[i:min(len(lines), i+8)]
            call_text = ' '.join(call_lines).lower()
            if '/root/.aws/config' in call_text:
                write_ini_calls_to_config.append((i, call_text))
    
    # Buggy script has exactly 1 write_ini_value call to config (endpoint only)
    # Fixed script should have 2+ calls (endpoint + region, or multiple calls)
    # If there are 2+ calls, at least one should be for region
    has_region_in_config_write = False
    
    if len(write_ini_calls_to_config) >= 2:
        # Multiple calls - check if any is for region
        for line_num, call_text in write_ini_calls_to_config:
            if '--key' in call_text:
                parts = call_text.split('--key')
                for part in parts[1:]:
                    after_key = part.strip()
                    first_token = after_key.split()[0] if after_key.split() else ''
                    first_token_clean = first_token.strip('"\'')
                    if first_token_clean == 'region':
                        has_region_in_config_write = True
                        break
                if has_region_in_config_write:
                    break
    elif len(write_ini_calls_to_config) == 1:
        # Only one call - check if it's for region (unlikely, but possible)
        call_text = write_ini_calls_to_config[0][1]
        if '--key' in call_text and 'region' in call_text:
            parts = call_text.split('--key')
            for part in parts[1:]:
                after_key = part.strip()
                first_token = after_key.split()[0] if after_key.split() else ''
                if first_token.strip('"\'') == 'region':
                    has_region_in_config_write = True
                    break
    
    # Buggy script has only 1 write_ini_value call (endpoint), fixed should have 2+ (endpoint + region)
    assert len(write_ini_calls_to_config) >= 2 or has_region_in_config_write, f"AWS script must write region to config file. Buggy script has {len(write_ini_calls_to_config)} write_ini_value call(s) to config (only endpoint), fixed should have 2+ (endpoint + region)."
    
    # Check that gcloud script uses --no-activate (was buggy - activated config)
    gcloud_script = read_text("/app/bin/configure_gcloud.sh")
    # Check for --no-activate in create command
    create_line = [line for line in gcloud_script.split('\n') if 'configurations create' in line and '--no-activate' in line]
    assert len(create_line) > 0, "gcloud script must use --no-activate when creating configuration"
    
    # Verify it doesn't activate the configuration (BUG line is OK, but actual activation is not)
    has_activate = False
    for line in gcloud_script.split('\n'):
        stripped = line.strip()
        if 'configurations activate' in line and not stripped.startswith('#'):
            has_activate = True
            break
    assert not has_activate, "gcloud script must NOT activate the configuration (should use --no-activate and --configuration flags)"
    
    # Check that it uses --configuration flag on config set commands
    gcloud_set_lines = []
    for line in gcloud_script.split('\n'):
        stripped = line.strip()
        if 'config set' in line and '--configuration' not in line and not stripped.startswith('#'):
            if 'BUG' not in line or 'intentional' not in line:
                gcloud_set_lines.append(line)
    assert len(gcloud_set_lines) == 0, f"gcloud script must use --configuration flag on all config set commands. Found: {gcloud_set_lines[:2]}"
    
    # Check that auth/disable_credentials is set
    assert 'auth/disable_credentials' in gcloud_script, "gcloud script must set auth/disable_credentials for offline emulator operation"
    
    # Check that Azure script has correct endpoint (was buggy - missing /devstoreaccount1)
    azure_script = read_text("/app/bin/configure_azure.sh")
    # Check that endpoint includes /devstoreaccount1
    endpoint_line = [line for line in azure_script.split('\n') if 'AZURITE_BLOB_ENDPOINT=' in line and '/devstoreaccount1' in line]
    assert len(endpoint_line) > 0, "Azure script must include /devstoreaccount1 in blob endpoint URL"
    
    # Check that verify_all.sh calls wait_for_ports.py (was buggy - missing)
    verify_script = read_text("/app/bin/verify_all.sh")
    assert 'wait_for_ports.py' in verify_script, "verify_all.sh must call wait_for_ports.py"
    # Verify it's actually executed (not just in a comment)
    verify_lines = [line for line in verify_script.split('\n') if 'wait_for_ports.py' in line and not line.strip().startswith('#')]
    assert len(verify_lines) > 0, "wait_for_ports.py must be in an executable line, not just a comment"


def test_emulator_ports_are_correct():
    """Verify emulator ports are exactly as specified (no port changes allowed)."""
    ensure_emulators()
    seed_defaults()
    sh("bash", "/app/bin/configure_all.sh")
    
    # Verify AWS config uses correct port
    aws_config = read_text("/root/.aws/config")
    assert "127.0.0.1:4566" in aws_config, "AWS must use port 4566"
    assert "http://127.0.0.1:4566" in aws_config, "AWS endpoint must be http://127.0.0.1:4566"
    
    # Verify gcloud config uses correct port
    gcloud_config = read_text("/root/.config/gcloud/configurations/config_pubsub-emulator")
    assert "127.0.0.1:8085" in gcloud_config, "gcloud must use port 8085"
    assert "http://127.0.0.1:8085/" in gcloud_config, "gcloud endpoint must be http://127.0.0.1:8085/"
    
    # Verify Azure config uses correct port
    azure_config = read_text("/root/.azure/config")
    assert "127.0.0.1:10000" in azure_config, "Azure must use port 10000"
    assert "http://127.0.0.1:10000/devstoreaccount1" in azure_config, "Azure endpoint must be http://127.0.0.1:10000/devstoreaccount1"


def test_no_external_network_calls():
    """Verify all endpoints point to localhost (no external network calls)."""
    ensure_emulators()
    seed_defaults()
    sh("bash", "/app/bin/configure_all.sh")
    
    # Verify all endpoints are localhost
    aws_config = read_text("/root/.aws/config")
    assert "127.0.0.1" in aws_config or "localhost" in aws_config, "AWS endpoint must be localhost"
    assert "http://" in aws_config or "https://" in aws_config, "AWS endpoint must have scheme"
    # Ensure no external domains
    assert ".com" not in aws_config and ".net" not in aws_config, "AWS must not use external domains"
    
    gcloud_config = read_text("/root/.config/gcloud/configurations/config_pubsub-emulator")
    assert "127.0.0.1" in gcloud_config or "localhost" in gcloud_config, "gcloud endpoint must be localhost"
    assert ".com" not in gcloud_config and ".net" not in gcloud_config, "gcloud must not use external domains"
    
    azure_config = read_text("/root/.azure/config")
    assert "127.0.0.1" in azure_config or "localhost" in azure_config, "Azure endpoint must be localhost"
    assert ".com" not in azure_config and ".net" not in azure_config, "Azure must not use external domains"



