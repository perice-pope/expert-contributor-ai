#!/bin/bash
set -euo pipefail

BASE="/app"

chmod 700 "${BASE}/bastion" "${BASE}/client" "${BASE}/ca"
chmod 755 "${BASE}/internal"

find "${BASE}/bastion" -type f -name "ssh_host_ed25519_key" -exec chmod 600 {} \;
find "${BASE}/internal" -type f -name "ssh_host_ed25519_key" -exec chmod 600 {} \;
find "${BASE}/client" -type f -name "id_client" -exec chmod 600 {} \;
find "${BASE}/ca" -type f -name "ssh_*_ca" -exec chmod 600 {} \;
find "${BASE}/ca" -type f -name "*.pub" -exec chmod 644 {} \;
find "${BASE}" -type f \( -name "*.pub" -o -name "*-cert.pub" \) -exec chmod 644 {} \;

touch "${BASE}/client/known_hosts"
chmod 600 "${BASE}/client/known_hosts"
rm -f "${BASE}/client/known_hosts.old"

touch "${BASE}/internal/authorized_principals"
chmod 644 "${BASE}/internal/authorized_principals"

chmod 755 "${BASE}/bin"

