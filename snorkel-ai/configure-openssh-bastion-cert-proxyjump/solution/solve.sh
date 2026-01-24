#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

ROOT="${APP_ROOT:-/app}"
cd "$ROOT"

rm -f "$ROOT/client/known_hosts" "$ROOT/client/known_hosts.old"

cat <<CONF > "$ROOT/bastion/sshd_config"
Port 2222
ListenAddress 127.0.0.1
Protocol 2
HostKey $ROOT/bastion/ssh_host_ed25519_key
PasswordAuthentication no
PubkeyAuthentication yes
TrustedUserCAKeys $ROOT/ca/user_ca.pub
AuthorizedPrincipalsFile $ROOT/bastion/authorized_principals
AuthorizedKeysFile none
AllowUsers appuser
UsePAM no
LogLevel VERBOSE
AllowTcpForwarding yes
GatewayPorts no
ClientAliveInterval 60
Subsystem sftp /usr/lib/openssh/sftp-server
CONF

echo "appuser" > "$ROOT/bastion/authorized_principals"

cat <<CONF > "$ROOT/apphost/sshd_config"
Port 2223
ListenAddress 127.0.0.1
Protocol 2
HostKey $ROOT/apphost/ssh_host_ed25519_key
HostCertificate $ROOT/apphost/ssh_host_ed25519_key-cert.pub
PasswordAuthentication no
PubkeyAuthentication yes
TrustedUserCAKeys $ROOT/ca/user_ca.pub
AuthorizedPrincipalsFile $ROOT/apphost/authorized_principals
AllowUsers appuser
UsePAM no
ClientAliveInterval 60
Subsystem sftp /usr/lib/openssh/sftp-server
CONF

echo "appuser" > "$ROOT/apphost/authorized_principals"

cat <<CONF > "$ROOT/client/ssh_config"
# Connection multiplexing configured for bastion only
# ProxyJump connections work better without global ControlMaster
Compression yes

Host bastion
  HostName 127.0.0.1
  Port 2222
  User appuser
  IdentityFile $ROOT/client/id_client
  CertificateFile $ROOT/client/id_client-cert.pub
  UserKnownHostsFile $ROOT/client/known_hosts
  StrictHostKeyChecking yes
  BatchMode yes
  LogLevel ERROR
  ControlMaster auto
  ControlPath /tmp/ssh-%r@%h:%p
  ControlPersist 10m

Host app-via-bastion
  HostName 127.0.0.1
  Port 2223
  User appuser
  IdentityFile $ROOT/client/id_client
  CertificateFile $ROOT/client/id_client-cert.pub
  ProxyJump bastion
  UserKnownHostsFile $ROOT/client/known_hosts
  StrictHostKeyChecking yes
  BatchMode yes
  LogLevel ERROR
CONF

cat <<CONF > "$ROOT/client/known_hosts"
@cert-authority [127.0.0.1]:2223 $(cat "$ROOT/ca/host_ca.pub")
[127.0.0.1]:2222 $(cat "$ROOT/bastion/ssh_host_ed25519_key.pub")
CONF

ssh-keygen -H -f "$ROOT/client/known_hosts" -N '' >/dev/null
rm -f "$ROOT/client/known_hosts.old"

"$ROOT/bin/fix_permissions.sh"

echo "Configs staged. Run sshd -t to verify, then start bastion and app to test ProxyJump." >&2
