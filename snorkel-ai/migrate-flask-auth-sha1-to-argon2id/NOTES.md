# Maintainer Notes

## What this task is testing

Agents must perform a complete security migration of a legacy authentication system:

1. **Understand password hashing security**: Recognize that unsalted SHA-1 is insecure and needs migration to modern algorithms (Argon2id)
2. **Implement Argon2id hashing**: Use proper password hashing with per-user salts and configurable parameters
3. **Maintain backward compatibility**: Support both SHA-1 (legacy) and Argon2id (new) during migration period
4. **Implement rehash-on-login**: Automatically upgrade password hashes when parameters change or during login
5. **Bulk migration workflow**: Create CLI tool to validate credentials and migrate users in bulk
6. **Error handling and auditing**: Track migration failures and generate audit reports

The task requires understanding of:
- Password hashing security (SHA-1 vs Argon2id)
- Argon2id hash format and parameter extraction
- Backward compatibility patterns in authentication systems
- CSV parsing and credential validation
- JSON file manipulation
- Flask web service architecture

## Intended failure modes

### 1. Not implementing Argon2id at all
- **Shallow fix**: Only fixing SHA-1 verification, not implementing Argon2id
- **Pattern**: Leaving TODO comments, not importing argon2 library
- **Why it fails**: Tests check for Argon2id hash format (`$argon2id$` prefix)
- **Test catches**: `test_users_migrated_to_argon2id` and `test_argon2id_hashes_valid` fail

### 2. Using shared salt instead of per-user salt
- **Shallow fix**: Using a global salt or no salt
- **Pattern**: `hash(password + global_salt)` instead of per-user random salt
- **Why it fails**: Argon2id automatically generates per-user salts, but agent might try to implement custom hashing
- **Test catches**: Hash format validation fails, or security issue (though tests may not catch this directly)

### 3. Not reading config parameters
- **Shallow fix**: Hardcoding Argon2id parameters instead of reading from config file
- **Pattern**: Using fixed `memory_cost=65536, time_cost=3` instead of reading `argon2_config.json`
- **Why it fails**: Tests verify parameters match config file
- **Test catches**: `test_argon2id_hashes_valid` fails parameter matching

### 4. Skipping backward compatibility
- **Shallow fix**: Only supporting Argon2id, removing SHA-1 verification
- **Pattern**: Not checking if hash is SHA-1 before trying Argon2id verification
- **Why it fails**: Users still have SHA-1 hashes before migration; login fails for unmigrated users
- **Test catches**: Service may work after migration, but breaks during migration period

### 5. Not implementing rehash-on-login
- **Shallow fix**: Only checking password, not checking if hash needs rehashing
- **Pattern**: Verifying password but not comparing hash parameters with current config
- **Why it fails**: When config parameters change, old hashes should be upgraded
- **Test catches**: Tests may not explicitly check this, but it's a requirement

### 6. Migration script doesn't validate credentials
- **Shallow fix**: Migrating all users without validating passwords from CSV
- **Pattern**: Updating all SHA-1 hashes to Argon2id without checking if password is correct
- **Why it fails**: Wrong passwords would create invalid hashes, breaking authentication
- **Test catches**: `test_failed_users_recorded` expects eve to be in failed_users (wrong password)

### 7. Not generating audit.json
- **Shallow fix**: Running migration but not creating audit file
- **Pattern**: Missing audit file creation code
- **Why it fails**: Tests require `/app/audit.json` with specific structure
- **Test catches**: `test_audit_json_created` and `test_audit_json_valid` fail

### 8. Incorrect audit structure
- **Shallow fix**: Creating audit file but with wrong field names or types
- **Pattern**: Using `migrated` instead of `migrated_count`, or strings instead of integers
- **Why it fails**: Tests check for exact field names and types
- **Test catches**: `test_audit_json_valid` fails type checking

### 9. Not handling CSV parsing correctly
- **Shallow fix**: Not reading CSV properly, missing username/password extraction
- **Pattern**: Hardcoding usernames or not parsing CSV rows
- **Why it fails**: Migration doesn't process all users from CSV
- **Test catches**: `test_some_users_migrated` fails if not enough users migrated

### 10. Hash format errors
- **Shallow fix**: Creating invalid Argon2id hash format
- **Pattern**: Custom hash format instead of standard `$argon2id$v=...$m=...,t=...,p=...$salt$hash`
- **Why it fails**: Argon2id library expects standard format; tests check format
- **Test catches**: `test_argon2id_hashes_valid` fails format parsing

### 11. Not updating users.json in-place
- **Shallow fix**: Creating new file or not saving changes
- **Pattern**: Reading users but not writing back updated hashes
- **Why it fails**: Changes are lost, users still have SHA-1 hashes
- **Test catches**: `test_users_migrated_to_argon2id` fails

### 12. Flask service not handling JSON properly
- **Shallow fix**: Not parsing request JSON or returning wrong format
- **Pattern**: Missing `request.get_json()` or wrong response format
- **Why it fails**: Service doesn't accept login requests properly
- **Test catches**: `test_auth_service_login_with_migrated_hash` fails

## Why tests are designed this way

### Behavioral validation over implementation checking
- Tests verify the **outputs** (`/app/users.json`, `/app/audit.json`) contain expected content
- Tests verify **service behavior** (login succeeds/fails) rather than checking specific code patterns
- Tests don't check if specific functions were used (allows multiple valid approaches)

### Comprehensive migration validation
- Tests verify migration actually happened (SHA-1 → Argon2id conversion)
- Tests verify correct number of users migrated (at least 4 out of 5)
- Tests verify failed users are tracked (eve with wrong password)
- Tests verify hash parameters match config file

### Service functionality validation
- Tests verify Flask service can start and respond
- Tests verify login works with migrated hashes
- Tests verify invalid passwords are rejected
- Tests don't require service to be running continuously (start/stop in tests)

### Edge case coverage
- Empty/missing file checks prevent false positives
- Hash format validation ensures proper Argon2id structure
- Parameter matching ensures config is actually used
- Idempotency check ensures migration can run multiple times

### Audit report validation
- Tests verify audit structure (required fields, correct types)
- Tests verify counts match actual results
- Tests verify failed users list is accurate

## Determinism and reproducibility

### Fixed inputs
- User database (`users.json`) has fixed SHA-1 hashes for known passwords
- Login attempts CSV has fixed username/password pairs
- Argon2 config has fixed parameters (memory_cost=65536, time_cost=3, parallelism=4)
- Passwords: alice=password123, bob=securepass456, charlie=mysecret789, diana=testpass321, eve=wrongpassword

### No external dependencies
- All operations work offline (no network calls)
- No time-dependent behavior (no sleeps, minimal polling)
- Flask service runs locally in tests

### Tool version pinning
- Python version pinned: `python:3.11-slim-bookworm`
- Flask version pinned: `Flask==3.0.0`
- argon2-cffi version pinned: `argon2-cffi==23.1.0`
- Base image pinned: `debian:bookworm-slim`

### Deterministic hashing
- Argon2id hashes are deterministic for same password and parameters
- However, salts are random, so exact hash values will differ between runs
- Tests check hash format and parameters, not exact hash values

### Idempotent operations
- Migration can run multiple times (skips already-migrated users)
- Service operations are stateless (except user file updates)

## Task difficulty knobs

### Easy mode (not used here)
- Single user to migrate
- No backward compatibility needed
- Simple hash replacement

### Medium mode (could be)
- Multiple users, straightforward migration
- Basic Argon2id implementation
- Simple audit report

### Hard mode (current)
- Multiple users with some failures (eve has wrong password)
- Backward compatibility required (SHA-1 + Argon2id)
- Rehash-on-login logic
- Configurable parameters from file
- Complete audit reporting
- Flask service integration

### Harder variants (future)
- Very large user databases (performance testing)
- Fragmented migration (some users migrated, some not)
- Parameter changes requiring rehash
- Multiple hash algorithm support (SHA-1, bcrypt, Argon2id)
- Database instead of JSON file
- Concurrent migration with locking

## Expected agent behavior

**Good agents will:**
1. Import argon2 library and use PasswordHasher
2. Read config from `argon2_config.json` and use those parameters
3. Check hash format (SHA-1 vs Argon2id) before verification
4. Implement rehash-on-login by comparing stored hash parameters with current config
5. Parse CSV correctly and validate each credential
6. Update users.json in-place after migration
7. Generate audit.json with correct structure (migrated_count, failed_count, failed_users)
8. Handle eve's wrong password gracefully (add to failed_users)
9. Make Flask service work with both hash types during migration

**Weak agents will:**
1. Not implement Argon2id at all (leave TODOs)
2. Hardcode parameters instead of reading config
3. Remove SHA-1 support (breaking backward compatibility)
4. Skip credential validation in migration (migrate everyone)
5. Not generate audit.json
6. Wrong audit structure (wrong field names/types)
7. Not update users.json (changes lost)
8. Flask service crashes or returns wrong format
9. Hash format errors (custom format instead of standard)
10. Not handle CSV parsing correctly

## Known issues and limitations

- User database is small (5 users) for realistic migration, but sufficient for testing
- JSON file storage is not production-ready (should use database), but appropriate for task
- No concurrent access handling (single-threaded migration)
- Rehash-on-login is tested implicitly but not explicitly (could add dedicated test)
- Argon2id hash values are non-deterministic due to random salts (tests check format, not exact values)
- Flask service runs in tests but may have port conflicts in some environments

## Harbor Infrastructure Troubleshooting

### Issue: RewardFileNotFoundError - Files not syncing from container to host

**Symptoms:**
- All tests pass (14/14) but Harbor reports `RewardFileNotFoundError`
- `test-stdout.txt` appears in verifier directory but `reward.txt` and `ctrf.json` do not
- Files exist inside container (`/logs/verifier/reward.txt`) but not on host filesystem

**Root Cause:**
The Harbor CLI runs inside a Docker container (via shim at `/home/perice09/.local/bin/harbor`) and mounts `${PWD}:/workspace`. When Harbor tells task containers to mount volumes at `/workspace/jobs/.../verifier`, Docker looks for `/workspace` on the **actual host filesystem**. If `/workspace` is a separate directory (not symlinked to the Harbor workspace), volume mounts fail silently.

**Fix:**
```bash
# Create symlink so /workspace points to the Harbor workspace
sudo rm -rf /workspace
sudo ln -s /home/perice09/workspace/snorkel-ai /workspace
```

**Verification:**
```bash
# Check symlink exists
ls -la /workspace

# Run oracle agent - should now create reward.txt
cd /home/perice09/workspace/snorkel-ai
harbor run --agent oracle --path migrate-flask-auth-sha1-to-argon2id

# Verify reward.txt exists
ls -la /workspace/jobs/*/migrate-flask-auth-sha1-to-argon2id__*/verifier/reward.txt
```

**Additional Fix for CI Checks:**
The Harbor shim needs to pass through API key environment variables for `harbor tasks check`:

```bash
# Edit /home/perice09/.local/bin/harbor
# Add these lines before "${HARBOR_IMAGE}" "$@":
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
  -e OPENAI_BASE_URL="${OPENAI_BASE_URL:-}" \
```

**When to Check:**
- If you see `RewardFileNotFoundError` despite tests passing
- If `test-stdout.txt` exists but `reward.txt` doesn't
- If Harbor was recently rebuilt or Docker environment changed
- If working on a new machine or after system updates

**Prevention:**
- Ensure `/workspace` symlink exists before running Harbor tasks
- Check symlink after Harbor Docker image rebuilds
- Document this requirement in setup scripts




