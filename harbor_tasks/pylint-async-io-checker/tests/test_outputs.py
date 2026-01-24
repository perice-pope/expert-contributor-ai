"""Tests for the Pylint async I/O checker plugin task."""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile


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


def test_entry_point_is_discoverable():
    """Verify entry point registration is discoverable after install."""
    import shutil

    install_cmd = None
    if shutil.which("uv"):
        install_cmd = ["uv", "pip", "install", "-e", "/app"]
    else:
        install_cmd = [sys.executable, "-m", "pip", "install", "-e", "/app"]

    install_result = subprocess.run(
        install_cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if install_result.returncode != 0 and "No module named pip" in install_result.stderr:
        ensure_result = subprocess.run(
            [sys.executable, "-m", "ensurepip", "--upgrade"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert ensure_result.returncode == 0, (
            "ensurepip failed. "
            f"Stdout: {ensure_result.stdout}\nStderr: {ensure_result.stderr}"
        )
        install_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "/app"],
            capture_output=True,
            text=True,
            timeout=120,
        )

    assert install_result.returncode == 0, (
        "Editable install failed. "
        f"Stdout: {install_result.stdout}\nStderr: {install_result.stderr}"
    )

    import importlib.metadata as metadata

    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        group = entry_points.select(group="pylint.checkers")
    else:
        group = entry_points.get("pylint.checkers", [])

    names = {entry_point.name for entry_point in group}
    assert "async_io_checker" in names, (
        f"Expected async_io_checker in pylint.checkers entry points. Found: {names}"
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


def test_pyproject_dependencies_are_pinned():
    """Verify required dependencies are pinned in pyproject.toml."""
    pyproject_path = Path("/app/pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()
    assert "pylint==3.0.3" in content, "pyproject.toml must pin pylint==3.0.3"
    assert "pytest==8.0.0" in content, "pyproject.toml must pin pytest==8.0.0"


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


def test_plugin_detects_requests_post():
    """Verify plugin detects requests.post in async functions."""
    test_file = Path("/tmp/test_requests_post.py")
    test_file.write_text("""
import requests

async def send():
    requests.post("https://example.com")
""")

    try:
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
            f"Plugin should detect requests.post. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_plugin_detects_input_call():
    """Verify plugin detects input() in async functions."""
    test_file = Path("/tmp/test_input.py")
    test_file.write_text("""
async def prompt():
    input("name?")
""")

    try:
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
            f"Plugin should detect input(). Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_plugin_detects_print_with_file():
    """Verify plugin detects print(file=...) in async functions."""
    test_file = Path("/tmp/test_print_file.py")
    test_file.write_text("""
import sys

async def log():
    print("hi", file=sys.stdout)
""")

    try:
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
            f"Plugin should detect print(file=...). Output: {output}"
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


def test_no_false_positive_in_to_thread():
    """Blocking calls inside asyncio.to_thread callbacks should NOT be flagged."""
    test_file = Path("/tmp/test_to_thread.py")
    test_file.write_text("""
import asyncio
import time

async def ok():
    await asyncio.to_thread(lambda: time.sleep(1))
""")
    
    try:
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
        blocking_messages = [line for line in output.split('\n') if 'blocking-io-in-async' in line]
        assert len(blocking_messages) == 0, (
            f"Blocking calls in to_thread should NOT be flagged. Found: {blocking_messages}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_aliased_imports():
    """Plugin should detect blocking calls even with import aliases."""
    test_file = Path("/tmp/test_alias.py")
    test_file.write_text("""
import requests as r

async def bad():
    r.get("https://example.com")
""")
    
    try:
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
            f"Plugin should detect r.get() as requests.get (aliased import). Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_flags_in_aenter():
    """Plugin should flag blocking calls in async context manager __aenter__."""
    test_file = Path("/tmp/test_aenter.py")
    test_file.write_text("""
import time

class AsyncCM:
    async def __aenter__(self):
        time.sleep(1)
        return self
    
    async def __aexit__(self, *args):
        pass
""")
    
    try:
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
            f"Plugin should detect blocking in __aenter__. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_flags_in_aexit():
    """Plugin should flag blocking calls in async context manager __aexit__."""
    test_file = Path("/tmp/test_aexit.py")
    test_file.write_text("""
import time

class AsyncCM:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        time.sleep(1)
""")

    try:
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
            f"Plugin should detect blocking in __aexit__. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_asyncio_coroutine_decorator():
    """Plugin should treat @asyncio.coroutine functions as async."""
    test_file = Path("/tmp/test_asyncio_coroutine.py")
    test_file.write_text(
        "import asyncio\n"
        "import time\n"
        "\n"
        "@asyncio.coroutine\n"
        "def legacy():\n"
        "    time.sleep(1)\n"
    )
    
    try:
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
            f"Plugin should detect blocking in @asyncio.coroutine functions. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_urllib_request_urlopen():
    """Plugin should detect urllib.request.urlopen in async functions."""
    test_file = Path("/tmp/test_urllib.py")
    test_file.write_text(
        "import urllib.request\n"
        "\n"
        "async def fetch():\n"
        "    urllib.request.urlopen(\"https://example.com\")\n"
    )
    
    try:
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
            f"Plugin should detect urllib.request.urlopen. Output: {output}"
        )
        assert "urllib.request.urlopen" in output or "urlopen" in output, (
            f"Warning should reference urlopen. Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_file_read_write():
    """Plugin should flag file.read() and file.write() in async functions."""
    test_file = Path("/tmp/test_file_ops.py")
    test_file.write_text(
        "async def file_ops():\n"
        "    f = open(\"data.txt\", \"w\")\n"
        "    f.write(\"hi\")\n"
        "    f.read()\n"
    )
    
    try:
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
        blocking_lines = [line for line in output.splitlines() if "blocking-io-in-async" in line]
        assert any("read" in line for line in blocking_lines), (
            f"Expected a blocking warning for file.read(). Output: {output}"
        )
        assert any("write" in line for line in blocking_lines), (
            f"Expected a blocking warning for file.write(). Output: {output}"
        )
    finally:
        if test_file.exists():
            test_file.unlink()


def test_config_enabled_false_disables_checker():
    """enabled=false in pyproject.toml should suppress warnings."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "pyproject.toml").write_text(
            "[tool.pylint.async_io_checker]\n"
            "enabled = false\n"
            "blocking_functions = [\"time.sleep\"]\n"
        )
        test_file = temp_path / "test_disabled.py"
        test_file.write_text(
            "import time\n"
            "\n"
            "async def run():\n"
            "    time.sleep(1)\n"
        )
        
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        assert "blocking-io-in-async" not in output, (
            f"Checker should be disabled via config. Output: {output}"
        )


def test_config_blocking_functions_override():
    """blocking_functions in pyproject.toml should be honored."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / "pyproject.toml").write_text(
            "[tool.pylint.async_io_checker]\n"
            "enabled = true\n"
            "blocking_functions = [\"math.sqrt\"]\n"
        )
        test_file = temp_path / "test_override.py"
        test_file.write_text(
            "import math\n"
            "\n"
            "async def run():\n"
            "    math.sqrt(9)\n"
        )
        
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        result = subprocess.run(
            ["python3", "-m", "pylint", "--load-plugins=async_io_checker", str(test_file)],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        assert "blocking-io-in-async" in output, (
            f"Custom blocking_functions should trigger warnings. Output: {output}"
        )


def test_warning_includes_line_and_column():
    """Warnings should include the line and column of the blocking call."""
    test_file = Path("/tmp/test_line_column.py")
    test_file.write_text(
        "import time\n"
        "\n"
        "async def run():\n"
        "    time.sleep(1)\n"
    )
    
    try:
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
        line_match = None
        for line in output.splitlines():
            if "blocking-io-in-async" in line:
                line_match = re.match(r"^.+:(\d+):(\d+): .*blocking-io-in-async", line)
                if line_match:
                    break
        
        assert line_match, f"Expected line/column in output. Output: {output}"
        line_no = int(line_match.group(1))
        col_no = int(line_match.group(2))
        assert line_no == 4, f"Expected blocking call on line 4, got {line_no}. Output: {output}"
        assert col_no == 4, f"Expected blocking call at column 4, got {col_no}. Output: {output}"
    finally:
        if test_file.exists():
            test_file.unlink()
