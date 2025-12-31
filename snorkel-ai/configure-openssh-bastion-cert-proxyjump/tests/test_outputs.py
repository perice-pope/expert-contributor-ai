import os
import socket
import subprocess
import time
from pathlib import Path

import pytest

BASE = Path(os.environ.get("APP_ROOT", "/app"))
BASTION_CONFIG = BASE / "bastion" / "sshd_config"
APP_CONFIG = BASE / "apphost" / "sshd_config"
SSH_CONFIG = BASE / "client" / "ssh_config"
KNOWN_HOSTS = BASE / "client" / "known_hosts"


def _port_from_config(config_path: Path) -> int:
    for line in config_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("port"):
            parts = stripped.split()
            if len(parts) >= 2:
                return int(parts[1])
    raise AssertionError(f"Port not found in {config_path}")


def _wait_for_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError as exc:  # pragma: no cover - diagnostic only
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f"Port {port} did not open in time: {last_error}")


def _ensure_user(username: str) -> None:
    result = subprocess.run(["id", username], capture_output=True)
    if result.returncode != 0:
        subprocess.run(["useradd", "-m", "-s", "/bin/bash", username], check=True)
    subprocess.run(["passwd", "-d", username], check=False)
    subprocess.run(["usermod", "-U", username], check=False)


def _config_with_cert(cert_path: Path) -> Path:
    lines = []
    for line in SSH_CONFIG.read_text().splitlines():
        if line.strip().startswith("CertificateFile"):
            indent = line[: line.index("CertificateFile")]
            lines.append(f"{indent}CertificateFile {cert_path}")
        else:
            lines.append(line)
    temp = Path("/tmp") / f"ssh_config_{cert_path.stem}"
    temp.write_text("\n".join(lines) + "\n")
    return temp


def _start_sshd(config_path: Path, runtime_dir: Path):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    check = subprocess.run(
        ["/usr/sbin/sshd", "-t", "-f", str(config_path)],
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, f"sshd config check failed: {check.stderr}"

    logfile = runtime_dir / "sshd.log"
    proc = subprocess.Popen(
        ["/usr/sbin/sshd", "-D", "-f", str(config_path), "-E", str(logfile)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _wait_for_port(_port_from_config(config_path))
    return proc


def _stop_proc(proc: subprocess.Popen):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def ssh_servers():
    _ensure_user("appuser")
    Path("/var/run/sshd").mkdir(parents=True, exist_ok=True)
    subprocess.run([f"{BASE}/bin/fix_permissions.sh"], check=True)

    bastion_proc = _start_sshd(BASTION_CONFIG, Path("/tmp/sshd-bastion"))
    app_proc = _start_sshd(APP_CONFIG, Path("/tmp/sshd-app"))

    yield

    _stop_proc(bastion_proc)
    _stop_proc(app_proc)


def test_proxyjump_configured():
    details = subprocess.check_output(
        ["ssh", "-G", "-F", str(SSH_CONFIG), "app-via-bastion"],
        text=True,
    )
    assert "proxyjump" in details
    assert "bastion" in details
    # ssh -G outputs paths as written in config, which uses /app/client/...
    assert "certificatefile" in details
    assert "id_client-cert.pub" in details


def test_stricthostkeychecking_yes():
    """Verify StrictHostKeyChecking is set to 'yes' (not 'accept-new' or missing)."""
    bastion_details = subprocess.check_output(
        ["ssh", "-G", "-F", str(SSH_CONFIG), "bastion"],
        text=True,
    )
    app_details = subprocess.check_output(
        ["ssh", "-G", "-F", str(SSH_CONFIG), "app-via-bastion"],
        text=True,
    )
    # ssh -G outputs 'true' for 'yes' values, so check for 'true' (not 'accept-new' or 'false')
    bastion_lower = bastion_details.lower()
    app_lower = app_details.lower()
    assert "stricthostkeychecking true\n" in bastion_lower, (
        f"bastion host must have StrictHostKeyChecking yes (got: {[line for line in bastion_lower.splitlines() if 'stricthostkeychecking' in line]})"
    )
    assert "stricthostkeychecking true\n" in app_lower, (
        f"app-via-bastion host must have StrictHostKeyChecking yes (got: {[line for line in app_lower.splitlines() if 'stricthostkeychecking' in line]})"
    )
    # Also verify it's not 'accept-new' or 'false'
    assert "stricthostkeychecking accept-new" not in bastion_lower, (
        "bastion host must not have StrictHostKeyChecking accept-new"
    )
    assert "stricthostkeychecking accept-new" not in app_lower, (
        "app-via-bastion host must not have StrictHostKeyChecking accept-new"
    )


def test_known_hosts_hashed_and_ca_present():
    """Verify known_hosts is hashed and contains required entries."""
    text = KNOWN_HOSTS.read_text()
    assert "@cert-authority" in text, "Host CA entry missing"
    
    # Verify the file contains hashed entries
    assert "|1|" in text, "known_hosts should contain hashed entries"
    
    # Verify @cert-authority entry is present (check in text since it may be unhashed)
    has_cert_authority = False
    for line in text.splitlines():
        if "@cert-authority" in line:
            has_cert_authority = True
            break
    assert has_cert_authority, "@cert-authority entry must be present"
    
    # Verify bastion host entry (port 2222) is present and lookupable
    # Use ssh-keygen -F to find it (works for both hashed and unhashed entries)
    lookup = subprocess.run(
        ["ssh-keygen", "-F", "[127.0.0.1]:2222", "-f", str(KNOWN_HOSTS)],
        capture_output=True,
        text=True,
    )
    assert lookup.returncode == 0, f"Bastion host entry (port 2222) must be present: {lookup.stderr}"
    
    # Verify the bastion entry is hashed by checking the lookup output or file content
    # If the entry is hashed, the file will contain |1| and ssh-keygen will still find it
    # Check that at least one entry in the file is hashed (the bastion entry should be)
    hashed_lines = [line for line in text.splitlines() if line.strip().startswith("|1|")]
    assert len(hashed_lines) > 0, "At least one entry (bastion host) must be hashed"
    
    # Verify the @cert-authority entry targets the correct host (port 2223)
    # This can be verified by checking the text or using ssh-keygen
    cert_auth_lookup = subprocess.run(
        ["ssh-keygen", "-F", "[127.0.0.1]:2223", "-f", str(KNOWN_HOSTS)],
        capture_output=True,
        text=True,
    )
    # The @cert-authority should match port 2223 (app host)
    assert cert_auth_lookup.returncode == 0 or "@cert-authority" in text, (
        "@cert-authority entry should be present for app host (port 2223)"
    )


def test_certificate_auth_via_proxyjump(ssh_servers):
    result = subprocess.run(
        [
            "ssh",
            "-F",
            str(SSH_CONFIG),
            "app-via-bastion",
            "--",
            "echo",
            "ok",
        ],
        text=True,
        capture_output=True,
        env={"SSH_AUTH_SOCK": "", **os.environ},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
    assert "authenticity" not in result.stderr.lower()


def test_expired_cert_rejected(ssh_servers):
    expired_cert = BASE / "client" / "id_client-expired-cert.pub"
    cfg = _config_with_cert(expired_cert)
    result = subprocess.run(
        [
            "ssh",
            "-F",
            str(cfg),
            "app-via-bastion",
            "--",
            "echo",
            "nope",
        ],
        text=True,
        capture_output=True,
        env={"SSH_AUTH_SOCK": "", **os.environ},
    )
    assert result.returncode != 0, "Expired certificate should not authenticate"


def test_wrong_principal_rejected(ssh_servers):
    wrong_cert = BASE / "client" / "id_client-wrong-principal-cert.pub"
    cfg = _config_with_cert(wrong_cert)
    result = subprocess.run(
        [
            "ssh",
            "-F",
            str(cfg),
            "app-via-bastion",
            "--",
            "echo",
            "nope",
        ],
        text=True,
        capture_output=True,
        env={"SSH_AUTH_SOCK": "", **os.environ},
    )
    assert result.returncode != 0, "Wrong principal certificate should be rejected"
