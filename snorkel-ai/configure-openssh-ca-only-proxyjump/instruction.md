# Configure OpenSSH CA Bastion with ProxyJump & ControlMaster

You have two local sshd instances acting as a bastion (port 2222) and an internal host (port 2223). Wire them to trust only CA-signed user certs, present CA-signed host certs, and reach the internal host via the bastion using ProxyJump and ControlMaster with strict host checks.

## Requirements
1. Create an SSH user CA and host CA under `/app/ca/`, sign the provided bastion and internal host keys with the host CA, and sign the provided client key for principal `appuser` with the user CA (no passwords or raw public keys).
2. Configure bastion sshd at `/app/bastion/sshd_config` (port 2222) to accept only the user CA for `appuser`, disable password auth, and serve its host certificate.
3. Configure internal sshd at `/app/internal/sshd_config` (port 2223) to use its host certificate, trust the same user CA via `AuthorizedPrincipalsFile` containing `appuser`, and disallow password/keyboard-interactive auth.
4. Update the client config `/app/client/ssh_config` to use ProxyJump through the bastion, ControlMaster/ControlPath (e.g., `/tmp/ssh-%r@%h:%p`) for multiplexing, `StrictHostKeyChecking yes`, the provided key + certificate, and only `/app/client/known_hosts` for host trust.
5. Hash `/app/client/known_hosts` and include both `@cert-authority` for the host CA and the bastion host key so `ssh` and `scp` to `app-via-bastion` run non-interactively with `StrictHostKeyChecking=yes`, while attempts with an unsigned key or a wrong/expired cert fail.

## Constraints
- Do not replace the provided private keys under `/app/bastion`, `/app/internal`, or `/app/client`; only add certificates/CA material.
- No network access; everything must run offline inside `/app`.
- Keep ports fixed: bastion 2222, internal 2223.
- Do not weaken security: keep `StrictHostKeyChecking yes`, no password auth, no bypassing CA validation.
- Do not copy `tests/` or `solution/` into the runtime image.

## Files
- `/app/ca/` (CA keys and certs you create)
- `/app/bastion/sshd_config`, `/app/bastion/ssh_host_ed25519_key*`
- `/app/internal/sshd_config`, `/app/internal/authorized_principals`, `/app/internal/ssh_host_ed25519_key*`
- `/app/client/ssh_config`, `/app/client/known_hosts`, `/app/client/id_client*`

## Outputs
- `/app/ca/ssh_user_ca` and `/app/ca/ssh_host_ca` with matching `.pub` and host/user certificates issued.
- `/app/bastion/sshd_config` and `/app/internal/sshd_config` enforcing CA-only auth on ports 2222/2223 with host certs loaded.
- `/app/internal/authorized_principals` listing `appuser`.
- `/app/client/ssh_config` using ProxyJump + ControlMaster and strict host checks.
- `/app/client/known_hosts` hashed with `@cert-authority` for the host CA and the bastion host key, enabling prompt-free ssh/scp to `app-via-bastion`.
