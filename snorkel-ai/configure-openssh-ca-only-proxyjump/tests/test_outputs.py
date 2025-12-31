import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

BASE = Path(os.environ.get("APP_ROOT", "/app"))
BASTION_CONFIG = BASE / "bastion" / "sshd_config"
INTERNAL_CONFIG = BASE / "internal" / "sshd_config"
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
        except OSError as exc:  # pragma: no cover - diagnostics only
            last_error = exc
            time.sleep(0.1)
    raise AssertionError(f"Port {port} did not open in time: {last_error}")


def _ensure_user(username: str) -> None:
    result = subprocess.run(["id", username], capture_output=True)
    if result.returncode != 0:
        subprocess.run(["useradd", "-m", "-s", "/bin/bash", username], check=True)
    subprocess.run(["passwd", "-d", username], check=False)
    subprocess.run(["usermod", "-U", username], check=False)


def _config_without_cert() -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    raw_key = temp_dir / "id_client_raw"
    raw_key.write_bytes((BASE / "client" / "id_client").read_bytes())
    os.chmod(raw_key, 0o600)

    lines = []
    for line in SSH_CONFIG.read_text().splitlines():
        lowered = line.strip().lower()
        if lowered.startswith("certificatefile"):
            continue
        if lowered.startswith("identityfile"):
            indent = line[: line.index("IdentityFile")]
            lines.append(f"{indent}IdentityFile {raw_key}")
            continue
        lines.append(line)
    lines.append("    ControlMaster no")
    lines.append("    ControlPath none")
    temp = temp_dir / "ssh_config_no_cert"
    temp.write_text("\n".join(lines) + "\n")
    return temp


def _resolved_control_path() -> Path:
    resolved = subprocess.check_output(
        ["ssh", "-G", "-F", str(SSH_CONFIG), "app-via-bastion"],
        text=True,
    )
    template = hostname = port = user = None
    for line in resolved.splitlines():
        if line.startswith("controlpath "):
            template = line.split(" ", 1)[1].strip()
        if line.startswith("hostname "):
            hostname = line.split(" ", 1)[1].strip()
        if line.startswith("port "):
            port = line.split(" ", 1)[1].strip()
        if line.startswith("user "):
            user = line.split(" ", 1)[1].strip()
    if not all([template, hostname, port, user]):
        raise AssertionError("ControlPath could not be resolved from ssh -G")
    control_path = (
        template.replace("%r", user)
        .replace("%h", hostname)
        .replace("%p", port)
    )
    return Path(control_path).expanduser()


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
def sshd():
    _ensure_user("appuser")
    Path("/var/run/sshd").mkdir(parents=True, exist_ok=True)
    subprocess.run([f"{BASE}/bin/fix_permissions.sh"], check=True)

    bastion_proc = _start_sshd(BASTION_CONFIG, Path("/tmp/sshd-bastion"))
    internal_proc = _start_sshd(INTERNAL_CONFIG, Path("/tmp/sshd-internal"))

    yield

    _stop_proc(bastion_proc)
    _stop_proc(internal_proc)


def test_ca_material_present():
    """Verify that all required CA keys, certificates, and signed host/user certs are present."""
    user_ca = BASE / "ca" / "ssh_user_ca"
    host_ca = BASE / "ca" / "ssh_host_ca"
    assert user_ca.exists()
    assert host_ca.exists()
    assert (user_ca.with_suffix(user_ca.suffix + ".pub")).exists()
    assert (host_ca.with_suffix(host_ca.suffix + ".pub")).exists()

    for host_dir in ["bastion", "internal"]:
        key = BASE / host_dir / "ssh_host_ed25519_key"
        cert = BASE / host_dir / "ssh_host_ed25519_key-cert.pub"
        assert key.exists()
        assert cert.exists()

    user_cert = BASE / "client" / "id_client-cert.pub"
    assert user_cert.exists()


def test_config_enforces_ca_only():
    """Verify that both sshd configs enforce CA-only authentication with no password/keyboard-interactive auth and proper host certificate presentation."""
    bastion_conf = BASTION_CONFIG.read_text()
    internal_conf = INTERNAL_CONFIG.read_text()
    assert "TrustedUserCAKeys" in bastion_conf
    assert "TrustedUserCAKeys" in internal_conf
    assert "AuthorizedKeysFile none" in bastion_conf
    assert "AuthorizedKeysFile none" in internal_conf
    assert "PasswordAuthentication no" in bastion_conf
    assert "PasswordAuthentication no" in internal_conf
    assert "KbdInteractiveAuthentication no" in bastion_conf
    assert "KbdInteractiveAuthentication no" in internal_conf
    assert "HostCertificate" in bastion_conf
    assert "HostCertificate" in internal_conf
    assert "AuthorizedPrincipalsFile" in internal_conf
    assert BASE.joinpath("internal", "authorized_principals").read_text().strip() == "appuser"


def test_client_configured_for_proxyjump_and_control():
    """Verify that client ssh_config has ProxyJump, ControlMaster, ControlPersist, CertificateFile, UserKnownHostsFile, and StrictHostKeyChecking configured correctly."""
    output = subprocess.check_output(
        ["ssh", "-G", "-F", str(SSH_CONFIG), "app-via-bastion"],
        text=True,
    )
    lowered = output.lower()
    assert "proxyjump bastion" in lowered
    assert "controlmaster auto" in lowered
    assert "controlpersist yes" in lowered or "controlpersist 5m" in lowered
    assert f"certificatefile {BASE / 'client' / 'id_client-cert.pub'}".lower() in lowered
    assert f"userknownhostsfile {KNOWN_HOSTS}".lower() in lowered
    assert "stricthostkeychecking yes" in lowered or "stricthostkeychecking true" in lowered


def test_known_hosts_hashed_and_ca_listed():
    """Verify that known_hosts is hashed (contains |1| markers) and includes @cert-authority entries for both bastion and internal hosts."""
    text = KNOWN_HOSTS.read_text()
    assert "@cert-authority" in text, "Host CA entry missing"
    assert "|1|" in text, "known_hosts should contain hashed entries"

    lookup = subprocess.run(
        ["ssh-keygen", "-F", "[127.0.0.1]:2222", "-f", str(KNOWN_HOSTS)],
        capture_output=True,
        text=True,
    )
    assert lookup.returncode == 0, lookup.stderr

    lookup_internal = subprocess.run(
        ["ssh-keygen", "-F", "[127.0.0.1]:2223", "-f", str(KNOWN_HOSTS)],
        capture_output=True,
        text=True,
    )
    assert lookup_internal.returncode == 0, lookup_internal.stderr


def test_ssh_and_scp_work(sshd):
    """Verify that ssh and scp commands work non-interactively through ProxyJump with ControlMaster, and that ControlPath socket is created."""
    env = {"SSH_AUTH_SOCK": "", **os.environ}
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
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
    assert "authenticity" not in result.stderr.lower()

    control_path = _resolved_control_path()
    assert control_path.exists(), "ControlPath not created"

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write("via-proxyjump")
        local_path = handle.name

    try:
        remote_path = "/home/appuser/from_client.txt"
        scp = subprocess.run(
            ["scp", "-F", str(SSH_CONFIG), local_path, f"app-via-bastion:{remote_path}"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert scp.returncode == 0, scp.stderr

        check = subprocess.run(
            ["ssh", "-F", str(SSH_CONFIG), "app-via-bastion", "--", "cat", remote_path],
            capture_output=True,
            text=True,
            env=env,
        )
        assert check.returncode == 0, check.stderr
        assert check.stdout.strip() == "via-proxyjump"
    finally:
        Path(local_path).unlink(missing_ok=True)


def test_raw_key_rejected(sshd):
    """Verify that authentication attempts using raw (unsigned) keys are rejected when certificate authentication is required."""
    _resolved_control_path().unlink(missing_ok=True)
    cfg = _config_without_cert()
    result = subprocess.run(
        [
            "ssh",
            "-F",
            str(cfg),
            "-o",
            "ControlMaster=no",
            "-S",
            "none",
            "app-via-bastion",
            "--",
            "true",
        ],
        text=True,
        capture_output=True,
        env={"SSH_AUTH_SOCK": "", **os.environ},
        timeout=10,
    )
    assert result.returncode != 0, "Unsigned key should not authenticate"


def test_password_auth_disabled(sshd):
    """Verify that password authentication is disabled and cannot be used even when explicitly requested."""
    _resolved_control_path().unlink(missing_ok=True)
    result = subprocess.run(
        [
            "ssh",
            "-F",
            str(SSH_CONFIG),
            "-o",
            "ControlMaster=no",
            "-S",
            "none",
            "-o",
            "PubkeyAuthentication=no",
            "-o",
            "PreferredAuthentications=password",
            "app-via-bastion",
            "--",
            "true",
        ],
        text=True,
        capture_output=True,
        env={"SSH_AUTH_SOCK": "", **os.environ},
        timeout=10,
    )
    assert result.returncode != 0, "Password auth should be disabled"
