# Configure OpenSSH Bastion ProxyJump with CAs

You have a prewired mini-lab with two sshd instances (a bastion on port 2222 and an app host on port 2223). The provided keys and certs are correct but the configs are not. Wire up ProxyJump through the bastion, enable OpenSSH certificate-based auth (user CA + host CA), and make sure host trust is non-interactive via hashed `known_hosts` with `@cert-authority`.

## Requirements
1. Configure the bastion sshd (`/app/bastion/sshd_config`) to accept the provided user CA for principal `appuser` on port 2222 (no passwords), suitable for ProxyJump use.
2. Configure the app sshd (`/app/apphost/sshd_config`) to present the provided host certificate and to trust the same user CA via `AuthorizedPrincipalsFile` so `appuser` can log in on port 2223.
3. Update the client config (`/app/client/ssh_config`) to ProxyJump through the bastion, use the provided client key + certificate, keep `StrictHostKeyChecking yes`, and rely on `/app/client/known_hosts` only.
4. Ensure `/app/client/known_hosts` is hashed and contains an `@cert-authority` entry for the host CA plus the bastion host key so no host-key prompts appear in batch mode.
5. Show that `ssh -F /app/client/ssh_config app-via-bastion -- echo ok` succeeds without prompts, while attempts using the expired cert or wrong principal cert fail (non-zero).

## Constraints
- Do not regenerate or replace any keys/certs under `/app/ca`, `/app/client`, or `/app/apphost`; configure with what is provided.
- No network access; keep everything offline and inside `/app`.
- Keep ports as-is: 2222 (bastion) and 2223 (app host).
- Do not weaken security (no `StrictHostKeyChecking no`, no password auth, no disabling CA checks).
- Avoid copying tests or solution artifacts into the runtime image.

## Files
- `/app/bastion/sshd_config`
- `/app/apphost/sshd_config`
- `/app/apphost/authorized_principals`
- `/app/client/ssh_config`
- `/app/client/known_hosts`
- `/app/ca/*` (provided CAs; leave untouched)
- `/app/apphost/ssh_host_ed25519_key*` and certificate
- `/app/client/id_client*` (provided client key + certs)

## Outputs
- `/app/bastion/sshd_config`: bastion sshd configured to trust the user CA on port 2222 for ProxyJump.
- `/app/apphost/sshd_config` and `/app/apphost/authorized_principals`: app sshd presenting its host cert and trusting the user CA for `appuser`.
- `/app/client/ssh_config`: ProxyJump through the bastion with the provided key + certificate and strict host checks.
- `/app/client/known_hosts`: hashed entries including `@cert-authority` for the host CA and the bastion host key, enabling non-interactive host trust.
