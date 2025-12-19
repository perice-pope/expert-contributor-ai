#!/usr/bin/env python3
"""
Small deterministic helper to poll for TCP ports.

We keep this in-repo to avoid depending on netcat flavors across distros.
"""

from __future__ import annotations

import argparse
import socket
import time


def can_connect(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tcp", action="append", default=[], help="host:port")
    p.add_argument("--timeout-sec", type=float, default=30.0)
    args = p.parse_args()

    targets: list[tuple[str, int]] = []
    for hp in args.tcp:
        host, port_s = hp.rsplit(":", 1)
        targets.append((host, int(port_s)))

    deadline = time.time() + args.timeout_sec
    pending = set(targets)
    while pending and time.time() < deadline:
        for t in list(pending):
            if can_connect(t[0], t[1]):
                pending.remove(t)
        if pending:
            time.sleep(0.25)

    if pending:
        missing = ", ".join(f"{h}:{p}" for h, p in sorted(pending))
        raise SystemExit(f"Timed out waiting for: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



