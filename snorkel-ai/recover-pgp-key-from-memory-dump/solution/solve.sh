#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "[oracle] Step 1: Extracting OpenPGP private key from memory dump..."

echo "[oracle] Parsing dump for candidate key blocks (with noise cleanup)..."

# Extract all key-like blocks, clean noise lines, choose the longest cleaned block.
python3 - <<'PY' > /tmp/key_candidates.txt
from pathlib import Path
import re

dump = Path("memory.dump").read_text(errors="ignore").splitlines()
blocks = []
current = []
inside = False
for line in dump:
    if "-----BEGIN PGP PRIVATE KEY BLOCK-----" in line:
        inside = True
        current = [line.strip()]
        continue
    if inside:
        current.append(line.strip())
        if "-----END PGP PRIVATE KEY BLOCK-----" in line:
            blocks.append(current)
            inside = False
            current = []

cleaned_blocks = []
for block in blocks:
    cleaned = []
    for ln in block:
        if "BEGIN PGP PRIVATE KEY BLOCK" in ln or "END PGP PRIVATE KEY BLOCK" in ln:
            cleaned.append(ln)
        elif re.fullmatch(r"[A-Za-z0-9+/=]+", ln):
            cleaned.append(ln)
    if len(cleaned) >= 8:
        cleaned_blocks.append(cleaned)

if not cleaned_blocks:
    raise SystemExit("no cleaned key blocks found")

# Choose the longest cleaned block (prefer real key over decoys)
cleaned_blocks.sort(key=len, reverse=True)
best = cleaned_blocks[0]
Path("/tmp/clean_key.asc").write_text("\n".join(best) + "\n", encoding="utf-8")
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
