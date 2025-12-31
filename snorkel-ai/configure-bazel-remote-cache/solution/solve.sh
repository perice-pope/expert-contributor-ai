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

# Extract cache statistics from build event JSON and build summary
python3 <<'PYTHON_SCRIPT'
import json
import sys
import re

def extract_from_summary(summary_file):
    """Extract cache stats from Bazel build summary output (primary method)."""
    total = 0
    cache_hits = 0
    executed = 0
    compile_executed = 0
    
    with open(summary_file, 'r') as f:
        content = f.read()
        
        # Look for build summary pattern: "X processes: Y remote cache hit, Z internal"
        # Example: "16 processes: 9 remote cache hit, 7 internal"
        # Or: "16 processes: 9 remote cache hit, 0 internal, 7 local"
        match = re.search(r'(\d+)\s+processes:.*?(\d+)\s+remote\s+cache\s+hit', content, re.IGNORECASE)
        if match:
            all_processes = int(match.group(1))
            cache_hits = int(match.group(2))
            
            # Extract internal count (non-cacheable actions)
            internal_match = re.search(r'(\d+)\s+internal', content, re.IGNORECASE)
            internal = int(internal_match.group(1)) if internal_match else 0
            
            # Total cacheable actions = all processes - internal
            total = all_processes - internal
            
            # Look for executed actions (actions that were actually run, not cached)
            # Format: "X processwrapper-sandbox" or "X worker" or "X linux-sandbox"
            executed_patterns = [
                r'(\d+)\s+processwrapper-sandbox',
                r'(\d+)\s+worker',
                r'(\d+)\s+linux-sandbox',
                r'(\d+)\s+local'
            ]
            for pattern in executed_patterns:
                exec_match = re.search(pattern, content, re.IGNORECASE)
                if exec_match:
                    executed = max(executed, int(exec_match.group(1)))
            
            # Try to identify compile actions from build output
            # Look for compile action patterns in the output
            compile_patterns = [
                r'Compiling\s+[^\n]+',
                r'javac\s+[^\n]+',
                r'g\+\+\s+[^\n]+',
                r'gcc\s+[^\n]+'
            ]
            compile_matches = sum(1 for pattern in compile_patterns if re.search(pattern, content, re.IGNORECASE))
            # If we see compile commands in output, some compiles were executed
            if compile_matches > 0 and executed > 0:
                compile_executed = min(executed, compile_matches)
    
    return total, cache_hits, executed, compile_executed

def extract_cache_stats_bep(bep_file):
    """Extract cache hit statistics from Bazel build event protocol JSON (fallback)."""
    total_actions = 0
    cache_hit_actions = 0
    compile_actions_executed = 0
    
    try:
        with open(bep_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    
                    # Bazel BEP format: { "id": { "actionCompleted": {...} }, "action": { "completed": {...} } }
                    # Check if this is an actionCompleted event
                    if 'id' in event and isinstance(event['id'], dict):
                        event_id = event['id']
                        if 'actionCompleted' in event_id:
                            # This is an actionCompleted event
                            if 'action' in event and isinstance(event['action'], dict):
                                action_completed = event['action'].get('completed')
                                if action_completed and isinstance(action_completed, dict):
                                    total_actions += 1
                                    
                                    # Check cache hit status
                                    cache_hit = action_completed.get('cacheHit', False)
                                    if cache_hit:
                                        cache_hit_actions += 1
                                    
                                    # Check if this is a compile action that was executed
                                    if not cache_hit:
                                        # Get action type and label
                                        action_type = action_completed.get('type', '')
                                        label = action_completed.get('label', '')
                                        
                                        # Identify compile actions
                                        action_type_str = str(action_type).lower()
                                        label_str = str(label).lower()
                                        
                                        if any(keyword in action_type_str for keyword in ['cppcompile', 'javac', 'compile']):
                                            compile_actions_executed += 1
                                        elif any(keyword in label_str for keyword in ['compile', 'cpp', 'java']):
                                            # Additional check: if it's not cached and has compile in label
                                            compile_actions_executed += 1
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return 0, 0, 0
    
    return total_actions, cache_hit_actions, compile_actions_executed

# Primary method: Extract from build summary output
total, cache_hits, executed, compile_executed = extract_from_summary('/tmp/second_build_output.txt')

# Fallback: Try BEP parsing if summary parsing didn't work well
if total == 0 or cache_hits == 0:
    print("Summary parsing found insufficient data, trying BEP parsing...", file=sys.stderr)
    bep_total, bep_cache_hits, bep_compile_executed = extract_cache_stats_bep('/tmp/second_build.json')
    
    if bep_total > 0:
        total = bep_total
        cache_hits = bep_cache_hits
        if compile_executed == 0:
            compile_executed = bep_compile_executed

# Final validation
if total == 0:
    print("ERROR: No actions found in build output or build event file", file=sys.stderr)
    print("Build output sample:", file=sys.stderr)
    try:
        with open('/tmp/second_build_output.txt', 'r') as f:
            lines = f.readlines()
            for line in lines[-20:]:  # Last 20 lines
                print(line.rstrip(), file=sys.stderr)
    except:
        pass
    sys.exit(1)

# Calculate cache hit percentage
cache_hit_percentage = (cache_hits / total) * 100 if total > 0 else 0

# Generate verification report
report = {
    "cache_hit_percentage": round(cache_hit_percentage, 2),
    "compile_actions_executed": compile_executed,
    "total_actions": total,
    "cache_hit_actions": cache_hits,
    "build_successful": True
}

with open('/app/cache_verification.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Cache hit percentage: {cache_hit_percentage:.2f}%")
print(f"Compile actions executed: {compile_executed}")
print(f"Total actions: {total}")
print(f"Cache hit actions: {cache_hits}")

# Verify requirements
if cache_hit_percentage < 95.0:
    print(f"ERROR: Cache hit percentage {cache_hit_percentage:.2f}% is below 95%", file=sys.stderr)
    sys.exit(1)

if compile_executed > 0:
    print(f"ERROR: {compile_executed} compile actions were executed (expected 0)", file=sys.stderr)
    sys.exit(1)

print("SUCCESS: All cache verification requirements met!")
PYTHON_SCRIPT

echo "Cache verification complete. Report written to /app/cache_verification.json"
