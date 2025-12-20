# Maintainer Notes

## What this task is testing

Agents must create a complete Pylint plugin that:
1. Uses AST parsing (via astroid) to detect blocking I/O calls in async functions
2. Emits warnings with helpful suggestions (asyncio.to_thread)
3. Supports configuration via pyproject.toml
4. Is properly installable as a Pylint extension via entry points
5. Includes comprehensive unit tests

The task requires understanding of:
- Pylint plugin architecture (BaseChecker, IAstroidChecker interface)
- Astroid AST traversal and node types
- Python async/await syntax and decorators
- pyproject.toml configuration and entry points
- pytest testing framework
- Recursive AST traversal for nested code blocks

## Intended failure modes

### 1. Incomplete AST traversal
- **Shallow fix**: Only checking top-level function calls, missing nested calls in if/for/while blocks
- **Pattern**: Using simple `for child in node.body: if isinstance(child, Call): check()` without recursion
- **Why it fails**: Blocking I/O often occurs inside conditional blocks or loops; shallow traversal misses these
- **Test catches**: `test_plugin_detects_blocking_io` may pass for simple cases but fail for nested calls

### 2. Missing attribute call handling
- **Shallow fix**: Only checking `astroid.Name` nodes (direct function calls like `open()`), missing `astroid.Attribute` nodes
- **Pattern**: `if isinstance(node.func, astroid.Name): check(node.func.name)` without handling `time.sleep()`, `requests.get()`
- **Why it fails**: Most blocking I/O uses qualified names (module.function), not bare names
- **Test catches**: `test_plugin_detects_blocking_io` fails because `time.sleep()` and `requests.get()` aren't detected

### 3. Incorrect async function detection
- **Shallow fix**: Only checking `node.is_async`, missing `@asyncio.coroutine` decorator
- **Pattern**: `if not node.is_async: return` without checking decorators
- **Why it fails**: Old-style coroutines use decorators, not `async def` syntax
- **Test catches**: Tests with `@asyncio.coroutine` decorator fail to trigger warnings

### 4. Missing entry points in pyproject.toml
- **Shallow fix**: Adding plugin code but forgetting entry points registration
- **Pattern**: Plugin exists but Pylint can't discover it because `[project.entry-points."pylint.checkers"]` is missing
- **Why it fails**: Pylint requires entry points to load plugins; without them, plugin is never registered
- **Test catches**: `test_pyproject_toml_has_entry_points` fails, plugin doesn't load

### 5. Configuration not read from pyproject.toml
- **Shallow fix**: Hardcoding blocking functions list, not reading from config
- **Pattern**: `self.blocking_functions = ["open"]` without `_load_config()` method
- **Why it fails**: Task requires configurable blocking functions; hardcoded list doesn't meet requirements
- **Test catches**: `test_pyproject_toml_has_configuration` may pass, but functionality doesn't use config

### 6. Incomplete unit tests
- **Shallow fix**: Writing minimal tests that don't cover edge cases
- **Pattern**: Only testing simple `async def` with one blocking call, missing nested blocks, decorators, etc.
- **Why it fails**: Tests don't verify all requirements (nested calls, decorators, config reading)
- **Test catches**: `test_unit_tests_pass` may pass, but `test_plugin_detects_blocking_io` fails for complex cases

### 7. Wrong qualified name extraction
- **Shallow fix**: Using `node.func.attrname` directly without building full qualified name
- **Pattern**: Checking `if node.func.attrname == "sleep"` instead of `if qualified_name == "time.sleep"`
- **Why it fails**: Multiple modules may have functions with same name; qualified name is needed for accurate detection
- **Test catches**: May cause false positives or miss qualified calls

### 8. Missing recursive traversal for control structures
- **Shallow fix**: Not traversing body of if/for/while/try blocks
- **Pattern**: Only checking `node.body` at function level, not recursively
- **Why it fails**: Blocking I/O often occurs inside conditional logic or error handling
- **Test catches**: Tests with nested blocking calls fail

### 9. Incorrect message format
- **Shallow fix**: Warning message doesn't include suggestion for asyncio.to_thread
- **Pattern**: Generic message like "Blocking I/O detected" without specific fix suggestion
- **Why it fails**: Task explicitly requires suggesting `asyncio.to_thread()` wrapper
- **Test catches**: `test_warnings_include_suggestions` fails

### 10. Missing pytest dependency
- **Shallow fix**: Writing tests but not adding pytest to pyproject.toml dependencies
- **Pattern**: Tests exist but can't run because pytest isn't installed
- **Why it fails**: Unit tests are required but can't execute without pytest
- **Test catches**: `test_unit_tests_pass` fails with import error

## Why tests are designed this way

### Behavioral validation over implementation checking
- Tests verify the **plugin behavior** (detects blocking I/O, emits warnings, reads config)
- Tests don't check specific implementation details (allows multiple valid approaches to AST traversal)
- Tests verify plugin integration with Pylint (can be loaded, registered, and used)

### Integration testing
- Tests run Pylint with the plugin on actual Python files (not just unit tests)
- Tests verify end-to-end behavior: plugin loads → detects issues → emits warnings
- Tests check both positive cases (detection) and negative cases (no false positives)

### Configuration verification
- Tests verify pyproject.toml structure (entry points, config section)
- Tests don't require specific config values (flexible on defaults, strict on structure)
- Tests verify plugin can read and use configuration

### Comprehensive coverage
- Tests cover async functions, sync functions, nested calls, different I/O types
- Tests verify both detection accuracy and suggestion quality
- Tests ensure plugin is properly installable and discoverable

## Determinism and reproducibility

### Fixed dependencies
- Pylint version pinned: `pylint==3.0.3`
- pytest version pinned: `pytest==8.0.0`
- toml version pinned: `toml==0.10.2`
- Python version pinned: `python:3.11-slim-bookworm`

### No external dependencies
- All operations work offline (no network calls)
- Test files are created dynamically in /tmp (no external fixtures)
- No time-dependent behavior

### Deterministic AST parsing
- Astroid parsing is deterministic (same code produces same AST)
- Plugin behavior is deterministic (same input produces same warnings)
- Test outcomes are deterministic (same plugin code produces same test results)

### Idempotent operations
- Plugin registration is idempotent
- Configuration reading is idempotent
- Test execution is idempotent

## Task difficulty knobs

### Easy mode (not used here)
- Single blocking function type (e.g., only `open()`)
- Simple async functions (no nested blocks)
- No configuration required
- Minimal unit tests

### Medium mode (could be)
- Multiple blocking function types
- Nested code blocks
- Basic configuration
- Standard unit tests

### Hard mode (current)
- Multiple blocking function types with qualified names
- Recursive AST traversal for nested blocks
- Configuration reading from pyproject.toml
- Entry points registration
- Comprehensive unit tests
- Detection of both `async def` and `@asyncio.coroutine`
- Proper qualified name extraction

### Harder variants (future)
- Support for async context managers
- Detection of blocking I/O in async generators
- Custom blocking function patterns (regex-based)
- Multiple configuration sources
- Performance optimization for large codebases
- Integration with type checkers

## Expected agent behavior

**Good agents will:**
1. Understand Pylint plugin architecture (BaseChecker, entry points)
2. Implement recursive AST traversal for nested code blocks
3. Handle both `astroid.Name` and `astroid.Attribute` node types
4. Detect async functions via both `is_async` and decorator checking
5. Extract qualified names correctly (e.g., "time.sleep", "requests.get")
6. Read configuration from pyproject.toml using toml library
7. Add proper entry points to pyproject.toml
8. Write comprehensive unit tests covering edge cases
9. Test plugin integration with Pylint on real files
10. Ensure warnings include helpful suggestions

**Weak agents will:**
1. Only check top-level function calls (miss nested blocks)
2. Only handle `astroid.Name` nodes (miss `time.sleep()`, `requests.get()`)
3. Only check `node.is_async` (miss `@asyncio.coroutine` decorator)
4. Hardcode blocking functions list (don't read from config)
5. Forget entry points in pyproject.toml (plugin doesn't load)
6. Write minimal tests that don't cover edge cases
7. Use wrong qualified name extraction (false positives/negatives)
8. Skip recursive traversal (miss blocking calls in if/for/while blocks)
9. Generic warning messages without specific suggestions
10. Missing pytest dependency (tests can't run)

## Known issues and limitations

- Pylint 3.0.3 API may differ slightly from other versions; solution is tested against this version
- Astroid node types and traversal patterns are specific to Pylint's AST library
- Configuration reading requires toml library (not in stdlib for Python 3.11)
- Entry points format is specific to setuptools/pip installation method
- Plugin discovery requires proper entry points; manual loading with `--load-plugins` also works
- Some edge cases (e.g., dynamically constructed function calls) may not be detected

