FROM debian:bookworm-slim

# Install required tools for memory analysis and GPG
# System packages don't require version pinning per Harbor guidelines
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg \
    binutils \
    grep \
    sed \
    gawk \
    coreutils \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create output directory
RUN mkdir -p /output

# Set up GPG directory
RUN mkdir -p /root/.gnupg && \
    chmod 700 /root/.gnupg

# Copy starter project files
COPY app/ /app/
