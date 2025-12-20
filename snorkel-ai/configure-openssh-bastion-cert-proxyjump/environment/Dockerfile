FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      openssh-client=1:9.2p1-2+deb12u7 \
      openssh-server=1:9.2p1-2+deb12u7 \
      passwd=1:4.13+dfsg1-1+deb12u1 \
      netcat-openbsd=1.219-1 \
      tini=0.19.0-1+b3 \
      tmux=3.3a-3 \
      asciinema=2.2.0-1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==8.3.3

WORKDIR /app

COPY app/ /app/

RUN mkdir -p /var/run/sshd

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash"]
