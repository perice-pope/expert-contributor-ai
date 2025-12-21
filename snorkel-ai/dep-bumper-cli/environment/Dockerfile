FROM python:3.11-slim-bookworm

# Install system dependencies
# Node.js 20.x for npm (pinned to specific version)
# build-essential for compiling native modules
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs=20.18.0-1nodesource1 \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
# pip-tools 7.4.1 for pip-compile command
RUN pip install --no-cache-dir \
    pip-tools==7.4.1

# Set working directory
WORKDIR /app

# Copy starter project files (DO NOT copy solution/ or tests/)
COPY app/ /app/
