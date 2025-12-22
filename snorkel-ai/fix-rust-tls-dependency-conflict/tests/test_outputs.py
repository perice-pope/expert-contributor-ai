"""Tests for Rust TLS dependency conflict fix.

These tests validate that:
1. The project builds successfully (cargo build)
2. All tests pass (cargo test)
3. The fix resolves the OpenSSL dependency issue
"""

import subprocess
import sys
from pathlib import Path


def test_cargo_build_succeeds():
    """Test that cargo build completes successfully after the fix."""
    result = subprocess.run(
        ["cargo", "build"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=300,
    )
    
    assert result.returncode == 0, (
        f"cargo build failed with exit code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_cargo_test_succeeds():
    """Test that cargo test completes successfully with all tests passing."""
    result = subprocess.run(
        ["cargo", "test"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=300,
    )
    
    assert result.returncode == 0, (
        f"cargo test failed with exit code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    
    # Verify that tests actually ran (not just compilation)
    assert "test result: ok" in result.stdout.lower() or "running" in result.stdout.lower(), (
        "cargo test output does not indicate tests were run"
    )


def test_cargo_toml_modified():
    """Test that Cargo.toml has been modified to use rustls-tls."""
    cargo_toml = Path("/app/Cargo.toml")
    assert cargo_toml.exists(), "Cargo.toml does not exist"
    
    content = cargo_toml.read_text()
    
    # The fix should use rustls-tls feature, not default native-tls
    # Check that reqwest configuration has been changed
    assert "rustls-tls" in content, (
        "Cargo.toml does not contain 'rustls-tls' feature. "
        "The fix should configure reqwest to use rustls-tls instead of native-tls."
    )
    
    # Verify default-features is disabled (to avoid native-tls)
    assert "default-features = false" in content or '"default-features": false' in content, (
        "Cargo.toml should disable default-features for reqwest to avoid native-tls"
    )


def test_binary_exists_after_build():
    """Test that the built binary exists after successful build."""
    # Check for debug binary (default cargo build output)
    debug_binary = Path("/app/target/debug/tls-client")
    # Or release binary if built with --release
    release_binary = Path("/app/target/release/tls-client")
    
    assert debug_binary.exists() or release_binary.exists(), (
        "Built binary not found. Expected /app/target/debug/tls-client or "
        "/app/target/release/tls-client to exist after cargo build."
    )
