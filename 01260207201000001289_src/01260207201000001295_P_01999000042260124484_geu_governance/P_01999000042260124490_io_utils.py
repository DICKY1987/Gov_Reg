"""GEU governance I/O utilities.

FILE_ID: 0199900004226012490
DOC_ID: DOC-CORE-GEU-GOVERNANCE-IO-UTILS-0199900004226012490
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

JSON = Dict[str, Any]

def read_json(path: Path) -> JSON:
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, obj: Any, *, indent: int = 2, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")

def write_jsonl(path: Path, records: Iterable[JSON]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(rec, sort_keys=True, ensure_ascii=False) for rec in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

def file_id_index_from_registry(registry: JSON) -> Dict[str, JSON]:
    idx: Dict[str, JSON] = {}
    for rec in registry.get("files", []):
        fid = rec.get("file_id")
        if fid:
            idx[str(fid)] = rec
    return idx
