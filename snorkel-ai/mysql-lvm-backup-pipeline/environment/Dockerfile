FROM debian:bookworm-slim

# Install system dependencies
# Note: LVM and MySQL require specific setup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    lvm2 \
    mysql-server \
    mysql-client \
    rsync \
    cron \
    procps \
    gawk \
    && rm -rf /var/lib/apt/lists/*

# Set up MySQL
RUN mkdir -p /var/run/mysqld && \
    chown mysql:mysql /var/run/mysqld && \
    chmod 755 /var/run/mysqld

# Initialize MySQL data directory (will be moved to LVM later)
RUN mysqld --initialize-insecure --user=mysql --datadir=/var/lib/mysql

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
