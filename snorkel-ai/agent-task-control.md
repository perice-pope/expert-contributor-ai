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

## Step 11: Create ZIP File
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

On macOS: open the task folder, select all files (Cmd+A), right-click → Compress.