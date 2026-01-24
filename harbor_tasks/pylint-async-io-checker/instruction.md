# Create Pylint Plugin for Async I/O Detection

A development team is experiencing performance issues in their async Python codebase. Blocking I/O operations (like file operations, network calls, or sleep) are being called directly inside async functions, causing the entire event loop to block. Your task is to create a Pylint plugin that automatically detects these blocking I/O calls in async functions and suggests wrapping them with `asyncio.to_thread()`.

## Requirements

1. **Create a Pylint plugin class**: Implement a Pylint checker class in `/app/async_io_checker.py` that inherits from `pylint.checkers.BaseChecker` and uses AST parsing to detect blocking I/O calls.

2. **Detect blocking I/O in async functions**: The plugin must identify blocking I/O operations inside functions decorated with `@asyncio.coroutine`, `async def`, or async context manager methods such as `__aenter__`/`__aexit__`. Blocking I/O includes:
   - Built-in functions: `open()`, `input()`, `print()` (when used for file I/O)
   - Standard library calls: `time.sleep()`, `requests.get()`, `requests.post()`, `urllib.request.urlopen()`
   - File operations: `file.read()`, `file.write()` (when not using `aiofiles` or similar)
   - Any function call that matches configured blocking patterns
   - Aliased imports should still be detected (e.g., `import requests as r` then `r.get(...)`)
   - Calls inside `asyncio.to_thread(...)` callbacks should NOT be flagged as blocking

3. **Emit warnings with suggestions**: For each detected blocking I/O call, emit a Pylint message with:
   - Message ID: `blocking-io-in-async`
   - Suggested fix: Wrap the call with `await asyncio.to_thread(...)`
   - Include line number and column of the blocking call

4. **Support configuration via pyproject.toml**: The plugin must read configuration from `pyproject.toml` under `[tool.pylint.async_io_checker]`:
   - `blocking_functions`: List of function names to treat as blocking (default: `["open", "time.sleep", "requests.get", "requests.post", "urllib.request.urlopen"]`)
   - `enabled`: Boolean to enable/disable the checker (default: `true`)

5. **Make plugin installable**: Configure `pyproject.toml` to:
   - Define the plugin as a Pylint extension
   - Include proper entry points for Pylint to discover the plugin
   - Specify required dependencies (pylint with pinned version)

6. **Write unit tests**: Create comprehensive unit tests in `/app/tests/test_async_io_checker.py` that verify:
   - Detection of blocking I/O in async functions
   - No false positives for non-blocking calls
   - Configuration reading from pyproject.toml
   - Warning messages include correct line numbers and suggestions

## Constraints

- **Use Python 3.11+**
- **Pylint version**: Pin to `pylint==3.0.3` (or compatible version)
- **No external network calls**: All operations must work offline
- **Do not modify Pylint core**: Only create a plugin, do not patch Pylint itself
- **Follow Pylint plugin conventions**: Use `pylint.checkers.BaseChecker` and register messages properly
- **Tests must use pytest**: Write tests using pytest with version pinned to `pytest==8.0.0`

## Files

- Plugin implementation: `/app/async_io_checker.py` (starter code with bugs)
- Configuration: `/app/pyproject.toml` (incomplete configuration)
- Unit tests: `/app/tests/test_async_io_checker.py` (incomplete or missing tests)
- Test fixtures: `/app/tests/fixtures/` (sample Python files for testing)

## Outputs

- `/app/async_io_checker.py` (complete Pylint plugin implementation)
- `/app/pyproject.toml` (complete configuration with entry points and dependencies)
- `/app/tests/test_async_io_checker.py` (complete unit test suite)
- `/app/tests/fixtures/*.py` (test fixture files if needed)

## Verification

The plugin will be verified by:
1. Running Pylint with the plugin on test files containing async functions with blocking I/O
2. Verifying that warnings are emitted with correct message IDs and suggestions
3. Running the unit test suite and verifying all tests pass
4. Verifying configuration is read correctly from pyproject.toml
