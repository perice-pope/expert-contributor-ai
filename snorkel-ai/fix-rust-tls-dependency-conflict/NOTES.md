# Maintainer Notes — fix-rust-tls-dependency-conflict

## Task Overview

This task requires agents to diagnose and fix a Rust build failure caused by a TLS dependency conflict. The project uses `reqwest` with default features (which uses `native-tls`/`openssl-sys`), but the system OpenSSL libraries are missing, causing `openssl-sys` to fail during compilation. The fix is to configure `reqwest` to use `rustls-tls` instead of `native-tls`.

## Intended Agent Failure Modes

1. **Installing libssl-dev only**: Agents may try to install `libssl-dev` (Option C) without realizing that using `rustls-tls` (Option A) is the preferred solution that avoids system dependencies entirely.

2. **Incomplete Cargo.toml modification**: Agents may modify `Cargo.toml` incorrectly, leaving `default-features = true` which still pulls in `native-tls`, or may not add the `rustls-tls` feature.

3. **Wrong feature syntax**: Agents may use incorrect TOML syntax when modifying features, causing parse errors.

4. **Not testing the fix**: Agents may modify `Cargo.toml` but not verify that `cargo build` and `cargo test` actually succeed.

5. **Modifying application code**: Agents may try to modify `src/main.rs` or `src/lib.rs` instead of fixing the dependency configuration.

6. **Using vendored OpenSSL**: Agents may enable `vendored` feature for `openssl-sys` (Option B) which works but is less ideal than using pure Rust `rustls-tls`.

7. **Partial fixes**: Agents may only fix the build but not ensure tests pass, or vice versa.

## Test Design Rationale

Tests validate:
- **Build success**: `cargo build` must complete successfully (validates the dependency conflict is resolved)
- **Test success**: `cargo test` must pass all tests (validates the application works correctly)
- **Cargo.toml modification**: Verifies that the fix uses `rustls-tls` and disables `default-features` (validates the correct approach was taken)
- **Binary existence**: Confirms that a binary was actually built (validates build completion)

Tests use behavioral validation (running actual commands) rather than source grepping, making them robust against formatting variations.

## Determinism and Reproducibility

- **No network calls in tests**: Tests run `cargo build` and `cargo test` which may download dependencies, but this is deterministic based on `Cargo.lock`
- **Pinned Rust version**: Dockerfile uses `rust:1.83-slim-bookworm` for consistency
- **No randomness**: All test checks are deterministic
- **Offline-capable**: Once dependencies are cached, the build can run offline

## Difficulty Knobs

- **Easy**: Simple dependency conflict with clear error message pointing to missing OpenSSL
- **Medium (current)**: Requires understanding of Rust feature flags and TLS backends, multiple valid solutions
- **Hard**: Add complexity like multiple conflicting dependencies, version constraints, or platform-specific issues

## Edge Cases Covered

- Verifying that both build and tests succeed (not just one)
- Checking that the correct fix approach was used (rustls-tls, not just installing libssl-dev)
- Ensuring the binary was actually produced (not just compilation succeeded)

## Why Tests Are Structured This Way

1. **Behavioral validation**: Tests check what the application does (builds, tests pass), not how it's formatted
2. **Command execution**: Uses subprocess to run actual `cargo` commands, catching real build failures
3. **Comprehensive checks**: Each requirement maps to a specific test
4. **No source grepping**: Tests verify behavior through execution rather than parsing source files (except for Cargo.toml which is the artifact being modified)
5. **Clear failure messages**: Each test has descriptive assertion messages

