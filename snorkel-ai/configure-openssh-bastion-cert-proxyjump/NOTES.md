# Maintainer Notes

## Intent and failure modes
- Agents often stop after getting a single sshd working; here they must fix both bastion and app configs plus the client side.
- Missing `TrustedUserCAKeys` on either sshd leads to auth failures; missing `HostCertificate` breaks host CA trust.
- Skipping `ProxyJump` makes the config check fail (`ssh -G`), even if direct access happens to work.
- Leaving `known_hosts` unhashed or without `@cert-authority` causes host-key verification failures (StrictHostKeyChecking=yes).
- Expired and wrong-principal certs ensure agents don’t blanket-accept any certificate.

## Test design
- `ssh -G` enforces ProxyJump presence rather than trusting that app host is reached directly.
- Behavioral checks use real sshd instances with the provided keys; success path requires CA trust, host cert, ProxyJump, and hashed known_hosts.
- Negative tests swap in expired and wrong-principal certificates to confirm correct rejection.
- `known_hosts` hashing is validated by absence of clear-text hosts and presence of `|1|` plus `@cert-authority`.

## Determinism
- All keys and certs are pre-generated and checked in; no network access or runtime downloads.
- Dockerfile pins base image and package versions; pytest pinned.
- Tests create users and run sshd locally with fixed ports (2222/2223) and short timeouts.
- `fix_permissions.sh` keeps file modes consistent across runs.
