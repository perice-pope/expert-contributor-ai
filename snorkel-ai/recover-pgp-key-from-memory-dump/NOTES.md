# Maintainer Notes

## What this task is testing

Agents must perform a complete forensic key recovery workflow:
1. Extract OpenPGP private key material from a binary memory dump
2. Reconstruct the key into valid ASCII-armored format
3. Import the key into GPG
4. Use the imported key to decrypt a ciphertext

The task requires understanding of:
- Memory dump analysis techniques (strings, grep, binary extraction)
- OpenPGP key format (ASCII-armored structure with BEGIN/END markers)
- GPG keyring management (import, key ID extraction)
- GPG decryption workflow (batch mode, pinentry settings)

## Intended failure modes

### 1. Incomplete or noisy key extraction
- **Shallow fix**: Using `strings` and grabbing the first BEGIN/END block (decoy wins)
- **Pattern**: Capturing base64 plus injected noise lines (`NOISE_LINE_*`, `MID_NOISE_*`) without cleanup
- **Why it fails**: GPG import fails or imports wrong block; decryption fails

### 2. Fragmented/long block handling
- **Shallow fix**: Stopping at the first END marker; real block spans mid-stream noise
- **Pattern**: Not scanning full dump or not sorting/choosing the longest plausible block
- **Why it fails**: Misses the real key portion after injected mid-stream noise

### 3. Decoy key traps
- **Shallow fix**: Importing the first complete-looking block (invalid base64 decoy)
- **Pattern**: Not validating import success or decrypting with the imported key
- **Why it fails**: Decryption fails silently; reward file stays 0

### 4. Key reconstruction and cleanup
- **Shallow fix**: Keeping non-base64 noise lines inside the block
- **Pattern**: Failing to strip noise lines injected between base64 lines
- **Why it fails**: GPG rejects malformed blocks

### 5. Import/decrypt workflow
- **Shallow fix**: Importing without batch/loopback; decrypting without checking output
- **Pattern**: Not resetting keyring between bad attempts (decoy contaminates)
- **Why it fails**: Hangs or produces empty output

### 6. Path and file handling errors
- **Shallow fix**: Not creating `/output` before writing
- **Pattern**: Writing to wrong path
- **Why it fails**: File write operations fail or tests can't find output

## Determinism and reproducibility

### Fixed inputs
- Memory dump is pre-generated with embedded key (deterministic content)
- Ciphertext is pre-encrypted with known plaintext (deterministic encryption)
- Expected plaintext is fixed: `SECRET_MESSAGE_42: The quick brown fox jumps over the lazy dog. Recovery successful!`

### No external dependencies
- All operations work offline (no network calls)
- GPG key generation happens during Docker build (if needed) or is pre-generated
- No time-dependent behavior (no sleeps, no polling)

### Tool version pinning
- GPG version pinned: `gnupg2=2.2.40-1.1`
- Base image pinned: `debian:bookworm-slim`
- All tools have fixed versions in Dockerfile

### Idempotent operations
- Key import is idempotent (can be run multiple times)
- Decryption produces same output each time
- No random elements in the workflow

## Task difficulty knobs

### Easy mode (not used here)
- Key is clearly delimited in memory dump
- Simple `grep` extraction works
- Key is already in perfect format

### Medium mode (could be)
- Key has some noise around it
- Requires basic cleanup (sed/awk)
- Standard GPG import works

### Hard mode (current)
- Key embedded with heavy noise, mid-stream noise block, and a decoy key
- Requires extracting the longest/valid block, cleaning noise lines, and reassembling
- Must handle GPG 2.x batch mode and pinentry settings
- Complete workflow from extraction → import → decryption

### Harder variants (future)
- Key is fragmented across memory regions
- Key is in binary format (not ASCII-armored)
- Multiple keys in dump, must identify correct one
- Key requires passphrase (adds complexity)

## Expected agent behavior

**Good agents will:**
1. Use `strings` or `grep -a` to extract readable key material
2. Clean up extracted key (remove noise, ensure proper BEGIN/END markers)
3. Import with `gpg --batch --yes --import`
4. Decrypt with `gpg --batch --yes --pinentry-mode loopback --decrypt`
5. Verify output file exists and has content

**Weak agents will:**
1. Try to use `extract_key.sh` as-is (incomplete)
2. Extract key but forget to clean it
3. Import without batch flags (hangs)
4. Decrypt without pinentry mode (hangs)
5. Write to wrong path or forget to create directory

