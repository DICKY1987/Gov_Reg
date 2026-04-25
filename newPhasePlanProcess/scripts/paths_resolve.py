#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from src.path_registry import DEFAULT_REGISTRY, resolve_key


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path_key")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = parser.parse_args()
    try:
        print(resolve_key(args.path_key, args.registry))
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
