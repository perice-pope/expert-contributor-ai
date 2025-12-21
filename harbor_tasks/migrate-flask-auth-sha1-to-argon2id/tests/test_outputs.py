"""Tests for the Flask auth service migration from SHA-1 to Argon2id."""
import json
import os
import subprocess
import time
from pathlib import Path
import requests
import argon2
import hashlib
import re


def test_users_json_exists():
    """Verify users.json file exists."""
    users_path = Path("/app/users.json")
    assert users_path.exists(), f"Users file {users_path} does not exist"
    assert users_path.is_file(), f"{users_path} exists but is not a file"


def test_users_json_valid():
    """Verify users.json is valid JSON with expected structure."""
    users_path = Path("/app/users.json")
    users = json.loads(users_path.read_text())
    
    assert isinstance(users, dict), "Users file must be a JSON object"
    assert len(users) > 0, "Users file must contain at least one user"
    
    # Verify each user has required fields
    for username, user_data in users.items():
        assert isinstance(user_data, dict), f"User {username} must be an object"
        assert 'username' in user_data, f"User {username} must have username field"
        assert 'password_hash' in user_data, f"User {username} must have password_hash field"


def test_migration_script_runs():
    """Verify migration script executes without errors."""
    migrate_path = Path("/app/migrate.py")
    assert migrate_path.exists(), "Migration script must exist"
    
    result = subprocess.run(
        ["python3", str(migrate_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Script should complete (may have warnings but should not crash)
    assert result.returncode == 0 or "Migration complete" in result.stdout, (
        f"Migration script failed: {result.stderr}"
    )


def test_audit_json_created():
    """Verify audit.json file was created by migration."""
    audit_path = Path("/app/audit.json")
    assert audit_path.exists(), f"Audit file {audit_path} does not exist"
    assert audit_path.is_file(), f"{audit_path} exists but is not a file"


def test_audit_json_valid():
    """Verify audit.json has correct structure and data types."""
    audit_path = Path("/app/audit.json")
    audit = json.loads(audit_path.read_text())
    
    assert isinstance(audit, dict), "Audit file must be a JSON object"
    assert 'migrated_count' in audit, "Audit must have migrated_count field"
    assert 'failed_count' in audit, "Audit must have failed_count field"
    assert 'failed_users' in audit, "Audit must have failed_users field"
    
    assert isinstance(audit['migrated_count'], int), "migrated_count must be an integer"
    assert isinstance(audit['failed_count'], int), "failed_count must be an integer"
    assert isinstance(audit['failed_users'], list), "failed_users must be an array"
    
    assert audit['migrated_count'] >= 0, "migrated_count must be non-negative"
    assert audit['failed_count'] >= 0, "failed_count must be non-negative"


def test_some_users_migrated():
    """Verify at least some users were successfully migrated."""
    audit_path = Path("/app/audit.json")
    audit = json.loads(audit_path.read_text())
    
    # At least 4 users should migrate successfully (alice, bob, charlie, diana)
    # eve has wrong password, so should fail
    assert audit['migrated_count'] >= 4, (
        f"Expected at least 4 users migrated, got {audit['migrated_count']}"
    )


def test_failed_users_recorded():
    """Verify failed users are recorded in audit."""
    audit_path = Path("/app/audit.json")
    audit = json.loads(audit_path.read_text())
    
    # eve should be in failed_users (wrong password in CSV)
    assert 'eve' in audit['failed_users'], (
        f"User 'eve' should be in failed_users (wrong password). "
        f"Failed users: {audit['failed_users']}"
    )


def test_users_migrated_to_argon2id():
    """Verify migrated users have Argon2id hashes (not SHA-1)."""
    users_path = Path("/app/users.json")
    users = json.loads(users_path.read_text())
    
    argon2id_count = 0
    sha1_count = 0
    
    for username, user_data in users.items():
        stored_hash = user_data.get('password_hash', '')
        
        # Check if Argon2id hash (starts with $argon2id$)
        if stored_hash.startswith('$argon2id$'):
            argon2id_count += 1
        # Check if SHA-1 hash (40 hex chars)
        elif len(stored_hash) == 40 and all(c in '0123456789abcdef' for c in stored_hash.lower()):
            sha1_count += 1
    
    # At least 4 users should be migrated to Argon2id
    assert argon2id_count >= 4, (
        f"Expected at least 4 users with Argon2id hashes, got {argon2id_count}. "
        f"SHA-1 count: {sha1_count}"
    )


def test_argon2id_hashes_valid():
    """Verify Argon2id hashes are valid and can be parsed."""
    users_path = Path("/app/users.json")
    users = json.loads(users_path.read_text())
    
    config_path = Path("/app/argon2_config.json")
    config = json.loads(config_path.read_text())
    
    for username, user_data in users.items():
        stored_hash = user_data.get('password_hash', '')
        
        if stored_hash.startswith('$argon2id$'):
            # Verify hash format
            assert stored_hash.startswith('$argon2id$'), f"Invalid Argon2id hash format for {username}"
            
            # Extract parameters from hash
            match = re.search(r'\$m=(\d+),t=(\d+),p=(\d+)\$', stored_hash)
            assert match is not None, f"Cannot parse Argon2id parameters for {username}"
            
            memory_cost = int(match.group(1))
            time_cost = int(match.group(2))
            parallelism = int(match.group(3))
            
            # Verify parameters match config
            assert memory_cost == config['memory_cost'], (
                f"Memory cost mismatch for {username}: {memory_cost} != {config['memory_cost']}"
            )
            assert time_cost == config['time_cost'], (
                f"Time cost mismatch for {username}: {time_cost} != {config['time_cost']}"
            )
            assert parallelism == config['parallelism'], (
                f"Parallelism mismatch for {username}: {parallelism} != {config['parallelism']}"
            )


def test_auth_service_starts():
    """Verify auth service can start and respond to requests."""
    # Start auth service in background
    # Use python3 from PATH, but ensure system packages are available
    # Use system Python which has Flask installed from Dockerfile
    # Flask is installed via pip in Dockerfile, try to find the system Python
    import shutil
    python_cmd = shutil.which("python3") or "python3"
    service_process = subprocess.Popen(
        [python_cmd, "/app/auth_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": "/usr/local/lib/python3.11/site-packages:/usr/lib/python3.11/site-packages"}
    )
    
    try:
        # Wait for service to start
        time.sleep(2)
        
        # Check if process is still running
        if service_process.poll() is not None:
            stdout, stderr = service_process.communicate()
            error_msg = f"Auth service process died with return code {service_process.returncode}"
            if stderr:
                error_msg += f"\nStderr: {stderr.decode('utf-8', errors='replace')}"
            if stdout:
                error_msg += f"\nStdout: {stdout.decode('utf-8', errors='replace')}"
            assert False, error_msg
        
        # Try to connect to service
        try:
            response = requests.get("http://localhost:5000/login", timeout=2)
            # Should get 405 Method Not Allowed (GET not allowed, but service is up)
            assert response.status_code in [400, 405], f"Unexpected status: {response.status_code}"
        except requests.exceptions.ConnectionError:
            # Service might not be ready yet, wait a bit more
            time.sleep(2)
            response = requests.get("http://localhost:5000/login", timeout=2)
            assert response.status_code in [400, 405], f"Unexpected status: {response.status_code}"
    finally:
        service_process.terminate()
        service_process.wait(timeout=5)


def test_auth_service_login_with_migrated_hash():
    """Verify auth service can authenticate with migrated Argon2id hashes."""
    # Load users to get a migrated user
    users_path = Path("/app/users.json")
    users = json.loads(users_path.read_text())
    
    # Find a user with Argon2id hash
    test_user = None
    test_password = None
    
    # Map of usernames to their passwords from login_attempts.csv
    password_map = {
        "alice": "password123",
        "bob": "securepass456",
        "charlie": "mysecret789",
        "diana": "testpass321"
    }
    
    for username, user_data in users.items():
        stored_hash = user_data.get('password_hash', '')
        if stored_hash.startswith('$argon2id$') and username in password_map:
            test_user = username
            test_password = password_map[username]
            break
    
    assert test_user is not None, "No migrated user found for testing"
    
    # Start auth service
    # Use python3 from PATH, but ensure system packages are available
    # Use system Python which has Flask installed from Dockerfile
    # Flask is installed via pip in Dockerfile, try to find the system Python
    import shutil
    python_cmd = shutil.which("python3") or "python3"
    service_process = subprocess.Popen(
        [python_cmd, "/app/auth_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": "/usr/local/lib/python3.11/site-packages:/usr/lib/python3.11/site-packages"}
    )
    
    try:
        time.sleep(2)
        
        # Test login
        response = requests.post(
            "http://localhost:5000/login",
            json={"username": test_user, "password": test_password},
            timeout=5
        )
        
        assert response.status_code == 200, (
            f"Login failed for {test_user}: {response.status_code} - {response.text}"
        )
        
        data = response.json()
        assert data.get('status') == 'success', (
            f"Login should succeed: {data}"
        )
    finally:
        service_process.terminate()
        service_process.wait(timeout=5)


def test_auth_service_rejects_invalid_password():
    """Verify auth service rejects invalid passwords."""
    # Start auth service
    # Use python3 from PATH, but ensure system packages are available
    # Use system Python which has Flask installed from Dockerfile
    # Flask is installed via pip in Dockerfile, try to find the system Python
    import shutil
    python_cmd = shutil.which("python3") or "python3"
    service_process = subprocess.Popen(
        [python_cmd, "/app/auth_service.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": "/usr/local/lib/python3.11/site-packages:/usr/lib/python3.11/site-packages"}
    )
    
    try:
        time.sleep(2)
        
        # Test login with wrong password
        response = requests.post(
            "http://localhost:5000/login",
            json={"username": "alice", "password": "wrongpassword"},
            timeout=5
        )
        
        assert response.status_code == 401, (
            f"Should reject invalid password: {response.status_code} - {response.text}"
        )
        
        data = response.json()
        assert data.get('status') == 'error', (
            f"Should return error status: {data}"
        )
    finally:
        service_process.terminate()
        service_process.wait(timeout=5)


def test_audit_failed_count_matches_failed_users():
    """Verify failed_count in audit matches number of failed_users."""
    audit_path = Path("/app/audit.json")
    audit = json.loads(audit_path.read_text())
    
    assert audit['failed_count'] == len(audit['failed_users']), (
        f"failed_count ({audit['failed_count']}) should match "
        f"number of failed_users ({len(audit['failed_users'])})"
    )


def test_migration_idempotent():
    """Verify running migration multiple times doesn't break things."""
    # Run migration again
    migrate_path = Path("/app/migrate.py")
    result = subprocess.run(
        ["python3", str(migrate_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert result.returncode == 0 or "Migration complete" in result.stdout, (
        f"Second migration run failed: {result.stderr}"
    )
    
    # Audit should still be valid
    audit_path = Path("/app/audit.json")
    audit = json.loads(audit_path.read_text())
    
    assert isinstance(audit['migrated_count'], int)
    assert isinstance(audit['failed_count'], int)
    assert isinstance(audit['failed_users'], list)
