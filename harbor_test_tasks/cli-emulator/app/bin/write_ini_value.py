#!/usr/bin/env python3
"""
Write/update a single INI key while preserving unrelated sections/keys.

Used to persist profile-like settings in standard CLI config files.
"""

from __future__ import annotations

import argparse
import configparser
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--path", required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    args = p.parse_args()

    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cfg = configparser.ConfigParser(interpolation=None)
    if path.exists():
        cfg.read(path)

    if not cfg.has_section(args.section):
        cfg.add_section(args.section)

    cfg.set(args.section, args.key, args.value)

    with path.open("w", encoding="utf-8") as f:
        cfg.write(f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())



