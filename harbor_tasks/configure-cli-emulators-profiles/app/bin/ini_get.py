#!/usr/bin/env python3
"""
Read a single INI key.

Exit codes:
- 0: printed value
- 2: missing section or key
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
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        return 2

    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)

    if not cfg.has_section(args.section):
        return 2
    if not cfg.has_option(args.section, args.key):
        return 2

    print(cfg.get(args.section, args.key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



