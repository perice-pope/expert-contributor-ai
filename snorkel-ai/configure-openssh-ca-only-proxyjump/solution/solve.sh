#!/bin/bash
# CANARY_STRING_PLACEHOLDER
set -euo pipefail

cd /app

echo "==> Creating CA keys if missing"
if [ ! -f /app/ca/ssh_user_ca ]; then
  ssh-keygen -t ed25519 -N '' -f /app/ca/ssh_user_ca -C 'user-ca'
fi
if [ ! -f /app/ca/ssh_host_ca ]; then
  ssh-keygen -t ed25519 -N '' -f /app/ca/ssh_host_ca -C 'host-ca'
fi

echo "==> Signing host keys with host CA"
ssh-keygen -h -s /app/ca/ssh_host_ca -I bastion-host -n bastion,127.0.0.1 -V -1d:+52w /app/bastion/ssh_host_ed25519_key.pub
ssh-keygen -h -s /app/ca/ssh_host_ca -I internal-host -n internal,127.0.0.1 -V -1d:+52w /app/internal/ssh_host_ed25519_key.pub

echo "==> Issuing user certificate for appuser"
ssh-keygen -s /app/ca/ssh_user_ca -I appuser-cert -n appuser -V -1d:+52w /app/client/id_client.pub

echo "==> Writing bastion sshd_config"
cat >/app/bastion/sshd_config <<'EOF'
Port 2222
ListenAddress 0.0.0.0
Protocol 2
HostKey /app/bastion/ssh_host_ed25519_key
HostCertificate /app/bastion/ssh_host_ed25519_key-cert.pub

UsePAM no
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile none
TrustedUserCAKeys /app/ca/ssh_user_ca.pub
AllowUsers appuser

ClientAliveInterval 120
ClientAliveCountMax 2
Subsystem sftp internal-sftp
LogLevel VERBOSE
EOF

echo "==> Writing internal sshd_config"
cat >/app/internal/sshd_config <<'EOF'
Port 2223
ListenAddress 0.0.0.0
Protocol 2
HostKey /app/internal/ssh_host_ed25519_key
HostCertificate /app/internal/ssh_host_ed25519_key-cert.pub

UsePAM no
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile none
TrustedUserCAKeys /app/ca/ssh_user_ca.pub
AuthorizedPrincipalsFile /app/internal/authorized_principals
AllowUsers appuser

ClientAliveInterval 120
ClientAliveCountMax 2
Subsystem sftp internal-sftp
LogLevel VERBOSE
EOF

echo "==> Setting allowed principals"
echo "appuser" >/app/internal/authorized_principals

echo "==> Updating client ssh_config with ProxyJump + ControlMaster"
cat >/app/client/ssh_config <<'EOF'
Host bastion
    HostName 127.0.0.1
    Port 2222
    User appuser
    StrictHostKeyChecking yes
    UserKnownHostsFile /app/client/known_hosts
    IdentityFile /app/client/id_client
    CertificateFile /app/client/id_client-cert.pub

Host app-via-bastion
    HostName 127.0.0.1
    Port 2223
    User appuser
    ProxyJump bastion
    StrictHostKeyChecking yes
    UserKnownHostsFile /app/client/known_hosts
    IdentityFile /app/client/id_client
    CertificateFile /app/client/id_client-cert.pub
    ControlMaster auto
    ControlPath /tmp/ssh-%r@%h:%p
    ControlPersist yes
    ServerAliveInterval 30
    ServerAliveCountMax 2
EOF

echo "==> Populating known_hosts with CA and bastion host key, then hashing"
HOST_CA_LINE="$(cat /app/ca/ssh_host_ca.pub)"
BASTION_KEY_LINE="$(cat /app/bastion/ssh_host_ed25519_key.pub)"
rm -f /app/client/known_hosts.old
cat >/app/client/known_hosts <<EOF
@cert-authority [127.0.0.1]:2222 ${HOST_CA_LINE}
@cert-authority [127.0.0.1]:2223 ${HOST_CA_LINE}
[127.0.0.1]:2222 ${BASTION_KEY_LINE}
EOF
ssh-keygen -H -f /app/client/known_hosts
rm -f /app/client/known_hosts.old

echo "==> Fixing permissions"
/app/bin/fix_permissions.sh

echo "==> Smoke test: config checks"
/usr/sbin/sshd -t -f /app/bastion/sshd_config
/usr/sbin/sshd -t -f /app/internal/sshd_config

echo "==> Done. Ready to run tests."
