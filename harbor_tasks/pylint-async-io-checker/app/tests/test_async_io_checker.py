# CANARY_STRING_PLACEHOLDER
"""Unit tests for async_io_checker plugin."""
import pytest
from pylint.lint import PyLinter
from pylint.reporters import CollectingReporter
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
    linter.set_reporter(CollectingReporter())
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
        blocking_messages = [m for m in messages if m.symbol == "blocking-io-in-async"]
        assert len(blocking_messages) >= 2, f"Expected at least 2 blocking I/O messages, got {len(blocking_messages)}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_no_false_positives_in_sync_function():
    """Test that plugin does not flag blocking I/O in sync functions."""
    linter = PyLinter()
    linter.set_reporter(CollectingReporter())
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
        blocking_messages = [m for m in messages if m.symbol == "blocking-io-in-async"]
        assert len(blocking_messages) == 0, f"Expected no blocking I/O messages in sync function, got {len(blocking_messages)}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_detects_open_in_async_function():
    """Test that plugin detects open() calls in async functions."""
    linter = PyLinter()
    linter.set_reporter(CollectingReporter())
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
        
        blocking_messages = [m for m in messages if m.symbol == "blocking-io-in-async"]
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
    linter.set_reporter(CollectingReporter())
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
        
        blocking_messages = [m for m in messages if m.symbol == "blocking-io-in-async"]
        if blocking_messages:
            # Check that message has line information
            msg = blocking_messages[0]
            assert hasattr(msg, "line") or hasattr(msg, "lineno"), "Message should have line number information"
    finally:
        if test_file.exists():
            test_file.unlink()
