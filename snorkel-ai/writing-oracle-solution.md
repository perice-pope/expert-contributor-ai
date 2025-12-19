# Writing Oracle Solution

The oracle solution (`solution/solve.sh`) is an expert-authored, deterministic script that proves the task is solvable.

## Basic Structure

```bash
#!/bin/bash
set -e

# Step 1: Navigate to working directory
cd /app

# Step 2: Perform the task
sed -i 's/bug/fix/' main.py

# Step 3: Verify the fix
python -c "from main import process; assert process('test') == expected"

# Step 4: Cleanup or final steps
echo "Task completed successfully"
```

## Key Principles

### 1) Demonstrate the command sequence
Show the steps you took, not just the final answer.

```bash
#!/bin/bash
# Find and fix the bug
grep -r "TypeError" /app/logs/ | head -1

# Fix the bug
sed -i '42s/data.process()/data.process() if data else None/' /app/main.py

# Verify
python -m pytest /app/tests/ -v
```

Avoid scripts that only output the answer:

```bash
#!/bin/bash
echo "42" > /output/answer.txt  # Not acceptable
```

### 2) Be deterministic
- Seed randomness.
- Avoid time-dependent behavior.
- Avoid network calls to external services.

### 3) Written by a human
Use LLM help sparingly for syntax, not for full solutions.

## Advanced Patterns

### Multi-step solutions
```bash
#!/bin/bash
set -e

# Set up environment
cd /app
source venv/bin/activate

# Fix config
python -c "
import json
config = json.load(open('config.json'))
config['debug'] = False
json.dump(config, open('config.json', 'w'))
"

# Fix server binding
sed -i 's/localhost/0.0.0.0/' server.py

# Restart service
pkill -f server.py || true
python server.py &
sleep 2

# Verify
curl -s http://localhost:8080/health | grep -q "ok"
```

### Using Python inside the solution
```bash
#!/bin/bash
cd /app

python << 'EOF'
import pandas as pd

df = pd.read_csv('/data/input.csv')
df['total'] = df['price'] * df['quantity']
df.to_csv('/data/output.csv', index=False)
EOF
```

### Interactive commands (solution.yaml)
Use for tasks that require interactive tools (e.g., vim).

```yaml
# solution/solution.yaml
commands:
  - type: interactive
    command: vim /app/file.txt
    inputs:
      - "dd"
      - "i"
      - "hello"
      - "<Esc>"
      - ":wq"
```

## Common Mistakes

### Hardcoding answers
```bash
# WRONG
echo "The answer is 42" > /output/result.txt

# RIGHT
cd /app
python calculate.py > /output/result.txt
```

### Non-deterministic behavior
```bash
# WRONG
python -c "import random; print(random.choice([1,2,3]))"

# RIGHT
python -c "import random; random.seed(42); print(random.choice([1,2,3]))"
```

### Missing error handling
```bash
# WRONG
cd /nonexistent || true
do_something

# RIGHT
set -e
cd /app
do_something
```

## Testing Your Solution

### Run locally
```bash
# Enter the container
uv run harbor tasks start-env --path harbor_tasks/<task-name> --interactive

# Inside the container, run your solution steps manually
```

### Run the oracle agent
```bash
uv run harbor run --agent oracle --path harbor_tasks/<task-name>
```

If it fails, either the solution is buggy, the tests are too strict, or the task itself has issues.

## Canary String
Every solution must start with the canary string:

```bash
#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -e
# ... rest of solution
```