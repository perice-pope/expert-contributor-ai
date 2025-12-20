FROM python:3.11-slim-bookworm

# Install system dependencies for image processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
# Pillow 10.0.0 for image processing
RUN pip install --no-cache-dir Pillow==10.0.0

# Set working directory
WORKDIR /app

# Create images output directory
RUN mkdir -p /app/images

# Copy starter project files
COPY app/ /app/
