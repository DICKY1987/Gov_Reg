#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
INDEX_DIR = ROOT / "indexes"

INDEX_FILES = {
    "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json": INDEX_DIR / "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.index.json",
    "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json": INDEX_DIR / "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.index.json",
    "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json": INDEX_DIR / "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.index.json",
}


def load_index(file_name: str) -> dict[str, Any]:
    path = INDEX_FILES[file_name]
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(file_name: str, semantic_id: str) -> str:
    artifact = load_index(file_name)
    matches: list[str] = []
    for entries in artifact.get("maps", {}).values():
        if semantic_id in entries:
            matches.append(entries[semantic_id])
    if not matches:
        raise KeyError(f"Unknown semantic id: {semantic_id}")
    if len(matches) > 1:
        raise KeyError(f"Ambiguous semantic id: {semantic_id}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve semantic IDs to RFC-6901 JSON Pointers.")
    parser.add_argument("--file", required=True, choices=sorted(INDEX_FILES), help="Indexed JSON source file name.")
    parser.add_argument("--id", required=True, dest="semantic_id", help="Semantic identity to resolve.")
    args = parser.parse_args()

    try:
        pointer = resolve(args.file, args.semantic_id)
    except KeyError as exc:
        print(json.dumps({"error": str(exc), "file": args.file, "semantic_id": args.semantic_id}, sort_keys=True))
        raise SystemExit(1) from exc
    print(json.dumps({"file": args.file, "semantic_id": args.semantic_id, "pointer": pointer}, sort_keys=True))


if __name__ == "__main__":
    main()
