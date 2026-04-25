#!/usr/bin/env python3
"""Apply an RFC-6902 JSON patch to a JSON document in-place."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonpatch


def main() -> None:
    p = argparse.ArgumentParser(description="Apply RFC-6902 patch to a JSON document.")
    p.add_argument("target", help="Path to the JSON document to patch in-place.")
    p.add_argument("patch", help="Path to the RFC-6902 patch file.")
    p.add_argument("--dry-run", action="store_true", help="Print result without writing.")
    args = p.parse_args()

    target = Path(args.target)
    doc = json.loads(target.read_text(encoding="utf-8"))
    ops = json.loads(Path(args.patch).read_text(encoding="utf-8"))
    result = jsonpatch.apply_patch(doc, ops)
    out = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(out)
    else:
        target.write_text(out, encoding="utf-8")
        print(f"Patched: {target}")


if __name__ == "__main__":
    main()
