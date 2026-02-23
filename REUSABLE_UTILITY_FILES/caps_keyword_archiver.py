#!/usr/bin/env python3
"""
caps_keyword_archiver.py

Identify and move files based on ALL-CAPS filename keywords.
A keyword counts only if it appears as a standalone token in ALL CAPS.

Workflow:
  1) plan  -> scans and writes:
       - MOVE_MANIFEST.json
       - MOVE_PLAN.md
     (no filesystem changes)
  2) apply -> executes moves exactly from MOVE_MANIFEST.json

Default behavior:
  - Only moves files whose filename (stem) contains >=1 CAPS keyword token
  - Destination layout:
      ARCHIVE_DIR\\<KEYS_JOINED>\\ <relative path from PARENT_DIR>
    Example:
      CENTRAL_ARCHIVE\\FINAL__REPORT\\LP_LONG_PLAN\\...\\MY_FINAL_REPORT.md
  - Never overwrites; collisions get a numeric suffix
  - Skips excluded dirs (.git, __pycache__, node_modules, venv, etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- USER DEFAULTS (can override via CLI) ---
DEFAULT_PARENT_DIR = r"C:\Users\richg\Gov_Reg"
DEFAULT_ARCHIVE_DIR = r"C:\Users\richg\CENTRAL_ARCHIVE"

KEYWORDS = {
    "REPORT",
    "COMPLETE",
    "QUICKSTART",
    "GUIDE",
    "CHECKLIST",
    "PLAN",
    "SUMMARY",
    "FINAL",
    "PHASE",
    "WEEK",
    "STATUS",
    "CHAT",
    "SCRIPT",
}

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".svn", ".hg",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".venv", "venv",
    ".idea", ".vscode",
}

TOKEN_SPLIT_RE = re.compile(r"[^A-Za-z0-9]+")  # split on non-alphanumerics


def utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def should_skip_dir(dir_name: str, exclude_dirs: set[str]) -> bool:
    return dir_name in exclude_dirs


def filename_caps_keywords(file_path: Path, keywords: set[str]) -> List[str]:
    """
    Extract ALL-CAPS keyword tokens from the filename stem only.
    Tokenization splits on non-alphanumerics (includes underscores, dashes, spaces, dots, etc.).

    Example:
      "MY_FINAL_REPORT_v2.md" -> tokens: ["MY", "FINAL", "REPORT", "v2"]
      matches -> ["FINAL", "REPORT"]

    A keyword counts only if token == keyword (exact, all caps).
    """
    stem = file_path.stem  # filename without extension
    tokens = [t for t in TOKEN_SPLIT_RE.split(stem) if t]
    matches = [t for t in tokens if t in keywords]
    # de-dupe but preserve order
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def keys_folder_name(keys: List[str]) -> str:
    """
    Deterministic folder naming.
    - sort keys
    - join up to 4 keys with "__"
    - if >4 keys, use "MULTI"
    """
    if not keys:
        return "NO_KEYWORDS"
    k = sorted(keys)
    if len(k) > 4:
        return "MULTI"
    return "__".join(k)


def collision_safe_dest(dest: Path) -> Tuple[Path, str]:
    """
    Never overwrite.
    If dest exists, add _N before suffix.
    Returns (final_dest, note).
    """
    if not dest.exists():
        return dest, "none"

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate, f"rename_{n}"
        n += 1


@dataclass
class PlannedMove:
    src: str
    src_rel: str
    keywords: List[str]
    dest: str
    dest_rel: str
    collision_note: str
    size_bytes: int


def plan(
    parent_dir: Path,
    archive_dir: Path,
    out_dir: Path,
    include_exts: Optional[set[str]],
    exclude_dirs: set[str],
) -> Dict:
    planned: List[PlannedMove] = []
    unmatched_count = 0

    for dirpath, dirnames, filenames in os.walk(parent_dir):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d, exclude_dirs)]

        for fn in filenames:
            src = Path(dirpath) / fn
            try:
                if not src.is_file():
                    continue
            except OSError:
                continue

            # Skip anything already under archive dir (extra safety)
            if is_under(src, archive_dir):
                continue

            # Optional extension filter
            ext = src.suffix.lower()
            if include_exts is not None and ext not in include_exts:
                continue

            keys = filename_caps_keywords(src, KEYWORDS)
            if not keys:
                unmatched_count += 1
                continue

            rel = src.relative_to(parent_dir)
            keys_folder = keys_folder_name(keys)

            dest_requested = archive_dir / keys_folder / rel
            dest_final, note = collision_safe_dest(dest_requested)

            planned.append(
                PlannedMove(
                    src=str(src),
                    src_rel=rel.as_posix(),
                    keywords=keys,
                    dest=str(dest_final),
                    dest_rel=str(dest_final.relative_to(archive_dir)).replace("\\", "/"),
                    collision_note=note,
                    size_bytes=src.stat().st_size,
                )
            )

    manifest = {
        "schema": "caps_keyword_archiver.manifest.v1",
        "created_utc": utc_iso(),
        "parent_dir": str(parent_dir),
        "archive_dir": str(archive_dir),
        "keywords": sorted(KEYWORDS),
        "include_exts": sorted(include_exts) if include_exts is not None else None,
        "exclude_dirs": sorted(exclude_dirs),
        "counts": {
            "planned_moves": len(planned),
            "non_matching_files_seen": unmatched_count,
        },
        "planned_moves": [pm.__dict__ for pm in planned],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "MOVE_MANIFEST.json"
    md_path = out_dir / "MOVE_PLAN.md"

    write_json(manifest_path, manifest)
    write_text(md_path, manifest_to_markdown(manifest))

    return {
        "manifest_path": str(manifest_path),
        "markdown_path": str(md_path),
        "manifest": manifest,
    }


def apply(manifest_path: Path, dry_run: bool) -> Dict:
    manifest = read_json(manifest_path)
    archive_dir = Path(manifest["archive_dir"])

    results = []
    for pm in manifest["planned_moves"]:
        src = Path(pm["src"])
        dest = Path(pm["dest"])

        record = {
            "src": pm["src"],
            "dest": pm["dest"],
            "keywords": pm["keywords"],
            "status": None,
            "error": None,
        }

        try:
            if not src.exists():
                record["status"] = "missing_source"
                results.append(record)
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)

            # final safety: never overwrite
            if dest.exists():
                record["status"] = "dest_exists_skip"
                results.append(record)
                continue

            if not dry_run:
                shutil.move(str(src), str(dest))

            record["status"] = "moved" if not dry_run else "planned_only"
        except Exception as e:
            record["status"] = "error"
            record["error"] = f"{type(e).__name__}: {e}"

        results.append(record)

    report = {
        "schema": "caps_keyword_archiver.apply_report.v1",
        "applied_utc": utc_iso(),
        "dry_run": dry_run,
        "manifest_path": str(manifest_path),
        "results": results,
        "counts": {
            "total": len(results),
            "moved": sum(1 for r in results if r["status"] == "moved"),
            "planned_only": sum(1 for r in results if r["status"] == "planned_only"),
            "missing_source": sum(1 for r in results if r["status"] == "missing_source"),
            "dest_exists_skip": sum(1 for r in results if r["status"] == "dest_exists_skip"),
            "error": sum(1 for r in results if r["status"] == "error"),
        },
    }

    report_path = manifest_path.parent / "APPLY_REPORT.json"
    report_md_path = manifest_path.parent / "APPLY_REPORT.md"

    write_json(report_path, report)
    write_text(report_md_path, apply_report_to_markdown(report, archive_dir))

    return {
        "report_path": str(report_path),
        "report_markdown_path": str(report_md_path),
    }


def manifest_to_markdown(manifest: Dict) -> str:
    lines = []
    lines.append("# MOVE PLAN (CAPS Keyword Archiver)")
    lines.append("")
    lines.append(f"- Created (UTC): `{manifest['created_utc']}`")
    lines.append(f"- Parent dir: `{manifest['parent_dir']}`")
    lines.append(f"- Archive dir: `{manifest['archive_dir']}`")
    lines.append(f"- Keywords: `{', '.join(manifest['keywords'])}`")
    lines.append(f"- Include extensions: `{manifest['include_exts']}`")
    lines.append(f"- Exclude dirs: `{', '.join(manifest['exclude_dirs'])}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Planned moves: **{manifest['counts']['planned_moves']}**")
    lines.append(f"- Non-matching files seen: **{manifest['counts']['non_matching_files_seen']}**")
    lines.append("")
    lines.append("## Planned Moves")
    lines.append("")
    lines.append("| # | Keywords | Source (relative) | Destination (relative to archive) | Size (bytes) | Collision |")
    lines.append("|---:|---|---|---|---:|---|")

    for i, pm in enumerate(manifest["planned_moves"], start=1):
        keys = ", ".join(pm["keywords"])
        src_rel = pm["src_rel"]
        dest_rel = pm["dest_rel"]
        size = pm["size_bytes"]
        col = pm["collision_note"]
        lines.append(f"| {i} | `{keys}` | `{src_rel}` | `{dest_rel}` | {size} | `{col}` |")

    lines.append("")
    return "\n".join(lines)


def apply_report_to_markdown(report: Dict, archive_dir: Path) -> str:
    lines = []
    lines.append("# APPLY REPORT (CAPS Keyword Archiver)")
    lines.append("")
    lines.append(f"- Applied (UTC): `{report['applied_utc']}`")
    lines.append(f"- Dry run: `{report['dry_run']}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    for k, v in report["counts"].items():
        lines.append(f"- {k}: **{v}**")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| # | Status | Keywords | Source | Destination | Error |")
    lines.append("|---:|---|---|---|---|---|")

    for i, r in enumerate(report["results"], start=1):
        keys = ", ".join(r["keywords"])
        src = r["src"]
        dest = r["dest"]
        try:
            dest_rel = str(Path(dest).relative_to(archive_dir)).replace("\\", "/")
        except Exception:
            dest_rel = dest
        err = (r["error"] or "").replace("\n", " ")
        lines.append(f"| {i} | `{r['status']}` | `{keys}` | `{src}` | `{dest_rel}` | `{err}` |")

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["plan", "apply"], required=True)
    p.add_argument("--parent", default=DEFAULT_PARENT_DIR)
    p.add_argument("--archive", default=DEFAULT_ARCHIVE_DIR)
    p.add_argument("--out", required=True, help="Output dir for MOVE_PLAN.md and manifest/report JSON")
    p.add_argument("--manifest", default=None, help="Path to MOVE_MANIFEST.json (required for apply if not in --out)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--include-exts", default=None,
                   help="Comma-separated list like .md,.pdf,.docx (optional). If omitted, all extensions allowed.")
    p.add_argument("--exclude-dirs", default=None,
                   help="Comma-separated dir names to exclude (optional).")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    parent_dir = Path(args.parent).resolve()
    archive_dir = Path(args.archive).resolve()
    out_dir = Path(args.out).resolve()

    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if args.exclude_dirs:
        for d in args.exclude_dirs.split(","):
            d = d.strip()
            if d:
                exclude_dirs.add(d)

    include_exts = None
    if args.include_exts:
        include_exts = set()
        for e in args.include_exts.split(","):
            e = e.strip().lower()
            if not e:
                continue
            if not e.startswith("."):
                e = "." + e
            include_exts.add(e)

    if args.mode == "plan":
        res = plan(parent_dir, archive_dir, out_dir, include_exts, exclude_dirs)
        print(res["markdown_path"])
        print(res["manifest_path"])
        return 0

    if args.mode == "apply":
        manifest_path = Path(args.manifest).resolve() if args.manifest else (out_dir / "MOVE_MANIFEST.json")
        if not manifest_path.exists():
            raise SystemExit(f"Manifest not found: {manifest_path}")
        res = apply(manifest_path, dry_run=args.dry_run)
        print(res["report_markdown_path"])
        print(res["report_path"])
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
