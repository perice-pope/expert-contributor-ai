FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    BAZEL_VERSION=7.1.1 \
    BAZEL_REMOTE_VERSION=2.6.1 \
    GO_VERSION=1.21.5

# Install system dependencies: C++ toolchain, Java, curl, unzip, netcat, git, go
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    openjdk-17-jdk \
    curl \
    ca-certificates \
    unzip \
    netcat-openbsd \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Go (pinned version 1.21.5) for building bazel-remote
RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz \
    && ln -s /usr/local/go/bin/go /usr/local/bin/go

# Install Bazel (pinned version 7.1.1)
RUN curl -fsSL https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/bazel-${BAZEL_VERSION}-linux-x86_64 -o /usr/local/bin/bazel \
    && chmod +x /usr/local/bin/bazel

# Build bazel-remote from source (pinned version 2.6.1)
RUN git clone --depth 1 --branch v${BAZEL_REMOTE_VERSION} https://github.com/buchgr/bazel-remote.git /tmp/bazel-remote \
    && cd /tmp/bazel-remote \
    && go build -o /usr/local/bin/bazel-remote \
    && chmod +x /usr/local/bin/bazel-remote \
    && rm -rf /tmp/bazel-remote

# Create cache directory
RUN mkdir -p /cache && chmod 777 /cache

# Set working directory
WORKDIR /app

# Copy starter project files (DO NOT copy solution/ or tests/)
COPY app/ /app/

# Create entrypoint script to start bazel-remote in background
RUN cat > /entrypoint.sh <<'ENTRYPOINT_EOF' && chmod +x /entrypoint.sh
#!/bin/bash
set -e
# Start bazel-remote in background (max_size required, set to 10GB)
bazel-remote --dir=/cache --port=8080 --host=0.0.0.0 --max_size=10 > /tmp/bazel-remote.log 2>&1 &
BAZEL_REMOTE_PID=$!
echo "Started bazel-remote (PID: $BAZEL_REMOTE_PID)"
# Wait a moment for bazel-remote to start
sleep 2
# Keep container alive
exec "$@"
ENTRYPOINT_EOF

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
