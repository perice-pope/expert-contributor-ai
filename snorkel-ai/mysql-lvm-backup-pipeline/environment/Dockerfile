FROM debian:bookworm-slim

# Install system dependencies
# Note: LVM and MySQL require specific setup
# Include curl and python3/pip for tests to avoid runtime installation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    lvm2 \
    default-mysql-server \
    default-mysql-client \
    rsync \
    cron \
    procps \
    gawk \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Pre-install uv for faster Python package management
RUN curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Pre-install pytest and pytest-json-ctrf to avoid runtime installation issues
# Debian bookworm requires --break-system-packages flag
RUN pip3 install --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5

# Set up MySQL
RUN mkdir -p /var/run/mysqld && \
    chown mysql:mysql /var/run/mysqld && \
    chmod 755 /var/run/mysqld

# Initialize MySQL data directory (will be moved to LVM later)
# MariaDB uses mariadb-install-db instead of mysqld --initialize-insecure
RUN mariadb-install-db --user=mysql --datadir=/var/lib/mysql --skip-test-db

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /backups/mysql /var/log /mnt/mysql_snapshot && \
    chmod 755 /backups/mysql /var/log /mnt/mysql_snapshot

# Copy starter project files (broken backup script)
COPY app/ /app/

# Set up LVM and MySQL data on logical volume
# This is done via an init script that runs at container start
COPY environment/init-lvm.sh /usr/local/bin/init-lvm.sh
RUN chmod +x /usr/local/bin/init-lvm.sh

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Default command runs init script then keeps container alive
CMD ["/bin/bash", "-c", "/usr/local/bin/init-lvm.sh && tail -f /dev/null"]
