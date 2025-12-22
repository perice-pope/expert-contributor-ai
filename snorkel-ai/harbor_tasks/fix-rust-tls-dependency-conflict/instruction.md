# Fix Rust TLS Dependency Conflict

A Rust project fails to build due to a dependency conflict between `native-tls` (which uses `openssl-sys`) and `rustls`. The host system's OpenSSL version is incompatible with the `openssl-sys` version required by the dependency tree. You must diagnose the issue and fix it so that `cargo build` and `cargo test` complete successfully.

## Requirements

1. **Diagnose the build failure**: Identify that the conflict is between `native-tls`/`openssl-sys` and `rustls`, and that the OpenSSL version is incompatible.

2. **Fix the dependency conflict**: Choose one of the following approaches:
   - Option A: Configure dependencies to use `rustls-tls` feature instead of `native-tls` (preferred if possible)
   - Option B: Enable `vendored` feature for `openssl-sys` to use a bundled OpenSSL
   - Option C: Install the correct `libssl-dev` version that matches `openssl-sys` requirements

3. **Ensure successful build**: After applying the fix, `cargo build` must complete without errors.

4. **Ensure successful tests**: After applying the fix, `cargo test` must complete successfully with all tests passing.

## Constraints

- Do NOT modify the core application logic in `/app/src/main.rs` or `/app/src/lib.rs` (if present)
- Do NOT change the functionality of the application
- You MAY modify `/app/Cargo.toml` to adjust features and dependencies
- You MAY modify `/app/Cargo.lock` if necessary (though it may be regenerated)
- You MAY install system packages via `apt-get` if needed

## Files

- Input: `/app/Cargo.toml` (dependency configuration)
- Input: `/app/src/main.rs` (application code - read-only for logic changes)
- Output: Modified `/app/Cargo.toml` with resolved dependency conflict
- Output: Successful `cargo build` output
- Output: Successful `cargo test` output

## Outputs

The task is considered complete when:

1. `/app/Cargo.toml` has been modified to resolve the TLS dependency conflict
2. Running `cargo build` in `/app` completes successfully (exit code 0)
3. Running `cargo test` in `/app` completes successfully with all tests passing (exit code 0)

The fix should be deterministic and reproducible - the same changes should work consistently.
