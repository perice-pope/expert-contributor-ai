FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
