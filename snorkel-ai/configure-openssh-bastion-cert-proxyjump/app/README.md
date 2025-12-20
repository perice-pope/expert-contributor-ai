Starter SSH lab layout:
- Bastion sshd listens on 2222 using /app/bastion/sshd_config (CA trust not wired).
- App sshd listens on 2223 using /app/apphost/sshd_config (host cert + CA trust not wired).
- Client bits in /app/client (ProxyJump missing, known_hosts unhashed, no @cert-authority entry).
- CAs live in /app/ca (do not rotate them).

Use /app/bin/fix_permissions.sh if sshd complains about key modes.
