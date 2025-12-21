#!/bin/bash
# CANARY_STRING_PLACEHOLDER

set -euo pipefail

cd /app

# Wait for bazel-remote to be ready (check if port is listening)
echo "Waiting for bazel-remote to be ready..."
for i in {1..30}; do
    if nc -z localhost 8080 2>/dev/null || curl -s -f http://localhost:8080 > /dev/null 2>&1; then
        echo "bazel-remote is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: bazel-remote did not become ready after 30 attempts" >&2
        echo "Checking bazel-remote log:" >&2
        cat /tmp/bazel-remote.log >&2 || true
        exit 1
    fi
    sleep 1
done

# Step 1: Configure Bazel remote cache
echo "Configuring Bazel remote cache..."
cat > .bazelrc <<'EOF'
build --remote_cache=http://localhost:8080
build --remote_accept_cached=true
build --remote_upload_local_results=true
EOF

# Step 2: Build project to prime the cache
echo "Building project to prime cache..."
bazel build //... --build_event_json_file=/tmp/first_build.json

# Step 3: Simulate fresh checkout (clean all local state)
echo "Simulating fresh checkout (cleaning local state)..."
bazel clean --expunge

# Step 4: Rebuild and capture build events
echo "Rebuilding with cache..."
bazel build //... --build_event_json_file=/tmp/second_build.json 2>&1 | tee /tmp/second_build_output.txt

# Step 5: Parse build event JSON to extract cache statistics
echo "Analyzing cache hit statistics..."

# Extract cache statistics from build event JSON
# The build event JSON contains action_completed events with cacheHit field
python3 <<'PYTHON_SCRIPT'
import json
import sys
import re

def extract_cache_stats(bep_file):
    """Extract cache hit statistics from Bazel build event protocol JSON."""
    total_actions = 0
    cache_hit_actions = 0
    compile_actions_executed = 0
    
    with open(bep_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                # Bazel BEP format: event.id.actionCompleted and event.action.completed
                action_data = None
                
                # Check for id.actionCompleted format
                if 'id' in event:
                    event_id = event['id']
                    if isinstance(event_id, dict) and 'actionCompleted' in event_id:
                        # This indicates an actionCompleted event, get the action data
                        if 'action' in event and 'completed' in event.get('action', {}):
                            action_data = event['action']['completed']
                # Check for direct action.completed format
                if not action_data and 'action' in event:
                    action_obj = event['action']
                    if isinstance(action_obj, dict) and 'completed' in action_obj:
                        action_data = action_obj['completed']
                
                if action_data:
                    total_actions += 1
                    
                    # Check if this is a cache hit
                    cache_hit = action_data.get('cacheHit', False)
                    if cache_hit:
                        cache_hit_actions += 1
                    
                    # Check if this is a compile action that was executed (not cached)
                    if not cache_hit:
                        # Check action type - could be in different fields
                        action_type = str(action_data.get('type', ''))
                        label = str(action_data.get('label', ''))
                        # Compile actions typically have 'compile' in the type or label
                        if 'CppCompile' in action_type or 'Javac' in action_type or \
                           'compile' in action_type.lower() or 'Compile' in label:
                            compile_actions_executed += 1
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue
    
    return total_actions, cache_hit_actions, compile_actions_executed

# Also try to extract from build summary if BEP parsing fails
def extract_from_summary(summary_file):
    """Extract cache stats from Bazel build summary output."""
    total = 0
    cache_hits = 0
    executed = 0
    with open(summary_file, 'r') as f:
        content = f.read()
        # Look for "X processes: Y remote cache hit, Z internal" pattern
        # Format: "16 processes: 9 remote cache hit, 7 internal"
        # We only count cacheable actions (exclude internal)
        match = re.search(r'(\d+)\s+processes:.*?(\d+)\s+remote\s+cache\s+hit', content)
        if match:
            all_processes = int(match.group(1))
            cache_hits = int(match.group(2))
            # Extract internal count if present
            internal_match = re.search(r'(\d+)\s+internal', content)
            internal = int(internal_match.group(1)) if internal_match else 0
            # Total cacheable = all - internal
            total = all_processes - internal
            # Check for executed actions (processwrapper-sandbox, worker, etc.)
            executed_match = re.search(r'(\d+)\s+(?:processwrapper-sandbox|worker|linux-sandbox)', content)
            if executed_match:
                executed = int(executed_match.group(1))
    return total, cache_hits, executed

# Analyze second build (the one that should hit cache)
total, cache_hits, compiles_executed = extract_cache_stats('/tmp/second_build.json')

# Fallback to summary parsing if BEP parsing found no actions
if total == 0:
    print("BEP parsing found no actions, trying summary output...", file=sys.stderr)
    total, cache_hits, summary_executed = extract_from_summary('/tmp/second_build_output.txt')
    if total == 0:
        print("ERROR: No actions found in build event file or summary", file=sys.stderr)
        sys.exit(1)
    # Use summary_executed for compile actions if BEP didn't provide it
    if compiles_executed == 0 and summary_executed > 0:
        compiles_executed = summary_executed

cache_hit_percentage = (cache_hits / total) * 100 if total > 0 else 0

# Generate verification report
report = {
    "cache_hit_percentage": round(cache_hit_percentage, 2),
    "compile_actions_executed": compiles_executed,
    "total_actions": total,
    "cache_hit_actions": cache_hits,
    "build_successful": True
}

with open('/app/cache_verification.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Cache hit percentage: {cache_hit_percentage:.2f}%")
print(f"Compile actions executed: {compiles_executed}")
print(f"Total actions: {total}")
print(f"Cache hit actions: {cache_hits}")

# Verify requirements
if cache_hit_percentage < 95.0:
    print(f"ERROR: Cache hit percentage {cache_hit_percentage:.2f}% is below 95%", file=sys.stderr)
    sys.exit(1)

if compiles_executed > 0:
    print(f"ERROR: {compiles_executed} compile actions were executed (expected 0)", file=sys.stderr)
    sys.exit(1)

print("SUCCESS: All cache verification requirements met!")
PYTHON_SCRIPT

echo "Cache verification complete. Report written to /app/cache_verification.json"
