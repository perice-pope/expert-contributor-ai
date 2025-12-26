# Recover OpenPGP Private Key from Process Memory Dump

A security incident response team has captured a memory dump from a compromised Linux process that was running a GPG agent. The process memory may contain fragments of cryptographic material. Your task is to perform forensic analysis to recover usable key material and decrypt the provided ciphertext.

## Requirements

1. **Analyze memory dump**: The file `/app/memory.dump` contains a forensic capture of process memory that may include cryptographic artifacts.
2. **Recover key material**: Locate and extract any cryptographic key data from the memory regions. The dump may contain fragmented, corrupted, or obfuscated data that requires careful reconstruction.
3. **Decrypt ciphertext**: Successfully decrypt `/app/ciphertext.asc` and write the plaintext to `/output/decrypted.txt`.

## Constraints

- **No external network calls**. All operations must work offline.
- **Do not modify the original dump file**.
- **Use standard forensic tools**: `gpg`, `strings`, `hexdump`, `grep`, `sed`, `awk`, and standard shell utilities.
- **Memory format**: The dump contains multiple memory regions with various data types. Not all regions contain useful information.

## Files

- Memory dump: `/app/memory.dump` (process memory capture)
- Ciphertext: `/app/ciphertext.asc` (encrypted message)
- Output directory: `/output/` (write decrypted plaintext here)

## Outputs

- `/output/decrypted.txt` (the decrypted plaintext message)

## Notes

- Memory dumps from live processes may contain fragmented or corrupted data
- Multiple key-like structures may be present; not all are valid
- Successful recovery requires understanding of OpenPGP key structure and memory forensics
