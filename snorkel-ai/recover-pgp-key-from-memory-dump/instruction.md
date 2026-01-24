# Recover OpenPGP Private Key from Process Memory Dump

A security incident response team has captured a memory dump from a compromised Linux process that was running a GPG agent. The process memory contains fragments of an OpenPGP private key that was loaded into memory. Your task is to extract the key material from the dump, reconstruct the complete key, import it into GPG, and decrypt a provided ciphertext to validate the recovery.

## Requirements

1. **Extract key material**: Analyze the memory dump file (`/app/memory.dump`) to locate and extract the OpenPGP private key data (may be ASCII-armored or binary format).
2. **Reconstruct the key**: Assemble the extracted fragments into a complete, valid OpenPGP private key file.
   - Write the reconstructed key to `/output/recovered_key.asc`
   - The reconstructed key must contain a single `BEGIN PGP PRIVATE KEY BLOCK` / `END PGP PRIVATE KEY BLOCK` pair with all noise lines removed (e.g., lines containing `NOISE_` or `GARBAGE_`)
3. **Import the key**: Import the reconstructed private key into the default GPG keyring using `gpg --import` and verify it is listed by `gpg --list-secret-keys`. Use the default GPG home (`/root/.gnupg`) so the keyring files are created there.
4. **Decrypt ciphertext**: Use the imported key to decrypt the provided ciphertext file (`/app/ciphertext.asc`) and write the plaintext to `/output/decrypted.txt`.
5. **Validate recovery**: The decrypted plaintext must match the expected secret message (tests will verify this).

## Constraints

- **No external network calls**. All operations must work offline.
- **Do not modify the memory dump file**. Extract data from it, but leave the original file unchanged.
- **Use standard tools only**: `gpg`, `strings`, `hexdump`, `grep`, `sed`, `awk`, and standard shell utilities.
- **Key format**: The extracted key may be ASCII-armored (starts with `-----BEGIN PGP PRIVATE KEY BLOCK-----`) or binary format. Handle both cases.
- **GPG keyring**: Import the key into the default GPG keyring location (`~/.gnupg/`).

## Files

- Memory dump: `/app/memory.dump` (binary file containing process memory)
- Ciphertext: `/app/ciphertext.asc` (ASCII-armored encrypted message)
- Extraction script (starter): `/app/extract_key.sh` (incomplete helper script)
- Output directory: `/output/` (write decrypted plaintext here)
- GPG home: `~/.gnupg/` (default GPG keyring location)

## Outputs

- `/output/decrypted.txt` (text file; the decrypted plaintext message)
