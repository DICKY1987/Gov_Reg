"""GEU governance CLI interface.

FILE_ID: 0199900004226012486
DOC_ID: DOC-CORE-GEU-GOVERNANCE-CLI-0199900004226012486
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .P_01999000042260124487_constants import FILE_REGISTRY_OVERLAY_PATH, GEU_EDGES_PATH, GEU_INDEX_PATH
from .P_01999000042260124488_generate import write_generated_artifacts, persist_generated_artifacts
from .P_01999000042260124491_report import build_report, write_reports

def _render_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

def _render_jsonl(records: Any) -> str:
    return "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in records) + ("\n" if records else "")

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def cmd_all(write: bool) -> int:
    bundle = write_generated_artifacts(write=write)
    report = build_report(findings=bundle["findings"], edge_schema_errors=bundle["edge_schema_errors"])
    write_reports(report)

    if not report["passed"]:
        if write:
            raise SystemExit("Refusing to write generated artifacts because validation failed. Fix findings first.")
        return 1

    if write:
        persist_generated_artifacts(bundle)
        return 0

    expected_index = _render_json(bundle["index"])
    expected_edges = _render_jsonl(bundle["edges"])
    expected_overlay = _render_json(bundle["overlay"])

    drift = []
    if _read_text(GEU_INDEX_PATH) != expected_index:
        drift.append(str(GEU_INDEX_PATH))
    if _read_text(GEU_EDGES_PATH) != expected_edges:
        drift.append(str(GEU_EDGES_PATH))
    if _read_text(FILE_REGISTRY_OVERLAY_PATH) != expected_overlay:
        drift.append(str(FILE_REGISTRY_OVERLAY_PATH))

    if drift:
        raise SystemExit("Generated artifact drift detected (re-run with --write to refresh):\n  - " + "\n  - ".join(drift))
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="geu_governance", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    allp = sub.add_parser("all", help="Validate GEU entries, write evidence report, and (optionally) write generated artifacts.")
    allp.add_argument("--write", action="store_true", help="Write generated artifacts (index/edges/overlay). Without this flag, performs drift check only.")
    return p

def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    if args.cmd == "all":
        return cmd_all(write=bool(args.write))
    raise SystemExit("Unknown command")

if __name__ == "__main__":
    raise SystemExit(main())
