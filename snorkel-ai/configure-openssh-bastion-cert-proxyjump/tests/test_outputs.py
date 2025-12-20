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
    assert f"certificatefile {BASE / 'client' / 'id_client-cert.pub'}" in details


def test_known_hosts_hashed_and_ca_present():
    text = KNOWN_HOSTS.read_text()
    assert "@cert-authority" in text, "Host CA entry missing"
    lookup = subprocess.run(
        ["ssh-keygen", "-F", "[127.0.0.1]:2222", "-f", str(KNOWN_HOSTS)],
        capture_output=True,
        text=True,
    )
    assert lookup.returncode == 0, lookup.stderr
    assert "|1|" in text, "known_hosts should contain hashed entries"


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
