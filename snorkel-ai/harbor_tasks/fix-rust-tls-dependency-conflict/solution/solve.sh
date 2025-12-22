#!/bin/bash
# CANARY_STRING_PLACEHOLDER

set -euo pipefail

# Fix Rust TLS dependency conflict
# The issue: reqwest with default features uses native-tls (openssl-sys),
# which requires system OpenSSL libraries that are missing.
# Solution: Use rustls-tls feature for reqwest instead of native-tls.

cd /app

# Modify Cargo.toml to use rustls-tls instead of native-tls
# This avoids the need for system OpenSSL libraries
sed -i 's/reqwest = { version = "0.11", default-features = true, features = \["json"\] }/reqwest = { version = "0.11", default-features = false, features = ["json", "rustls-tls"] }/' Cargo.toml

# Verify the build works
echo "Building project..."
cargo build

# Verify tests pass
echo "Running tests..."
cargo test

echo "Fix complete: Project builds and tests pass using rustls-tls instead of native-tls."
