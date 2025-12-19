# Writing Task Instructions and Configuration

Harbor 2.0 separates instructions and configuration:
- `instruction.md`: task instructions (Markdown).
- `task.toml`: configuration and metadata (TOML).

Clear, unambiguous instructions are essential.

## instruction.md Structure
```markdown
# Fix Empty Input Bug

Your task is to fix the bug in /app/main.py that causes
the application to crash when processing empty input.

## Requirements

The fix should:
1. Handle empty string input gracefully
2. Return an empty list instead of crashing
3. Not modify any other behavior

## Files

- Input: `/app/main.py`
- Output: Modified `/app/main.py`
```

## task.toml Structure
```toml
version = "1.0"

[metadata]
author_name = "Your Name"
author_email = "your.email@example.com"
difficulty = "medium"
category = "debugging"
tags = ["python", "memory-leak", "debugging"]

[verifier]
timeout_sec = 120.0

[agent]
timeout_sec = 120.0

[environment]
build_timeout_sec = 600.0
docker_image = "some-org/some-name:some-tag"
cpus = 1
memory_mb = 2048
storage_mb = 10240
```

## Writing Good Instructions (instruction.md)

### Be explicit
State every requirement; avoid ambiguity.

```markdown
# Fix Server Error Handling

Fix the bug in /app/server.py that causes a 500 error
when the request body is empty.

## Requirements
1. Return HTTP 400 with message "Request body required"
2. Do not modify the response format for valid requests
3. Add a test case in /app/tests/test_server.py
```

Avoid vague instructions like “Fix the server bug.”

### Use absolute paths
Always use full paths starting with `/`.
- Good: `/app/config/settings.json`
- Bad: `config/settings.json` or `./settings.json`

### Specify output files
If tests check specific outputs, name them.

```markdown
# Process Data and Output Results

Write your solution to /output/result.json

## Output Format
```json
{
  "status": "success",
  "count": <number>,
  "items": [...]
}
```
```

### Define data formats precisely
```markdown
# Parse CSV to JSON

Parse the CSV at /data/input.csv and output to /data/output.json

## CSV Format
- First row is headers
- Columns: id, name, value
- Values may contain commas (enclosed in quotes)

## JSON Format
- Array of objects
- Each object has keys: id (int), name (string), value (float)
```

### List all constraints
```markdown
# Optimize Database Query

Optimize the query in /app/db/queries.py

## Constraints
- Must complete in under 100ms for 1M rows
- Do not change the function signature
- Do not use raw SQL (ORM only)
- Result must maintain same ordering
```

### Avoid tool requirements you cannot verify
- Bad: “Use vim to edit the file.”
- Good: “Edit /app/config.txt to change the port from 8080 to 3000.”

## task.toml Configuration Fields
- `metadata.difficulty` (required): `easy | medium | hard`
- `metadata.category` (required): task taxonomy value
- `metadata.tags` (required): 3–6 descriptive tags
- `metadata.author_name` / `metadata.author_email` (optional)
- `verifier.timeout_sec` (optional, default 120)
- `agent.timeout_sec` (optional, default 120)
- `environment.build_timeout_sec` (optional, default 600)
- `environment.docker_image` (optional)
- `environment.cpus`, `environment.memory_mb`, `environment.storage_mb`

## Validation
CI checks include:
- `validate_task_fields`: required fields in `task.toml`
- `check_task_absolute_path`: instructions use absolute paths
- `file_reference_mentioned`: output files mentioned in `instruction.md`
- `typos`: basic spelling checks

## Key Differences from Terminal-Bench
- Instructions are Markdown (`instruction.md`) for readability.
- Configuration is TOML (`task.toml`) for clean nesting.
- Clear separation: instructions vs. metadata.
- No multiline YAML strings—Markdown handles formatting.