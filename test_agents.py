#!/usr/bin/env python3
"""Rezip task and test with agents"""
import os
import zipfile
import tempfile
import shutil
import subprocess
import sys

# Step 1: Rezip with updated instructions
print("=" * 60)
print("STEP 1: Rezipping with updated instructions...")
print("=" * 60)

zip_path = "/home/perice09/workspace/revisions/configure-cli-emulators-profiles-submission-revised.zip"
instruction_src = "/home/perice09/workspace/snorkel-ai/configure-cli-emulators-profiles/instruction.md"
output_zip = "/home/perice09/workspace/revisions/configure-cli-emulators-profiles-submission-revised.zip"

if not os.path.exists(zip_path):
    print(f"ERROR: Zip file not found: {zip_path}")
    sys.exit(1)

if not os.path.exists(instruction_src):
    print(f"ERROR: Instruction file not found: {instruction_src}")
    sys.exit(1)

print(f"Extracting {zip_path}...")
with tempfile.TemporaryDirectory() as tmpdir:
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(tmpdir)
    
    print(f"Copying updated instruction.md from {instruction_src}...")
    shutil.copy(instruction_src, os.path.join(tmpdir, "instruction.md"))
    
    print(f"Creating new zip at {output_zip}...")
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, tmpdir)
                z.write(file_path, arcname)
    
    print(f"✓ Rezip complete: {output_zip}")

# Step 2: Test with oracle
print("\n" + "=" * 60)
print("STEP 2: Testing with oracle agent...")
print("=" * 60)

try:
    result = subprocess.run(
        ["harbor", "run", "-a", "oracle", "-p", "harbor_tasks/configure-cli-emulators-profiles"],
        cwd="/home/perice09/workspace",
        capture_output=True,
        text=True,
        timeout=300
    )
    print("STDOUT:")
    print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    print(f"\nExit code: {result.returncode}")
except subprocess.TimeoutExpired:
    print("TIMEOUT after 5 minutes")
except Exception as e:
    print(f"ERROR: {e}")

# Step 3: Test with claude-code
print("\n" + "=" * 60)
print("STEP 3: Testing with claude-code (Sonnet 4.5)...")
print("=" * 60)
print("(This may take several minutes...)")

try:
    result = subprocess.run(
        ["harbor", "run", "-a", "claude-code", "-m", "anthropic/claude-sonnet-4-5-20250929", 
         "-p", "harbor_tasks/configure-cli-emulators-profiles", "-k", "3", "-n", "1"],
        cwd="/home/perice09/workspace",
        capture_output=True,
        text=True,
        timeout=600
    )
    print("STDOUT:")
    print(result.stdout[-1500:] if len(result.stdout) > 1500 else result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    print(f"\nExit code: {result.returncode}")
except subprocess.TimeoutExpired:
    print("TIMEOUT after 10 minutes")
except Exception as e:
    print(f"ERROR: {e}")

# Step 4: Test with codex-gpt5
print("\n" + "=" * 60)
print("STEP 4: Testing with codex-gpt5...")
print("=" * 60)
print("(This may take several minutes...)")

try:
    result = subprocess.run(
        ["harbor", "run", "-a", "codex-gpt5", "-p", "harbor_tasks/configure-cli-emulators-profiles", 
         "-k", "3", "-n", "1"],
        cwd="/home/perice09/workspace",
        capture_output=True,
        text=True,
        timeout=600
    )
    print("STDOUT:")
    print(result.stdout[-1500:] if len(result.stdout) > 1500 else result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    print(f"\nExit code: {result.returncode}")
except subprocess.TimeoutExpired:
    print("TIMEOUT after 10 minutes")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)

