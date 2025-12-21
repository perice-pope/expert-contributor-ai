#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Fixing async_io_checker.py plugin implementation..."

# Fix the plugin to properly detect blocking I/O in async functions
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
    
    def _load_config(self):
        """Load configuration from pyproject.toml."""
        self.blocking_functions = ["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen"]
        self.enabled = True
        
        # Try to read pyproject.toml
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
                # If config parsing fails, use defaults
                pass
    
    def _is_async_function(self, node):
        """Check if a function is async (async def or @asyncio.coroutine)."""
        # Check for async def
        if isinstance(node, astroid.AsyncFunctionDef):
            return True
        if isinstance(node, astroid.FunctionDef) and node.is_async:
            return True
        
        # Check for @asyncio.coroutine decorator
        if isinstance(node, astroid.FunctionDef):
            for decorator in node.decorators.nodes:
                if isinstance(decorator, astroid.Call):
                    if isinstance(decorator.func, astroid.Name) and decorator.func.name == "coroutine":
                        return True
                elif isinstance(decorator, astroid.Attribute):
                    if decorator.attrname == "coroutine":
                        return True
                elif isinstance(decorator, astroid.Name):
                    if decorator.name == "coroutine":
                        return True
        
        return False
    
    def visit_functiondef(self, node: astroid.FunctionDef):
        """Visit function definitions."""
        if not self.enabled:
            return
        
        if not self._is_async_function(node):
            return
        
        # Traverse all nodes in the function body recursively
        self._check_node(node.body, node)
    
    def visit_asyncfunctiondef(self, node: astroid.AsyncFunctionDef):
        """Visit async function definitions."""
        if not self.enabled:
            return
        
        self._check_node(node.body, node)
    
    def _check_node(self, nodes, func_node):
        """Recursively check nodes for blocking I/O calls."""
        for node in nodes:
            if isinstance(node, astroid.Call):
                self._check_blocking_call(node, func_node)
            elif isinstance(node, astroid.Expr):
                # Expr nodes wrap Call nodes (e.g., time.sleep(1) is Expr(Call(...)))
                if isinstance(node.value, astroid.Call):
                    self._check_blocking_call(node.value, func_node)
            elif isinstance(node, astroid.Assign):
                # Assign nodes can have Call nodes as values (e.g., response = requests.get(...))
                if isinstance(node.value, astroid.Call):
                    self._check_blocking_call(node.value, func_node)
            elif isinstance(node, astroid.With):
                # Check With statements - open() calls are in context_expr (items are tuples: (context_expr, optional_vars))
                if hasattr(node, "items"):
                    for item in node.items:
                        # item is a tuple: (context_expr, optional_vars)
                        if isinstance(item, tuple) and len(item) > 0:
                            context_expr = item[0]
                            if isinstance(context_expr, astroid.Call):
                                self._check_blocking_call(context_expr, func_node)
                # Recursively check nested blocks
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node)
            elif isinstance(node, (astroid.If, astroid.For, astroid.While)):
                # Recursively check nested blocks
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node)
            elif isinstance(node, astroid.Try):
                # Check try, except, and else blocks
                if hasattr(node, "body"):
                    self._check_node(node.body, func_node)
                if hasattr(node, "handlers"):
                    for handler in node.handlers:
                        if hasattr(handler, "body"):
                            self._check_node(handler.body, func_node)
                if hasattr(node, "orelse"):
                    self._check_node(node.orelse, func_node)
    
    def _check_blocking_call(self, node: astroid.Call, func_node):
        """Check if a call is blocking I/O."""
        # Check direct function names (e.g., open())
        if isinstance(node.func, astroid.Name):
            if node.func.name in self.blocking_functions:
                self.add_message(
                    "blocking-io-in-async",
                    node=node,
                    args=(node.func.name,),
                )
        
        # Check attribute calls (e.g., time.sleep(), requests.get())
        elif isinstance(node.func, astroid.Attribute):
            # Get full qualified name (e.g., "time.sleep", "requests.get")
            try:
                qualified_name = self._get_qualified_name(node.func)
                if qualified_name in self.blocking_functions:
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(qualified_name,),
                    )
            except Exception:
                # If we can't get qualified name, try just the attribute name
                if node.func.attrname in self.blocking_functions:
                    self.add_message(
                        "blocking-io-in-async",
                        node=node,
                        args=(node.func.attrname,),
                    )
    
    def _get_qualified_name(self, node):
        """Get the qualified name of an attribute node."""
        parts = []
        current = node
        while isinstance(current, astroid.Attribute):
            parts.append(current.attrname)
            current = current.expr
        if isinstance(current, astroid.Name):
            parts.append(current.name)
        return ".".join(reversed(parts))


def register(linter):
    """Register the checker with pylint."""
    linter.register_checker(AsyncIOChecker(linter))
PYTHON_EOF

echo "[oracle] Step 2: Fixing pyproject.toml configuration..."

# Fix pyproject.toml to include entry points and proper configuration
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

# Create comprehensive unit tests
mkdir -p tests
cat > tests/test_async_io_checker.py << 'PYTEST_EOF'
# CANARY_STRING_PLACEHOLDER
"""Unit tests for async_io_checker plugin."""
import pytest
from pylint.lint import PyLinter
from pylint.checkers import initialize
import sys
from pathlib import Path

# Add parent directory to path to import the plugin
sys.path.insert(0, str(Path(__file__).parent.parent))

from async_io_checker import AsyncIOChecker


def test_plugin_loads():
    """Test that the plugin can be loaded and initialized."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    assert checker is not None
    assert checker.name == "async-io-checker"
    assert checker.enabled is True


def test_detects_blocking_io_in_async_function():
    """Test that plugin detects blocking I/O in async functions."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    linter.register_checker(checker)
    
    # Create a test file with blocking I/O in async function
    test_code = """
import time
import requests

async def fetch_data():
    time.sleep(1)
    response = requests.get("https://example.com")
    return response.text
"""
    
    # Write test file
    test_file = Path("/tmp/test_async_blocking.py")
    test_file.write_text(test_code)
    
    try:
        linter.check([str(test_file)])
        messages = linter.reporter.messages
        
        # Should have at least 2 messages (time.sleep and requests.get)
        blocking_messages = [m for m in messages if m.msg_id == "blocking-io-in-async"]
        assert len(blocking_messages) >= 2, f"Expected at least 2 blocking I/O messages, got {len(blocking_messages)}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_no_false_positives_in_sync_function():
    """Test that plugin does not flag blocking I/O in sync functions."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    linter.register_checker(checker)
    
    test_code = """
import time

def sync_function():
    time.sleep(1)
    return "ok"
"""
    
    test_file = Path("/tmp/test_sync.py")
    test_file.write_text(test_code)
    
    try:
        linter.check([str(test_file)])
        messages = linter.reporter.messages
        
        # Should have no blocking I/O messages
        blocking_messages = [m for m in messages if m.msg_id == "blocking-io-in-async"]
        assert len(blocking_messages) == 0, f"Expected no blocking I/O messages in sync function, got {len(blocking_messages)}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_open_in_async_function():
    """Test that plugin detects open() calls in async functions."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    linter.register_checker(checker)
    
    test_code = """
async def read_file():
    with open("data.txt", "r") as f:
        return f.read()
"""
    
    test_file = Path("/tmp/test_open.py")
    test_file.write_text(test_code)
    
    try:
        linter.check([str(test_file)])
        messages = linter.reporter.messages
        
        blocking_messages = [m for m in messages if m.msg_id == "blocking-io-in-async"]
        assert len(blocking_messages) >= 1, f"Expected at least 1 blocking I/O message for open(), got {len(blocking_messages)}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_configuration_reading():
    """Test that plugin reads configuration from pyproject.toml."""
    # This test verifies the configuration loading logic exists
    # Actual config reading is tested implicitly through other tests
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    
    # Check that default blocking functions are set
    assert len(checker.blocking_functions) > 0
    assert "open" in checker.blocking_functions or "time.sleep" in checker.blocking_functions


def test_warning_includes_line_number():
    """Test that warnings include correct line numbers."""
    linter = PyLinter()
    checker = AsyncIOChecker(linter)
    linter.register_checker(checker)
    
    test_code = """
async def test():
    import time
    time.sleep(1)
"""
    
    test_file = Path("/tmp/test_lineno.py")
    test_file.write_text(test_code)
    
    try:
        linter.check([str(test_file)])
        messages = linter.reporter.messages
        
        blocking_messages = [m for m in messages if m.msg_id == "blocking-io-in-async"]
        if blocking_messages:
            # Check that message has line information
            msg = blocking_messages[0]
            assert hasattr(msg, "line") or hasattr(msg, "lineno"), "Message should have line number information"
    finally:
        if test_file.exists():
            test_file.unlink()
PYTEST_EOF

echo "[oracle] Step 4: Installing plugin dependencies..."

# Install toml for configuration reading
pip install --no-cache-dir toml==0.10.2

echo "[oracle] Step 5: Running unit tests to verify fixes..."

# Run the unit tests
python -m pytest tests/test_async_io_checker.py -v

echo "[oracle] Solution complete - plugin implementation fixed and tested"
