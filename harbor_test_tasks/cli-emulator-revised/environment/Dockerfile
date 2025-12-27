FROM python:3.11-slim-bookworm

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    CLOUDSDK_CORE_DISABLE_PROMPTS=1 \
    CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1 \
    AZURE_CORE_DISABLE_TELEMETRY=1 \
    AZURE_EXTENSION_USE_DYNAMIC_INSTALL=no \
    PYTHONUNBUFFERED=1

# System deps:
# - openjdk: Pub/Sub emulator
# - nodejs/npm: Azurite
# - curl/gnupg/ca-certificates: add Google Cloud APT repo
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gnupg \
      openjdk-17-jre-headless \
      nodejs \
      npm \
      procps \
    && rm -rf /var/lib/apt/lists/*

# Google Cloud CLI + Pub/Sub emulator (installed at image build time; no runtime downloads).
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /etc/apt/keyrings/google-cloud.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/google-cloud.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      google-cloud-cli \
      google-cloud-cli-pubsub-emulator \
    && rm -rf /var/lib/apt/lists/*

# Pinned Python CLIs + libraries.
# - awscli: used to talk to the S3 endpoint
# - moto[server]: lightweight S3-compatible mock (replaces heavy LocalStack runtime)
# - azure-cli: used to talk to Azurite (storage commands)
# NOTE: pytest moved to test.sh to keep test deps separate
RUN pip install --no-cache-dir \
      awscli==1.34.33 \
      "moto[server]==5.1.0" \
      azure-cli==2.64.0

# Pinned Azurite.
RUN npm install -g azurite@3.33.0

# Starter project lives under /app.
COPY app/ /app/

RUN chmod -R a+rx /app/bin


