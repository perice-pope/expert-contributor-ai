FROM debian:bookworm-slim

# Pin package versions for determinism
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    cmake=3.25.1-1 \
    clang=1:14.0-55.7~deb12u1 \
    libomp-dev=1:14.0-55.7~deb12u1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set Clang as default compiler
ENV CC=clang
ENV CXX=clang++

# Copy app directory (Harbor will mount it, but we copy for build context)
COPY app/ /app/

WORKDIR /app
