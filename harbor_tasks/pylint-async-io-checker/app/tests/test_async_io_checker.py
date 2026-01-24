# CANARY_STRING_PLACEHOLDER
"""Unit tests for async_io_checker plugin."""
from pathlib import Path
import sys

from pylint.lint import PyLinter
from pylint.reporters import CollectingReporter

# Add parent directory to path to import the plugin
sys.path.insert(0, str(Path(__file__).parent.parent))

from async_io_checker import AsyncIOChecker


def run_linter_on_code(test_code, tmp_path, monkeypatch=None, workdir=None):
    """Run pylint with the async_io_checker plugin and return collected messages."""
    if workdir is not None and monkeypatch is not None:
        monkeypatch.chdir(workdir)

    test_file = (workdir or tmp_path) / "test_input.py"
    test_file.write_text(test_code)

    linter = PyLinter()
    linter.set_reporter(CollectingReporter())
    checker = AsyncIOChecker(linter)
    linter.register_checker(checker)
    linter.check([str(test_file)])

    return linter.reporter.messages


def blocking_messages(messages):
    """Filter blocking-io-in-async messages."""
    return [m for m in messages if m.symbol == "blocking-io-in-async"]


def test_plugin_loads():
    """Test that the plugin can be loaded and initialized."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    assert checker is not None
    assert checker.name == "async-io-checker"
    assert checker.enabled is True


def test_detects_blocking_io_in_async_function(tmp_path):
    """Test that plugin detects blocking I/O in async functions."""
    test_code = (
        "import time\n"
        "import requests\n"
        "\n"
        "async def fetch_data():\n"
        "    time.sleep(1)\n"
        "    response = requests.get(\"https://example.com\")\n"
        "    return response.text\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 2


def test_detects_requests_post(tmp_path):
    """Test that plugin detects requests.post calls."""
    test_code = (
        "import requests\n"
        "\n"
        "async def send():\n"
        "    requests.post(\"https://example.com\")\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_no_false_positives_in_sync_function(tmp_path):
    """Test that plugin does not flag blocking I/O in sync functions."""
    test_code = (
        "import time\n"
        "\n"
        "def sync_function():\n"
        "    time.sleep(1)\n"
        "    return \"ok\"\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) == 0


def test_detects_open_in_async_function(tmp_path):
    """Test that plugin detects open() calls in async functions."""
    test_code = (
        "async def read_file():\n"
        "    with open(\"data.txt\", \"r\") as f:\n"
        "        return f.read()\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_detects_input_call(tmp_path):
    """Test that plugin detects input() calls in async functions."""
    test_code = (
        "async def prompt():\n"
        "    input(\"name?\")\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_detects_print_with_file(tmp_path):
    """Test that plugin detects print(file=...) calls in async functions."""
    test_code = (
        "import sys\n"
        "\n"
        "async def log():\n"
        "    print(\"hi\", file=sys.stdout)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_detects_file_read_write(tmp_path):
    """Test that plugin flags file.read() and file.write() calls."""
    test_code = (
        "async def file_ops():\n"
        "    f = open(\"data.txt\", \"w\")\n"
        "    f.write(\"hi\")\n"
        "    f.read()\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 3


def test_detects_asyncio_coroutine_decorator(tmp_path):
    """Test that @asyncio.coroutine functions are treated as async."""
    test_code = (
        "import asyncio\n"
        "import time\n"
        "\n"
        "@asyncio.coroutine\n"
        "def legacy():\n"
        "    time.sleep(1)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_detects_urllib_request_urlopen(tmp_path):
    """Test that plugin detects urllib.request.urlopen calls."""
    test_code = (
        "import urllib.request\n"
        "\n"
        "async def fetch():\n"
        "    urllib.request.urlopen(\"https://example.com\")\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_detects_aliased_imports(tmp_path):
    """Test that plugin detects blocking calls even with import aliases."""
    test_code = (
        "import requests as r\n"
        "\n"
        "async def bad():\n"
        "    r.get(\"https://example.com\")\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_no_false_positive_in_to_thread(tmp_path):
    """Blocking calls inside asyncio.to_thread callbacks should NOT be flagged."""
    test_code = (
        "import asyncio\n"
        "import time\n"
        "\n"
        "async def ok():\n"
        "    await asyncio.to_thread(lambda: time.sleep(1))\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) == 0


def test_flags_in_aenter(tmp_path):
    """Plugin should flag blocking calls in async context manager __aenter__."""
    test_code = (
        "import time\n"
        "\n"
        "class AsyncCM:\n"
        "    async def __aenter__(self):\n"
        "        time.sleep(1)\n"
        "        return self\n"
        "\n"
        "    async def __aexit__(self, *args):\n"
        "        pass\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_flags_in_aexit(tmp_path):
    """Plugin should flag blocking calls in async context manager __aexit__."""
    test_code = (
        "import time\n"
        "\n"
        "class AsyncCM:\n"
        "    async def __aenter__(self):\n"
        "        return self\n"
        "\n"
        "    async def __aexit__(self, *args):\n"
        "        time.sleep(1)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_configuration_enabled_false_disables_checker(tmp_path, monkeypatch):
    """enabled=false in pyproject.toml should disable warnings."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pylint.async_io_checker]\n"
        "enabled = false\n"
        "blocking_functions = [\"time.sleep\"]\n"
    )

    test_code = (
        "import time\n"
        "\n"
        "async def run():\n"
        "    time.sleep(1)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path, monkeypatch=monkeypatch, workdir=tmp_path)
    assert len(blocking_messages(messages)) == 0


def test_configuration_blocking_functions_override(tmp_path, monkeypatch):
    """blocking_functions in pyproject.toml should be honored."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pylint.async_io_checker]\n"
        "enabled = true\n"
        "blocking_functions = [\"math.sqrt\"]\n"
    )

    test_code = (
        "import math\n"
        "\n"
        "async def run():\n"
        "    math.sqrt(9)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path, monkeypatch=monkeypatch, workdir=tmp_path)
    assert len(blocking_messages(messages)) >= 1


def test_warning_includes_line_and_column(tmp_path):
    """Warnings should include correct line and column numbers."""
    test_code = (
        "import time\n"
        "\n"
        "async def run():\n"
        "    time.sleep(1)\n"
    )

    messages = run_linter_on_code(test_code, tmp_path)
    blocking = blocking_messages(messages)
    assert blocking, "Expected at least one blocking-io-in-async warning"

    msg = blocking[0]
    line_no = getattr(msg, "line", getattr(msg, "lineno", None))
    col_no = getattr(msg, "column", getattr(msg, "col", None))
    assert line_no == 4, f"Expected line 4, got {line_no}"
    assert col_no == 4, f"Expected column 4, got {col_no}"
