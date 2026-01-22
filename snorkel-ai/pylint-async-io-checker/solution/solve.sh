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
        self.blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen", "sleep"]
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
        if isinstance(node, astroid.FunctionDef) and node.is_async:
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
blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen", "sleep"]
TOML_EOF

echo "[oracle] Step 3: Writing comprehensive unit tests..."

mkdir -p tests
cat > tests/test_async_io_checker.py << 'PYTEST_EOF'
# CANARY_STRING_PLACEHOLDER
"""Unit tests for async_io_checker plugin."""
import pytest
import subprocess
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_pylint_with_plugin(test_file):
    """Run pylint with the async_io_checker plugin and return output."""
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
    return result.stdout + result.stderr


def test_plugin_loads():
    """Test that the plugin can be loaded and initialized."""
    from pylint.lint import PyLinter
    from async_io_checker import AsyncIOChecker
    
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    assert checker is not None
    assert checker.name == "async-io-checker"


def test_detects_blocking_io_in_async_function():
    """Test that plugin detects blocking I/O in async functions."""
    test_code = '''
import time
import requests

async def fetch_data():
    time.sleep(1)
    response = requests.get("https://example.com")
    return response.text
'''
    test_file = Path("/tmp/test_async_blocking.py")
    test_file.write_text(test_code)
    
    try:
        output = run_pylint_with_plugin(test_file)
        assert "blocking-io-in-async" in output
        assert "time.sleep" in output
        assert "requests.get" in output
    finally:
        test_file.unlink(missing_ok=True)


def test_no_false_positives_in_sync_function():
    """Test that plugin does not flag blocking I/O in sync functions."""
    test_code = '''
import time

def sync_function():
    time.sleep(1)
    return "ok"
'''
    test_file = Path("/tmp/test_sync.py")
    test_file.write_text(test_code)
    
    try:
        output = run_pylint_with_plugin(test_file)
        blocking_lines = [line for line in output.split('\n') if 'blocking-io-in-async' in line]
        assert len(blocking_lines) == 0
    finally:
        test_file.unlink(missing_ok=True)


def test_detects_open_in_async_function():
    """Test that plugin detects open() calls in async functions."""
    test_code = '''
async def read_file():
    with open("data.txt", "r") as f:
        return f.read()
'''
    test_file = Path("/tmp/test_open.py")
    test_file.write_text(test_code)
    
    try:
        output = run_pylint_with_plugin(test_file)
        assert "blocking-io-in-async" in output
        assert "open" in output
    finally:
        test_file.unlink(missing_ok=True)


def test_no_false_positive_in_to_thread():
    """Blocking calls inside asyncio.to_thread should NOT be flagged."""
    test_code = '''
import asyncio
import time

async def ok():
    await asyncio.to_thread(lambda: time.sleep(1))
'''
    test_file = Path("/tmp/test_to_thread.py")
    test_file.write_text(test_code)
    
    try:
        output = run_pylint_with_plugin(test_file)
        blocking_lines = [line for line in output.split('\n') if 'blocking-io-in-async' in line]
        assert len(blocking_lines) == 0, f"Expected 0 messages in to_thread callback. Got: {blocking_lines}"
    finally:
        test_file.unlink(missing_ok=True)


def test_detects_aliased_imports():
    """Should detect blocking calls even with import aliases."""
    test_code = '''
import requests as r

async def bad():
    r.get("https://example.com")
'''
    test_file = Path("/tmp/test_alias.py")
    test_file.write_text(test_code)
    
    try:
        output = run_pylint_with_plugin(test_file)
        assert "blocking-io-in-async" in output, f"Expected blocking detection for aliased import. Output: {output}"
    finally:
        test_file.unlink(missing_ok=True)
PYTEST_EOF

echo "[oracle] Step 4: Installing plugin dependencies..."

pip install --no-cache-dir toml==0.10.2

echo "[oracle] Step 5: Running unit tests to verify fixes..."

python -m pytest tests/test_async_io_checker.py -v

echo "[oracle] Solution complete - all difficulty layers implemented"
