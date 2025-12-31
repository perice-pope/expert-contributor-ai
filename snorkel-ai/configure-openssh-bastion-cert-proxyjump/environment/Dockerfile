FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      openssh-client \
      openssh-server \
      passwd \
      netcat-openbsd \
      tini \
      tmux \
      asciinema \
    && rm -rf /var/lib/apt/lists/*

# pytest installed in test.sh, not in image

WORKDIR /app

COPY app/ /app/

RUN mkdir -p /var/run/sshd

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash"]
