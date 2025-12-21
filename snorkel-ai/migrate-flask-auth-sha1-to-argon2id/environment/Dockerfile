FROM python:3.11-slim-bookworm

# Install system dependencies (including curl for uv installation in test.sh)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for test dependencies (pinned version)
RUN curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install pinned Python dependencies
# Flask 3.0.0 for web framework
# argon2-cffi 23.1.0 for Argon2id password hashing
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    argon2-cffi==23.1.0

# Set working directory
WORKDIR /app

# Copy starter project files (DO NOT copy solution/ or tests/)
COPY app/ /app/
