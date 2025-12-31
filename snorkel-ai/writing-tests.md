# Writing Tests

`tests/test_outputs.py` should verify task completion with clear, behavior-focused pytest tests.

## Basic Structure
```python
"""Tests for the data processing task."""
import json
from pathlib import Path


def test_output_file_exists():
    """Verify the output file was created."""
    assert Path("/output/result.json").exists()


def test_output_format():
    """Verify the output has correct JSON structure."""
    with open("/output/result.json") as f:
        data = json.load(f)

    assert "status" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_correct_count():
    """Verify the item count is correct."""
    with open("/output/result.json") as f:
        data = json.load(f)

    assert len(data["items"]) == 42
```

## Key Principles

### 1) Test behavior, not implementation
```python
# Good
def test_function_handles_empty_input():
    """Empty input should return empty list."""
    from app.main import process
    assert process("") == []

# Bad (brittle)
def test_has_empty_check():
    """Check if code has empty input handling."""
    source = open("/app/main.py").read()
    assert "if not" in source
```

### 2) Informative docstrings
Every test needs a docstring explaining the behavior it checks (CI enforces this).

```python
def test_api_returns_json():
    """API endpoint should return valid JSON with Content-Type header."""
    response = requests.get("http://localhost:8080/api/data")
    assert response.headers["Content-Type"] == "application/json"
    assert response.json()
```

### 3) Match task requirements
Map each instruction to a test, e.g.:
- "Return empty list for empty input" → `test_empty_input_returns_empty_list`
- "Output to /data/result.csv" → `test_output_file_exists`
- "Include header row" → `test_csv_has_header`

### 4) Cover edge cases
```python
def test_empty_input():
    """Empty input is handled gracefully."""
    assert process("") == []

def test_single_item():
    """Single item input works correctly."""
    assert process("a") == ["a"]

def test_large_input():
    """Large input is handled efficiently."""
    result = process("x" * 10_000)
    assert len(result) == 10_000

def test_special_characters():
    """Special characters are preserved."""
    assert process("héllo 世界") == ["héllo", "世界"]
```

## tests/test.sh
Install deps, run pytest, and emit the reward file.

```bash
#!/bin/bash
cd /tests

uv venv
source .venv/bin/activate
uv pip install pytest requests

pytest test_outputs.py -v

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

Install test-only dependencies here, not in the Dockerfile. The script must produce `/logs/verifier/reward.txt` or `/logs/verifier/reward.json`.

### ⚠️ CRITICAL: Reward Output Requirements (MANDATORY)

**Rewards must be binary (0 or 1 only):**
- ✅ `1` = All tests pass
- ❌ `0` = Any test fails
- 🚫 **PARTIAL REWARDS ARE EXPLICITLY FORBIDDEN** (no 0.25, 0.5, 0.75, etc.)

**Required pattern:**
Every `test.sh` file MUST use this exact logic:
```bash
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

**Enforcement:**
- Submissions are checked to ensure every `test.sh` contains this exact pattern
- Any `test.sh` that does not use this exact logic, or assigns partial rewards in any way, will be blocked
- This is a hard check in the task skeleton and submission validation

## Common Patterns

### Testing file output
```python
def test_csv_output():
    """Verify CSV output format and content."""
    import csv

    with open("/output/data.csv") as f:
        rows = list(csv.DictReader(f))

    assert rows
    assert "id" in rows[0]
    assert "name" in rows[0]
```

### Testing API endpoints
```python
import requests

def test_health_endpoint():
    """Health check endpoint returns 200."""
    response = requests.get("http://localhost:8080/health")
    assert response.status_code == 200

def test_api_error_handling():
    """Invalid requests return 400."""
    response = requests.post(
        "http://localhost:8080/api/data",
        json={"invalid": "data"}
    )
    assert response.status_code == 400
```

### Testing database state
```python
import sqlite3

def test_database_populated():
    """Database contains expected records."""
    conn = sqlite3.connect("/app/data.db")
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    assert count == 100
```

### Testing command output
```python
import subprocess

def test_cli_help():
    """CLI shows help message."""
    result = subprocess.run(
        ["python", "/app/cli.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
```

## Anti-Patterns to Avoid

### Brittle string matching
```python
# BAD
def test_output():
    output = open("/output/log.txt").read()
    assert output == "Processing complete\n"

# GOOD
def test_output():
    output = open("/output/log.txt").read()
    assert "complete" in output.lower()
```

### Hardcoded random values
```python
# BAD
def test_random():
    result = generate_random()
    assert result == 42

# GOOD
def test_random():
    result = generate_random()
    assert 1 <= result <= 100
```

### Order-dependent tests
```python
# BAD
def test_1_setup():
    global data
    data = load_data()

def test_2_process():
    process(data)

# GOOD
def test_process():
    data = load_data()
    result = process(data)
    assert result is not None
```

## CI Validation
Checks include:
- `behavior_in_tests`: all requirements have tests.
- `behavior_in_task_description`: tests align with `instruction.md`.
- `informative_test_docstrings`: every test has a docstring.
- `ruff`: code passes linting.