# Creating Docker Environment

Place the Dockerfile in `environment/`. Keep it reproducible, lightweight, and non-privileged.

## Basic Dockerfile
`environment/Dockerfile` template:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (PIN VERSIONS!)
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.1.0 \
    requests==2.31.0

# Copy task files
COPY app/ /app/

# Set up environment
ENV PYTHONPATH=/app
```

## Key Principles
1) **Pin all dependencies**  
```dockerfile
# Good
RUN pip install numpy==1.26.4

# Bad
RUN pip install numpy
RUN pip install numpy>=1.0
```
System packages (apt-get) do not need pinning.

2) **Never copy solution or tests**  
```dockerfile
# WRONG - Never do this!
COPY solution/ /solution/
COPY tests/ /tests/
```

3) **No privileged mode**  
```yaml
# WRONG - Never use this!
services:
  task:
    privileged: true
```

4) **Keep images lightweight**  
- Use slim base images.  
- Clean apt cache.  
- Avoid unnecessary packages.

## docker-compose.yaml
```yaml
version: "3.8"
services:
  task:
    build: .
    working_dir: /app
    volumes:
      - ./workspace:/workspace
    environment:
      - PYTHONPATH=/app
```

## Multi-Container Setup
```yaml
version: "3.8"
services:
  app:
    build: .
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
```

## Common Patterns

### Python project
```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app
```

### Node.js project
```dockerfile
FROM node:20-slim
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY src/ /app/src/
```

### System administration task
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*
```

### Git repository task
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Pin to a specific commit to prevent cheating
RUN git clone https://github.com/example/repo.git /app \
    && cd /app && git checkout abc123def
```

## Troubleshooting

### Build fails
```bash
cd environment
docker build -t my-task .
docker run -it my-task bash
```

### Container won't start
```bash
docker-compose logs
```

### Permission issues (macOS)
Enable Docker socket access: Settings → Advanced → “Allow the default Docker socket to be used”.

## CI Checks
Your Dockerfile is validated for:
- `pinned_dependencies`: pip packages have versions.
- `tests_or_solution_in_image`: no solution/tests copied.
- `check_dockerfile_references`: no forbidden references.
- `check_privileged_containers`: no privileged mode.
