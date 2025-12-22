# Use Rust base image with newer version
FROM rust:1.83-slim-bookworm

# Install build dependencies but do NOT install libssl-dev
# This will cause openssl-sys to fail during build (which is the bug to fix)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Intentionally do NOT install libssl-dev to create openssl-sys build failure
# The fix is to either:
# 1. Install libssl-dev (Option C)
# 2. Use rustls-tls feature for reqwest (Option A - preferred)
# 3. Enable vendored feature for openssl-sys (Option B)

WORKDIR /app

# Copy starter project files (DO NOT copy solution/ or tests/)
COPY app/ /app/
