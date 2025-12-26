#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Analyzing memory dump for fragmented key data..."

# The new dump has the key fragmented across multiple memory regions
# We need to: 
# 1. Find all regions containing key fragments
# 2. Extract and reassemble them
# 3. Clean noise/corruption
# 4. Reconstruct complete key

python3 - <<'PY' > /tmp/key_candidates.txt
from pathlib import Path
import re

dump_lines = Path("/app/memory.dump").read_text(errors="ignore").splitlines()

# Strategy: Look for memory regions containing "gpg keyring buffer"
# These regions contain the fragmented key spread across 3 parts
key_region_lines = []
in_key_region = False

for line in dump_lines:
    if "gpg keyring buffer" in line:
        in_key_region = True
        continue
    if in_key_region:
        # Stop at next region marker
        if line.startswith("[Region") and "gpg keyring buffer" not in line:
            in_key_region = False
            continue
        key_region_lines.append(line)

if not key_region_lines:
    raise SystemExit("no key buffer regions found")

print(f"Found {len(key_region_lines)} lines in key buffer regions", file=__import__("sys").stderr)

# Now find and reassemble the key from these fragmented lines
header = None
footer = None
key_data_lines = []

for line in key_region_lines:
    line = line.strip()
    if "-----BEGIN PGP PRIVATE KEY BLOCK-----" in line:
        header = line
        continue
    elif "-----END PGP PRIVATE KEY BLOCK-----" in line:
        footer = line
        continue
    
    # Between header and footer - collect valid base64 lines
    # Filter out noise lines - valid base64 only
    # Note: Don't filter by length - checksum line can be as short as 5 chars
    if re.fullmatch(r"[A-Za-z0-9+/=]+", line):
        # Skip obvious noise markers
        if not any(noise in line for noise in [
            "NOISE", "MARKER", "FRAGMENT", "END_", "buffer_", 
            "noise_", "GARBAGE", "corruption_", "metadata_", "_hdr_", "_end_"
        ]):
            key_data_lines.append(line)

if not header or not footer:
    raise SystemExit("key header/footer not found in fragments")

if len(key_data_lines) < 20:
    raise SystemExit(f"too few key data lines recovered: {len(key_data_lines)}")

# Reconstruct complete key
reconstructed = [header] + key_data_lines + [footer]
Path("/tmp/clean_key.asc").write_text("\n".join(reconstructed) + "\n", encoding="utf-8")
print(f"Reconstructed key with {len(key_data_lines)} data lines", file=__import__("sys").stderr)
print("/tmp/clean_key.asc")
PY

KEY_FILE=$(head -n 1 /tmp/key_candidates.txt || true)
if [ -z "$KEY_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "[oracle] Error: No candidate key blocks found" >&2
    exit 1
fi

echo "[oracle] Step 2: Importing best candidate key..."

# Reset GPG home for clean import
export GNUPGHOME=/root/.gnupg
rm -rf "$GNUPGHOME"
mkdir -p "$GNUPGHOME"
chmod 700 "$GNUPGHOME"

gpg --batch --yes --import "$KEY_FILE" >/tmp/gpg_import.log 2>&1 || true

# Verify import succeeded by checking for keys in keyring
if ! gpg --list-secret-keys --with-colons 2>/dev/null | grep -q "^fpr:"; then
    echo "[oracle] Error: Key import failed - no keys found in keyring" >&2
    cat /tmp/gpg_import.log >&2 || true
    exit 1
fi

echo "[oracle] Step 3: Using imported keyring from successful candidate..."

echo "[oracle] Step 4: Decrypting ciphertext with recovered key..."

# Decrypt the ciphertext
# Use --batch --yes to avoid prompts, and --pinentry-mode loopback for non-interactive
mkdir -p /output
gpg --batch --yes --pinentry-mode loopback --decrypt --output /output/decrypted.txt ciphertext.asc 2>&1 | grep -v "^gpg:" || true

# Verify decryption succeeded
if [ ! -f /output/decrypted.txt ] || [ ! -s /output/decrypted.txt ]; then
    echo "[oracle] Error: Decryption failed or produced empty output" >&2
    exit 1
fi

echo "[oracle] Step 5: Validation complete"
echo "[oracle] Decrypted message:"
cat /output/decrypted.txt
