#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

chmod 600 \
  "$ROOT/ca/user_ca" \
  "$ROOT/ca/host_ca" \
  "$ROOT/client/id_client" \
  "$ROOT/bastion/ssh_host_ed25519_key" \
  "$ROOT/apphost/ssh_host_ed25519_key"

chmod 644 \
  "$ROOT/ca/user_ca.pub" \
  "$ROOT/ca/host_ca.pub" \
  "$ROOT/client/id_client.pub" \
  "$ROOT/client/id_client-cert.pub" \
  "$ROOT/client/id_client-expired-cert.pub" \
  "$ROOT/client/id_client-wrong-principal-cert.pub" \
  "$ROOT/bastion/ssh_host_ed25519_key.pub" \
  "$ROOT/apphost/ssh_host_ed25519_key.pub" \
  "$ROOT/apphost/ssh_host_ed25519_key-cert.pub" \
  "$ROOT/client/known_hosts" \
  "$ROOT/apphost/authorized_principals"

if id appuser >/dev/null 2>&1; then
  chown appuser:appuser "$ROOT/apphost"
  chown appuser:appuser "$ROOT/apphost/authorized_principals"
fi
