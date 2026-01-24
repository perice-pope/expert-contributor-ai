#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Fixing async_io_checker.py plugin implementation..."

# Fix the plugin with all difficulty layers:
# 1. Thread-offload scope exemption (to_thread, run_in_executor)
# 2. Import alias resolution
# 3. Async context manager methods + async generators
cat > async_io_checker.py << 'PYTHON_EOF'
# CANARY_STRING_PLACEHOLDER
"""Pylint plugin to detect blocking I/O in async functions."""
import astroid
import toml
from pathlib import Path
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


class AsyncIOChecker(BaseChecker):
    """Checker for blocking I/O operations in async functions."""
    name = "async-io-checker"
    priority = -1
    msgs = {
        "E9001": (
            "Blocking I/O call '%s' in async function. Consider wrapping with 'await asyncio.to_thread(...)'",
            "blocking-io-in-async",
            "Blocking I/O detected in async context",
        ),
    }
    
    def __init__(self, linter: PyLinter):
        super().__init__(linter)
        self._load_config()
        # Import alias map: {local_name: fully_qualified_name}
        self._import_map = {}
    
    def _load_config(self):
        """Load configuration from pyproject.toml."""
        self.blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen"]
        self.enabled = True
        
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            pyproject_path = Path("/app/pyproject.toml")
        
        if pyproject_path.exists():
            try:
                config = toml.load(pyproject_path)
                checker_config = config.get("tool", {}).get("pylint", {}).get("async_io_checker", {})
                
                if "blocking_functions" in checker_config:
                    self.blocking_functions = checker_config["blocking_functions"]
                if "enabled" in checker_config:
                    self.enabled = checker_config["enabled"]
            except Exception:
                pass
    
    def visit_module(self, node):
        """Visit module to build import alias map."""
        self._import_map = {}
        for child in node.body:
            if isinstance(child, astroid.Import):
                # import requests as r -> {r: requests}
                for name, alias in child.names:
                    local_name = alias if alias else name
                    self._import_map[local_name] = name
            elif isinstance(child, astroid.ImportFrom):
                # from time import sleep as s -> {s: time.sleep}
                module = child.modname or ""
                for name, alias in child.names:
                    local_name = alias if alias else name
                    full_name = f"{module}.{name}" if module else name
                    self._import_map[local_name] = full_name
    
    def visit_functiondef(self, node: astroid.FunctionDef):
        """Visit function definitions."""
        if not self.enabled:
            return
        
        if not self._is_async_function(node):
            return
        
        self._check_node(node.body, node, in_offload=False)
    
    def visit_asyncfunctiondef(self, node: astroid.AsyncFunctionDef):
        """Visit async function definitions."""
        if not self.enabled:
            return
        
        self._check_node(node.body, node, in_offload=False)
    
    def _is_async_function(self, node):
        """Check if a function is async."""
        if isinstance(node, astroid.AsyncFunctionDef):
            return True
        if isinstance(node, astroid.FunctionDef) and getattr(node, "is_async", False):
            return True
        # Check for @asyncio.coroutine decorator
        if isinstance(node, astroid.FunctionDef) and node.decorators:
            for decorator in node.decorators.nodes:
                if isinstance(decorator, astroid.Attribute) and decorator.attrname == "coroutine":
                    return True
                if isinstance(decorator, astroid.Name) and decorator.name == "coroutine":
                    return True
        return False
    
    def _is_offload_call(self, node):
        """Check if this is a call to asyncio.to_thread or run_in_executor."""
        if not isinstance(node, astroid.Call):
            return False
        
        # Check asyncio.to_thread(...)
        if isinstance(node.func, astroid.Attribute):
            if node.func.attrname in ("to_thread", "run_in_executor"):
                return True
        
        # Check to_thread(...) if imported directly
        if isinstance(node.func, astroid.Name):
            if node.func.name in ("to_thread", "run_in_executor"):
                return True
        
        return False
    
    def _get_offload_callback(self, node):
        """Get the callback argument from to_thread/run_in_executor call."""
        if not node.args:
            return None
        
        # to_thread(func, ...) - first arg is the callback
        if isinstance(node.func, astroid.Attribute) and node.func.attrname == "to_thread":
            return node.args[0] if node.args else None
        
        # run_in_executor(executor, func, ...) - second arg is the callback
        if isinstance(node.func, astroid.Attribute) and node.func.attrname == "run_in_executor":
            return node.args[1] if len(node.args) > 1 else None
        
        # Direct import case
        if isinstance(node.func, astroid.Name):
            if node.func.name == "to_thread":
                return node.args[0] if node.args else None
            if node.func.name == "run_in_executor":
                return node.args[1] if len(node.args) > 1 else None
        
        return None
    
    def _check_node(self, nodes, func_node, in_offload=False):
        """Recursively check nodes for blocking I/O calls."""
        for node in nodes:
            # Handle offload calls - traverse callback with in_offload=True
            if isinstance(node, astroid.Expr) and isinstance(node.value, astroid.Await):
                await_value = node.value.value
                if self._is_offload_call(await_value):
                    callback = self._get_offload_callback(await_value)
                    if callback and isinstance(callback, astroid.Lambda):
                        # Lambda body is single expression
                        self._check_node([callback.body], func_node, in_offload=True)
                    elif callback and isinstance(callback, astroid.Name):
                        # Named function passed - we can't easily trace it, skip
                        pass
                    continue
            
            if isinstance(node, astroid.Call):
                # Check if this is an offload call
                if self._is_offload_call(node):
                    callback = self._get_offload_callback(node)
                    if callback and isinstance(callback, astroid.Lambda):
                        self._check_node([callback.body], func_node, in_offload=True)
                    continue
                
                # Only flag if NOT inside offload callback
                if not in_offload:
                    self._check_blocking_call(node, func_node)
            
            elif isinstance(node, astroid.Expr):
                if isinstance(node.value, astroid.Call):
                    if self._is_offload_call(node.value):
                        callback = self._get_offload_callback(node.value)
                        if callback and isinstance(callback, astroid.Lambda):
                            self._check_node([callback.body], func_node, in_offload=True)
                        continue
                    if not in_offload:
                        self._check_blocking_call(node.value, func_node)
                elif isinstance(node.value, astroid.Await):
                    # Check the awaited value
                    if isinstance(node.value.value, astroid.Call):
                        if self._is_offload_call(node.value.value):
                            continue
                        if not in_offload:
                            self._check_blocking_call(node.value.value, func_node)
            
            elif isinstance(node, astroid.Assign):
                if isinstance(node.value, astroid.Call):
                    if not in_offload:
                        self._check_blocking_call(node.value, func_node)
            
            elif isinstance(node, astroid.With):
                # Check context expressions
                if hasattr(node, "items"):
                    for item in node.items:
                        if isinstance(item, tuple) and len(item) > 0:
                            context_expr = item[0]
                            if isinstance(context_expr, astroid.Call):
                                if not in_offload:
                                    self._check_blocking_call(context_expr, func_node)
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node, in_offload)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node, in_offload)
            
            elif isinstance(node, astroid.AsyncWith):
                # Async with - also check body
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node, in_offload)
            
            elif isinstance(node, (astroid.If, astroid.For, astroid.While)):
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node, in_offload)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node, in_offload)
            
            elif isinstance(node, astroid.Try):
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node, in_offload)
                if hasattr(node, "handlers"):
                    for handler in node.handlers:
                        if hasattr(handler, "body"):
                            self._check_node(handler.body, func_node, in_offload)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node, in_offload)
                if hasattr(node, "finalbody"):
                    self._check_node(node.finalbody, func_node, in_offload)
    
    def _check_blocking_call(self, node: astroid.Call, func_node):
        """Check if a call is blocking I/O."""
        # Check direct function names (e.g., open(), sleep())
        if isinstance(node.func, astroid.Name):
            func_name = node.func.name

            if func_name == "input":
                self.add_message(
                    "blocking-io-in-async",
                    node=node,
                    args=(func_name,),
                )
                return

            if func_name == "print":
                keywords = node.keywords or []
                if any(keyword.arg == "file" for keyword in keywords):
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(func_name,),
                    )
                    return
            
            # Resolve alias to fully qualified name
            resolved = self._import_map.get(func_name, func_name)
            
            # Check if resolved name or any suffix matches blocking list
            if resolved in self.blocking_functions or func_name in self.blocking_functions:
                self.add_message(
                    "blocking-io-in-async",
                    node=node,
                    args=(resolved,),
                )
                return
            
            # Check if it's a suffix match (e.g., "time.sleep" matches "sleep")
            for blocking in self.blocking_functions:
                if blocking.endswith(f".{func_name}") or blocking == func_name:
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(resolved,),
                    )
                    return
        
        # Check attribute calls (e.g., time.sleep(), requests.get(), r.get())
        elif isinstance(node.func, astroid.Attribute):
            try:
                qualified_name = self._get_qualified_name(node.func)
                if qualified_name in self.blocking_functions:
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(qualified_name,),
                    )
                    return

                attr_name = node.func.attrname
                if attr_name in ("read", "write"):
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(qualified_name,),
                    )
                    return

                for blocking in self.blocking_functions:
                    if blocking == attr_name or blocking.endswith(f".{attr_name}"):
                        self.add_message(
                            "blocking-io-in-async",
                            node=node,
                            args=(qualified_name,),
                        )
                        return
            except Exception:
                pass
    
    def _get_qualified_name(self, node):
        """Get the qualified name, resolving import aliases."""
        parts = []
        current = node
        while isinstance(current, astroid.Attribute):
            parts.append(current.attrname)
            current = current.expr
        
        if isinstance(current, astroid.Name):
            base_name = current.name
            # Resolve alias
            resolved_base = self._import_map.get(base_name, base_name)
            parts.append(resolved_base)
        
        return ".".join(reversed(parts))


def register(linter):
    """Register the checker with pylint."""
    linter.register_checker(AsyncIOChecker(linter))
PYTHON_EOF

echo "[oracle] Step 2: Fixing pyproject.toml configuration..."

cat > pyproject.toml << 'TOML_EOF'
# CANARY_STRING_PLACEHOLDER
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pylint-async-io-checker"
version = "0.1.0"
description = "Pylint plugin to detect blocking I/O in async functions"
requires-python = ">=3.11"
dependencies = [
    "pylint==3.0.3",
    "pytest==8.0.0",
    "toml==0.10.2",
]

[project.entry-points."pylint.checkers"]
async_io_checker = "async_io_checker:AsyncIOChecker"

[tool.pylint.async_io_checker]
enabled = true
blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen"]
TOML_EOF

echo "[oracle] Step 3: Writing comprehensive unit tests..."

mkdir -p tests
cat > tests/test_async_io_checker.py << 'PYTEST_EOF'
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
    """Blocking calls inside asyncio.to_thread should NOT be flagged."""
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
PYTEST_EOF

echo "[oracle] Step 4: Installing plugin dependencies..."

pip install --no-cache-dir toml==0.10.2

echo "[oracle] Step 5: Running unit tests to verify fixes..."

python -m pytest tests/test_async_io_checker.py -v

echo "[oracle] Solution complete - all difficulty layers implemented"
