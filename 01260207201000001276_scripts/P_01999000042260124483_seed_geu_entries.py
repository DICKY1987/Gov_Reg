#!/usr/bin/env python3
"""Seed GEU entry files by parsing a subsystem map (markdown) and a file registry.

FILE_ID: 01999000042260124483
DOC_ID: P_01999000042260124483

Deterministic and safe to re-run:
- Will not overwrite existing <geu_id>.json unless --overwrite.
- Writes seed_report.json summarizing match resolution and ambiguities.

Usage:
  PYTHONPATH=src python scripts/seed_geu_entries_from_subsystem_map.py \
    --map AI_PROD_PIPELINE_DETAILED_SUBSYSTEM_MAP.md \
    --registry governance_registry.json \
    --out governance/geu-registry/entries \
    --overwrite
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from P_01999000042260124484_geu_governance.P_01999000042260124489_id_scheme import make_geu_id
from P_01999000042260124484_geu_governance.P_01999000042260124490_io_utils import read_json, write_json
from P_01999000042260124484_geu_governance.P_01999000042260124487_constants import GEU_TYPE_CODES_PATH

JSON = Dict[str, Any]

HEADER_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
FILE_RE = re.compile(r"`([^`]+)`")

def guess_geu_type(title: str) -> str:
    t = title.lower()
    if "work unit" in t or "schema" in t:
        return "SCHEMA_BASED"
    if "registry" in t or "ssot" in t or "rules" in t:
        return "RULE_BASED"
    if "runner" in t or "gate" in t or "pipeline" in t:
        return "RUNNER_BASED"
    if "evidence" in t:
        return "EVIDENCE_ONLY"
    return "OTHER"

def guess_role_slot(filename: str) -> str:
    f = filename.lower()
    if f.endswith(".schema.json") or f.endswith("*schema.json") or ("schema" in f and f.endswith(".json")):
        return "SCHEMA"
    if "validate" in f or "validator" in f:
        return "VALIDATOR"
    if "gate" in f or "runner" in f or "execute" in f:
        return "RUNNER"
    if "failure" in f or "error" in f or "exception" in f:
        return "FAILURE_MODE"
    if f.startswith("test*") or "/tests/" in f or f.endswith("_test.py"):
        return "TEST"
    if "report" in f or "render" in f:
        return "REPORT"
    return "UTILITY"

def find_candidates(registry_files: List[JSON], basename: str) -> List[JSON]:
    b = basename.lower()
    out = []
    for rec in registry_files:
        rp = (rec.get("relative_path") or "").lower()
        if rp.endswith("/" + b) or rp.endswith("\\" + b) or rp.endswith(b):
            out.append(rec)
    return out

def parse_subsystems(md_text: str) -> List[Tuple[str, List[str]]]:
    subs: List[Tuple[str, List[str]]] = []
    cur_title: str | None = None
    cur_files: List[str] = []
    for line in md_text.splitlines():
        m = HEADER_RE.match(line.strip())
        if m:
            if cur_title is not None:
                subs.append((cur_title, cur_files))
            cur_title = m.group("title").strip()
            cur_files = []
            continue
        for f in FILE_RE.findall(line):
            cur_files.append(f)
    if cur_title is not None:
        subs.append((cur_title, cur_files))
    return subs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True, type=Path)
    ap.add_argument("--registry", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    md = args.map.read_text(encoding="utf-8", errors="replace")
    subs = parse_subsystems(md)

    reg = read_json(args.registry)
    reg_files = reg.get("files", [])
    type_codes = read_json(GEU_TYPE_CODES_PATH)

    report: JSON = {"generated": True, "subsystems": []}
    seq_by_prefix: Dict[str, int] = {}

    args.out.mkdir(parents=True, exist_ok=True)

    for title, files in subs:
        geu_type = guess_geu_type(title)
        basenames = [Path(f).name for f in files]

        matches: List[Tuple[str, List[JSON]]] = []
        resolved: List[Tuple[str, JSON]] = []
        for b in basenames:
            cands = find_candidates(reg_files, b)
            matches.append((b, cands))
            if len(cands) == 1:
                resolved.append((b, cands[0]))

        anchor = None
        for b, rec in resolved:
            if guess_role_slot(b) == "SCHEMA":
                anchor = rec
                break
        if anchor is None and resolved:
            anchor = resolved[0][1]

        if anchor is None:
            report["subsystems"].append({
                "title": title,
                "status": "SKIPPED_NO_ANCHOR_MATCH",
                "reason": "No registry match resolved unambiguously.",
                "matches": [(b, [r.get("relative_path") for r in c]) for b, c in matches],
            })
            continue

        prefix_key = f"{geu_type}:{anchor['file_id']}"
        seq = seq_by_prefix.get(prefix_key, 0) + 1
        seq_by_prefix[prefix_key] = seq
        geu_id = make_geu_id(geu_type=geu_type, anchor_file_id=anchor["file_id"], type_codes=type_codes, seq=seq)

        entry_path = args.out / f"{geu_id}.json"
        if entry_path.exists() and not args.overwrite:
            report["subsystems"].append({"title": title, "status": "SKIPPED_EXISTS", "geu_id": geu_id})
            continue

        members = []
        for b, rec in resolved:
            if rec["file_id"] == anchor["file_id"]:
                continue
            members.append({
                "file_id": rec["file_id"],
                "role_slot": guess_role_slot(b),
                "required": False,
                "shared_access": "NONE",
                "notes": f"Seeded from map: {b}",
            })

        entry: JSON = {
            "geu_id": geu_id,
            "geu_type": geu_type,
            "geu_key": title,
            "anchor_file_id": anchor["file_id"],
            "anchor_role_slot": guess_role_slot(Path(anchor["relative_path"]).name),
            "anchor_shared_access": "NONE",
            "members": members,
            "depends_on_geu_ids": [],
            "outputs": [],
            "tests": [],
        }
        entry_path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["subsystems"].append({
            "title": title,
            "status": "WROTE",
            "geu_id": geu_id,
            "anchor_relative_path": anchor.get("relative_path"),
            "resolved_count": len(resolved),
            "ambiguous_count": sum(1 for _, c in matches if len(c) > 1),
        })

    write_json(args.out / "seed_report.json", report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
