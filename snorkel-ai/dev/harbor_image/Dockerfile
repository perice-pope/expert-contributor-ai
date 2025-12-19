FROM python:3.12-slim-bookworm

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Harbor CLI (pinned). This image is only for task authors on hosts without Python 3.12+.
RUN python -m pip install --no-cache-dir "harbor==0.1.25"

WORKDIR /workspace

ENTRYPOINT ["harbor"]



