# TLS Client

A Rust application that demonstrates a TLS dependency conflict.

## Problem

This project intentionally has a dependency conflict:
- `reqwest` with default features uses `native-tls` (which depends on `openssl-sys`)
- `tokio-rustls` uses `rustls`
- Both `native-tls` and `rustls` are explicitly included

The host system's OpenSSL version may be incompatible with the `openssl-sys` version required.

## Solution

Fix the dependency conflict by:
1. Using `rustls-tls` feature for `reqwest` instead of `native-tls`
2. Or enabling `vendored` feature for `openssl-sys`
3. Or installing the correct `libssl-dev` version

