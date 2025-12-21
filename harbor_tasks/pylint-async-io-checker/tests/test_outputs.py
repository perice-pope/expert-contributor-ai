"""Tests for the Pylint async I/O checker plugin task."""
from pathlib import Path
import subprocess
import sys
import os
import re


def test_plugin_file_exists():
    """Verify the async_io_checker.py plugin file exists."""
    plugin_path = Path("/app/async_io_checker.py")
    assert plugin_path.exists(), f"Plugin file {plugin_path} does not exist"
    assert plugin_path.is_file(), f"{plugin_path} exists but is not a file"


def test_plugin_is_importable():
    """Verify the plugin can be imported without errors."""
    plugin_path = Path("/app/async_io_checker.py")
    assert plugin_path.exists(), "Plugin file must exist"
    
    # Try to import the plugin
    sys.path.insert(0, "/app")
    try:
        import async_io_checker
        assert hasattr(async_io_checker, "AsyncIOChecker"), "Plugin must define AsyncIOChecker class"
    except ImportError as e:
        assert False, f"Failed to import plugin: {e}"


def test_pyproject_toml_has_entry_points():
    """Verify pyproject.toml contains entry points for Pylint."""
    pyproject_path = Path("/app/pyproject.toml")
    assert pyproject_path.exists(), f"pyproject.toml {pyproject_path} does not exist"
    
    content = pyproject_path.read_text()
    
    # Check for entry points section
    assert "[project.entry-points" in content or '["pylint.checkers"]' in content, (
        "pyproject.toml must contain entry points for Pylint checkers"
    )
    
    # Check that async_io_checker is referenced
    assert "async_io_checker" in content, (
        "pyproject.toml must reference async_io_checker in entry points"
    )


def test_pyproject_toml_has_configuration():
    """Verify pyproject.toml contains configuration section for the plugin."""
    pyproject_path = Path("/app/pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"
    
    content = pyproject_path.read_text()
    
    # Check for configuration section
    assert "[tool.pylint.async_io_checker]" in content, (
        "pyproject.toml must contain [tool.pylint.async_io_checker] configuration section"
    )


def test_unit_tests_exist():
    """Verify unit test file exists."""
    test_path = Path("/app/tests/test_async_io_checker.py")
    assert test_path.exists(), f"Unit test file {test_path} does not exist"


def test_unit_tests_pass():
    """Verify unit tests pass when run."""
    test_path = Path("/app/tests/test_async_io_checker.py")
    assert test_path.exists(), "Unit test file must exist"
    
    # Run pytest on the test file (use python3 which has pytest installed)
    result = subprocess.run(
        ["python3", "-m", "pytest", str(test_path), "-v"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=60
    )
    
    assert result.returncode == 0, (
        f"Unit tests failed with return code {result.returncode}. "
        f"Stdout: {result.stdout}\nStderr: {result.stderr}"
    )


def test_plugin_detects_blocking_io():
    """Verify plugin detects blocking I/O calls in async functions."""
    # Create a test file with blocking I/O
    test_file = Path("/tmp/test_blocking_io.py")
    test_file.write_text("""
import time
import requests

async def fetch_data():
    time.sleep(1)
    response = requests.get("https://example.com")
    return response.text
""")
    
    try:
        # Run pylint with the plugin (use python3 which has pylint installed)
        # Set PYTHONPATH to include /app so pylint can find the plugin
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd="/app",
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that blocking-io-in-async messages are present
        output = result.stdout + result.stderr
        assert "blocking-io-in-async" in output, (
            f"Plugin should detect blocking I/O. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_plugin_no_false_positives():
    """Verify plugin does not flag blocking I/O in sync functions."""
    # Create a test file with blocking I/O in sync function
    test_file = Path("/tmp/test_sync.py")
    test_file.write_text("""
import time

def sync_function():
    time.sleep(1)
    return "ok"
""")
    
    try:
        # Run pylint with the plugin (use python3 which has pylint installed)
        # Set PYTHONPATH to include /app so pylint can find the plugin
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd="/app",
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check that no blocking-io-in-async messages are present
        output = result.stdout + result.stderr
        blocking_messages = [line for line in output.split('\n') if 'blocking-io-in-async' in line]
        assert len(blocking_messages) == 0, (
            f"Plugin should not flag sync functions. Found messages: {blocking_messages}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_plugin_detects_open_call():
    """Verify plugin detects open() calls in async functions."""
    test_file = Path("/tmp/test_open.py")
    test_file.write_text("""
async def read_file():
    with open("data.txt", "r") as f:
        return f.read()
""")
    
    try:
        # Run pylint with the plugin (use python3 which has pylint installed)
        # Set PYTHONPATH to include /app so pylint can find the plugin
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd="/app",
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        assert "blocking-io-in-async" in output, (
            f"Plugin should detect open() in async function. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_warnings_include_suggestions():
    """Verify warnings include suggestions for asyncio.to_thread."""
    test_file = Path("/tmp/test_suggestion.py")
    test_file.write_text("""
import time

async def test():
    time.sleep(1)
""")
    
    try:
        # Set PYTHONPATH to include /app so pylint can find the plugin
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd="/app",
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        # Check that suggestion mentions asyncio.to_thread
        assert "asyncio.to_thread" in output or "to_thread" in output, (
            f"Warning should suggest asyncio.to_thread. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()
