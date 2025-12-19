# Agent Task Control

Use this checklist to build and validate a task.

## Step 1: Extract and Rename
- Copy "template-task" folder and Rename to your task name (kebab-case), e.g., `fix-memory-leak-python`.

## Step 2: Write Task Instructions and Configuration
- Edit `instruction.md` with clear, explicit requirements.

```markdown
# Your Task Title

Your task description here. Be explicit about all requirements.

## Requirements

1. Requirement one
2. Requirement two
3. Requirement three
```

- Configure `task.toml`.

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
cpus = 1
memory_mb = 2048
storage_mb = 10240
```

## Step 3: Configure Docker Environment
- Edit `environment/Dockerfile` to add dependencies and pin versions.
- Never copy `solution/` or `tests/` into the image.
- For multi-container setups, see the Docker environment documentation.

**Troubleshooting (macOS):**

```bash
sudo dscl . create /Groups/docker
sudo dseditgroup -o edit -a "$USER" -t user docker
```

## Step 4: Test Your Solution Locally
Enter the container and iterate:

```bash
harbor run --agent oracle --path harbor_tasks/<task-name> --interactive
```

## Step 5: Create Solution File
- Add `solution/solve.sh` with the verified command sequence.
- Must be deterministic and human-authored.
- See `writing-oracle-solution.md` for guidance.

## Step 6: Write Tests
- Add `tests/test.sh` and pytest tests (e.g., `tests/test_outputs.py`).
- Script must produce `/logs/verifier/reward.txt`.

```bash
#!/bin/bash
cd /tests
uv venv
source .venv/bin/activate
uv pip install pytest

pytest test_outputs.py -v

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

See `writing-tests.md` for details.

## Step 7: Run Oracle Agent

```bash
harbor run --agent oracle --path harbor_tasks/<task-name>
```

Fix issues until this passes.

## Step 8: Test with Real Agents

```bash (check .env)
export OPENAI_API_KEY=<your-portkey-api-key>
export OPENAI_BASE_URL=https://api.portkey.ai/v1

# GPT-5
harbor run -a terminus-2 -m openai/@openai-tbench/gpt-5 -p harbor_tasks/<task-name>

# Claude Sonnet 4.5
harbor run -a terminus-2 -m openai/@anthropic-tbench/claude-sonnet-4-5-20250929 -p harbor_tasks/<task-name>
```

Run each 2–3 times; target pass rate < 80%.

## Step 9: Run CI/LLMaJ Checks Locally

```bash
# GPT-5
harbor run -a terminus-2 -m openai/@openai-tbench/gpt-5 -p harbor_tasks/<task-name>

# Claude Sonnet 4.5
harbor run -a terminus-2 -m openai/@anthropic-tbench/claude-sonnet-4-5-20250929 -p harbor_tasks/<task-name>
```

All checks should pass before submission.

## Step 10: Final Verification
- Oracle agent passes.
- CI/LLMaJ checks pass.
- Tested against real agents (pass rate < 80%).
- All required files are present.

```bash
# Oracle agent
harbor run --agent oracle --path harbor_tasks/<task-name>

# CI/LLMaJ checks
harbor run -a terminus-2 -m openai/@openai-tbench/gpt-5 -p harbor_tasks/<task-name>
```

## Step 11: Pre-Submission Checklist

**⚠️ CRITICAL: Verify these before creating your ZIP file to avoid CI build failures:**

### 1. Validate `task.toml` Configuration
- ✅ **Category must be valid**: Check that `category` in `task.toml` is one of:
  - `build-and-dependency-management`
  - `data-processing`
  - `debugging`
  - `games`
  - `machine-learning`
  - `scientific-computing`
  - `security`
  - `software-engineering`
  - `system-administration`
  
  ❌ **Invalid examples**: `devops`, `cloud`, `infrastructure`, etc.

- ✅ **Difficulty must be valid**: `easy`, `medium`, or `hard`

### 2. Validate `tests/test.sh`
- ✅ **pytest must include `-rA` flag**: The test script must use `pytest -rA` (not just `pytest` or `pytest -q`)
  
  ✅ **Correct format:**
  ```bash
  python3 -m pytest -q -rA /tests/test_outputs.py
  ```
  
  ❌ **Will fail:**
  ```bash
  python3 -m pytest -q /tests/test_outputs.py  # Missing -rA
  ```

### 3. Clean Up Before Zipping
- ✅ **Exclude `__MACOSX/` folder**: macOS creates this metadata folder when zipping. It causes UTF-8 encoding errors in CI.
- ✅ **Exclude `jobs/` folder**: This contains runtime artifacts and should not be submitted.
- ✅ **Exclude hidden files**: `.DS_Store`, `.git/`, etc.

### 4. Verify File Structure
- ✅ **`task.toml` must be at root** of the zip (not nested in a subfolder)
- ✅ **`tests/test.sh` must exist** at `tests/test.sh` relative to root
- ✅ **All required files present**: `instruction.md`, `task.toml`, `solution/solve.sh`, `tests/test.sh`, `environment/Dockerfile`

### 5. Create ZIP from Task Directory
**Important**: Zip the contents of your task folder, NOT the folder itself.

**✅ Correct approach (Linux):**
```bash
cd snorkel-ai/your-task-name
zip -r submission.zip . -x "jobs/*" -x "__MACOSX/*" -x ".*" -x "NOTES.md"
```

**✅ Correct approach (macOS - manual):**
1. Open your task folder in Finder
2. Select all files (Cmd+A)
3. Right-click → Compress Items
4. **Verify** the zip contains files at root level (not nested in a folder)

**❌ Incorrect**: Zipping the parent folder or including nested task folder structure

### 6. Verify ZIP Contents
Before submitting, verify your zip structure:
```bash
unzip -l submission.zip | head -20
```

Should show:
```
task.toml          # at root ✓
instruction.md     # at root ✓
tests/test.sh      # correct path ✓
solution/solve.sh  # correct path ✓
```

Should NOT show:
```
your-task-name/task.toml  # nested - WRONG ❌
__MACOSX/...              # metadata - WRONG ❌
```

## Step 12: Create ZIP File
- Select individual files inside your task folder (not the folder itself).

```
my-task/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   └── [build files]
├── solution/
│   └── solve.sh
└── tests/
    ├── test.sh
    └── [test files]
```

On macOS: open the task folder, select all files (Cmd+A), right-click → Compress. **Then verify the zip contents before submitting.**