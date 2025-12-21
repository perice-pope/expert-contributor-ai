FROM python:3.11-slim-bookworm

# Install system dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
# Pylint 3.0.3 for plugin development
# pytest 8.0.0 for testing
# toml 0.10.2 for configuration reading
RUN pip install --no-cache-dir \
    pylint==3.0.3 \
    pytest==8.0.0 \
    pytest-cov==4.1.0 \
    toml==0.10.2

# Set working directory
WORKDIR /app

# Copy starter project files (DO NOT copy solution/ or tests/)
COPY app/ /app/
