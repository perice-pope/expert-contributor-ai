# Maintainer Notes

## Intended agent failure modes
- Leaves password authentication enabled or omits `AuthorizedKeysFile none`, so raw keys/pass auth still work (tests force failures).
- Signs only the user cert but forgets host certificates or host CA entries, causing host-key prompts with `StrictHostKeyChecking=yes`.
- Updates client `ProxyJump` but skips ControlMaster/ControlPath, so scp/second connections re-prompt or hang.
- Adds `@cert-authority` but does not hash `known_hosts`, so lookups fail and tests reject.
- Forgets `AuthorizedPrincipalsFile` content (`appuser`) on the internal host, causing cert auth to fail even though a CA is set.
- Generates certs with the wrong principal or omits `-h` on host certs, leading to opaque sshd errors during startup.

## Test design highlights
- Behavioral tests start real sshd instances on 2222/2223, then exercise ssh + scp through ProxyJump with ControlMaster and `StrictHostKeyChecking=yes`.
- Negative coverage: raw key auth fails, password auth fails, and host CA presence is verified via hashed `known_hosts`.
- Config parsing is light-touch (presence checks) but runtime behavior is decisive (actual ssh/scp success/failure).

## Determinism and reproducibility
- Debian 12 base with pinned openssh + python package versions.
- Pre-generated host/user private keys ship in `/app`; agents create deterministic CA material and certs during solve.
- Tests avoid network access and poll sshd ports with bounded timeouts for stability.

