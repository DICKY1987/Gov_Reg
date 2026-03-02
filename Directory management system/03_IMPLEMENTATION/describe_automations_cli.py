#!/usr/bin/env python3
"""
describe_automations_cli.py

Scan a file or directory for .py files, generate:
- <stem>.automation_descriptor.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from automation_descriptor_extractor import AutomationDescriptorExtractor


def iter_py_files(p: Path):
    if p.is_file():
        if p.suffix.lower() == ".py":
            yield p
        return
    for f in p.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in f.parts):
            continue
        yield f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Python file or directory")
    ap.add_argument("--out", default="", help="Output directory (default: alongside each script)")
    args = ap.parse_args()

    target = Path(args.path).resolve()
    out_dir = Path(args.out).resolve() if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    extractor = AutomationDescriptorExtractor()

    for f in iter_py_files(target):
        res = extractor.extract_file(f)
        out_json = extractor.to_json(res)

        if out_dir:
            out_path = out_dir / f"{f.stem}.automation_descriptor.json"
        else:
            out_path = f.with_suffix(f.suffix + ".automation_descriptor.json")

        out_path.write_text(out_json, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
