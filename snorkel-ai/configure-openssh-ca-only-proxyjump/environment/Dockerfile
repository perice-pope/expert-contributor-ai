FROM debian:12.7-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      openssh-server=1:9.2p1-2+deb12u7 \
      openssh-client=1:9.2p1-2+deb12u7 \
      python3=3.11.2-1+b1 \
      python3-pip=23.0.1+dfsg-1 \
      python3-venv=3.11.2-1+b1 \
      ca-certificates=20230311+deb12u1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Note: pytest is installed in tests/test.sh, not in the Docker image

WORKDIR /app

COPY app /app/

RUN mkdir -p /var/run/sshd /logs/verifier && \
    chmod 755 /var/run/sshd
