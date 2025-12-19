#!/bin/bash
set -euo pipefail

# Installs a pinned Harbor CLI into the current user's Python user-base.
# This is for task authors; the tasks themselves must remain offline inside Docker.

HARBOR_VERSION="0.1.25"

echo "[setup_harbor] Installing harbor==${HARBOR_VERSION}"

python_mm="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

# harbor==0.1.25 requires Python >= 3.12. If the host Python is older (common on Debian),
# we install a Docker-based shim instead of trying (and failing) to pip install locally.
if python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
then
  # Debian/Ubuntu may enforce PEP 668 ("externally managed environment"), which blocks
  # `pip install --user`. If that happens, install into a dedicated venv and add a shim.
  if python3 -m pip install --user --upgrade "harbor==${HARBOR_VERSION}" >/dev/null 2>&1; then
USER_BIN="$(python3 -m site --user-base)/bin"
  else
    echo "[setup_harbor] pip --user failed (likely PEP 668). Falling back to venv install..."
    VENV_DIR="${HOME}/.local/share/harbor-cli-${HARBOR_VERSION}"
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade "harbor==${HARBOR_VERSION}" >/dev/null

    mkdir -p "${HOME}/.local/bin"
    ln -sf "${VENV_DIR}/bin/harbor" "${HOME}/.local/bin/harbor"
    USER_BIN="${HOME}/.local/bin"
  fi

  if [ ! -x "${USER_BIN}/harbor" ]; then
    echo "[setup_harbor] ERROR: harbor did not install correctly. Expected ${USER_BIN}/harbor" >&2
    exit 1
  fi
else
  echo "[setup_harbor] Host Python is ${python_mm} (< 3.12); installing a dockerized harbor shim..."

  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  HARBOR_IMAGE="snorkel-harbor:${HARBOR_VERSION}"

  if ! docker image inspect "${HARBOR_IMAGE}" >/dev/null 2>&1; then
    echo "[setup_harbor] Building ${HARBOR_IMAGE} (one-time; requires network to fetch base image + harbor wheel)..."
    docker build -t "${HARBOR_IMAGE}" -f "${REPO_ROOT}/dev/harbor_image/Dockerfile" "${REPO_ROOT}/dev/harbor_image" >/dev/null
  fi

  mkdir -p "${HOME}/.local/bin"
  cat > "${HOME}/.local/bin/harbor" <<EOF
#!/bin/bash
set -euo pipefail

HARBOR_IMAGE="${HARBOR_IMAGE}"

# Ensure the docker socket and compose plugin are available inside the container.
exec docker run --rm -t \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  -v /usr/bin/docker:/usr/bin/docker:ro \\
  -v /usr/libexec/docker/cli-plugins:/usr/libexec/docker/cli-plugins:ro \\
  -v "\${PWD}:/workspace" \\
  -w /workspace \\
  -e HOME=/tmp \\
  "\${HARBOR_IMAGE}" "\$@"
EOF
  chmod +x "${HOME}/.local/bin/harbor"
  USER_BIN="${HOME}/.local/bin"
fi

cat <<EOF

Harbor installed.

Add this to your shell rc if needed:
  export PATH="${USER_BIN}:\$PATH"

Verify:
  harbor --help
  harbor tasks --help

Docker preflight (required for running tasks):
  bash dev/check_docker.sh

EOF


