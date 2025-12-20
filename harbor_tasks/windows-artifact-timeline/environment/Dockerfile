FROM python:3.11.9-slim-bookworm

# Install system dependencies (system packages don't need version pinning per Harbor docs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for test dependencies (pinned version)
RUN curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy the application code (but NOT solution/ or tests/)
COPY app/ /app/

# Ensure the output directory exists
RUN mkdir -p /output

# Set Python to use UTF-8 encoding
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Default command (can be overridden)
CMD ["python3", "/app/timeline_tool.py"]
