#!/usr/bin/env python3
"""
Phase A patcher for module section refactor.

Generates:
- REFERENCE_INDEX.json
- REWRITE_PATCHSET/ (manifest + per-file plans)
- registry patch (RFC-6902) + applies it
- registry_patch_report.md and hash evidence
"""

from __future__ import annotations

import argparse
import json
import fnmatch
import os
import re
import shutil
import subprocess
import tempfile
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".jsonl",
    ".ps1",
    ".csv",
}

GLOBAL_EXCLUDES = [
    "**/.git/**",
    "**/.state/**",
    "**/.state_temp/**",
    "**/.venv/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/backups/**",
    "**/BACKUP_FILES/**",
    "**/Archive_*/**",
    "**/*_Archive_Gov_Reg/**",
    "**/*Archive_Gov_Reg*/**",
    "**/*_evidence/**",
    "**/evidence/**",
    "**/EVIDENCE/**",
    "**/reports/**",
    "**/metrics/**",
    "**/.migration/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.log",
    "**/*.tmp",
    "**/*.bak",
    "**/*.zip",
    "**/*.7z",
]

FILE_ID_RE = re.compile(r"^\d{20}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def to_windows_path(path_posix: str) -> str:
    return path_posix.replace("/", "\\")


def match_globs(path_norm: str, patterns: List[str]) -> bool:
    text = path_norm.lower()
    for pattern in patterns:
        pat = pattern.lower()
        if fnmatch.fnmatch(text, pat) or (pat.startswith("**/") and fnmatch.fnmatch(text, pat[3:])):
            return True
    return False


def should_skip(rel_path: str) -> bool:
    return match_globs(rel_path, GLOBAL_EXCLUDES)


def iter_text_files(repo_root: Path) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        rel_dir = normalize_path(Path(dirpath), repo_root)
        if should_skip(rel_dir + "/"):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not should_skip(f"{rel_dir}/{d}/")]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() in TEXT_EXTENSIONS:
                try:
                    if path.stat().st_size > 2 * 1024 * 1024:
                        continue
                except OSError:
                    continue
                files.append(path)
    return files


def build_old_new_maps(move_records: List[Dict[str, Any]]) -> Tuple[Dict[str, str], Dict[str, str]]:
    old_to_new: Dict[str, str] = {}
    old_to_id: Dict[str, str] = {}
    for move in move_records:
        file_id = move.get("file_id")
        if not file_id:
            continue

        rel_win = move.get("source_relpath")
        dest_win = move.get("dest_relpath")
        if rel_win and dest_win:
            old_to_new[rel_win] = dest_win
            old_to_id[rel_win] = file_id
            rel_posix = rel_win.replace("\\", "/")
            dest_posix = dest_win.replace("\\", "/")
            old_to_new[rel_posix] = dest_posix
            old_to_id[rel_posix] = file_id

        abs_old = move.get("source_abs_path")
        abs_new = move.get("dest_abs_path")
        if abs_old and abs_new:
            old_to_new[abs_old] = abs_new
            old_to_id[abs_old] = file_id
    return old_to_new, old_to_id


def build_regex(patterns: List[str]) -> re.Pattern:
    escaped = sorted({re.escape(p) for p in patterns if p}, key=len, reverse=True)
    if not escaped:
        return re.compile(r"(?!x)x")
    joined = "|".join(escaped)
    return re.compile(joined)


def line_starts(text: str) -> List[int]:
    starts = [0]
    for idx, char in enumerate(text):
        if char == "\n":
            starts.append(idx + 1)
    return starts


def line_number_for_offset(starts: List[int], offset: int) -> int:
    return bisect_right(starts, offset)


def hash_text(text: str) -> str:
    return sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def build_registry_index(registry_path: Path, repo_root: Path) -> Dict[str, str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    index = {}
    for rec in registry.get("files") or []:
        if not isinstance(rec, dict):
            continue
        rel = rec.get("relative_path")
        if not rel:
            continue
        rel_norm = rel.replace("\\", "/")
        root_name = repo_root.name
        if rel_norm.startswith(root_name + "/"):
            rel_norm = rel_norm[len(root_name) + 1 :]
        rel_norm = rel_norm.lstrip("./")
        index[to_windows_path(rel_norm)] = rec.get("file_id", "")
        index[rel_norm] = rec.get("file_id", "")
    return index


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)


def backup_if_exists(path: Path) -> None:
    if not path.exists():
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".backup_{timestamp}")
    path.rename(backup_path)


def generate_reference_index(
    repo_root: Path,
    registry_path: Path,
    move_records: List[Dict[str, Any]],
    reference_index_path: Path,
) -> Dict[str, Any]:
    old_to_new, old_to_id = build_old_new_maps(move_records)
    patterns = [p for p in old_to_new.keys() if p]
    registry_index = build_registry_index(registry_path, repo_root)

    references = []
    unresolved = []

    rg_path = shutil.which("rg")
    if rg_path and patterns:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            for pattern in patterns:
                handle.write(pattern)
                handle.write("\n")
            pattern_path = handle.name

        include_globs = [f"*.{ext.lstrip('.')}" for ext in TEXT_EXTENSIONS]
        rg_cmd = [
            rg_path,
            "--fixed-strings",
            "--json",
            "--hidden",
            "--max-filesize",
            "2M",
            "-f",
            pattern_path,
        ]
        for glob in include_globs:
            rg_cmd += ["-g", glob]
        for glob in GLOBAL_EXCLUDES:
            rg_cmd += ["-g", f"!{glob}"]
        rg_cmd.append(".")

        proc = subprocess.run(
            rg_cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr.strip())

        for line in (proc.stdout or "").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") != "match":
                continue
            data = event.get("data", {})
            path_text = data.get("path", {}).get("text")
            if not path_text:
                continue
            rel_posix = Path(path_text).as_posix()
            rel_win = to_windows_path(rel_posix)
            file_id = registry_index.get(rel_win) or registry_index.get(rel_posix)
            line_no = data.get("line_number")
            line_text = data.get("lines", {}).get("text", "")
            for sub in data.get("submatches", []):
                matched_text = sub.get("match", {}).get("text")
                if not matched_text:
                    continue
                new_value = old_to_new.get(matched_text)
                if not new_value:
                    unresolved.append(
                        {
                            "source_file": rel_win,
                            "matched_text": matched_text,
                            "reason": "NO_TARGET_MAPPING",
                        }
                    )
                    continue
                ref_id_seed = f"{rel_win}|{line_no}|{matched_text}|{new_value}"
                ref_id = sha256(ref_id_seed.encode("utf-8")).hexdigest()
                references.append(
                    {
                        "ref_id": ref_id,
                        "source_file_id": file_id,
                        "source_relpath": rel_win,
                        "ref_type": "PATH_STRING",
                        "old_value": matched_text,
                        "new_value": new_value,
                        "location": f"line:{line_no}",
                        "rewrite_plan_id": None,
                        "confidence": 1.0,
                        "evidence": hash_text(line_text),
                        "target_file_id": old_to_id.get(matched_text),
                    }
                )
        os.unlink(pattern_path)
    elif patterns:
        matcher = build_regex(patterns)
        text_files = iter_text_files(repo_root)
        for path in text_files:
            rel_posix = normalize_path(path, repo_root)
            rel_win = to_windows_path(rel_posix)
            file_id = registry_index.get(rel_win) or registry_index.get(rel_posix)
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            starts = line_starts(content)

            for match in matcher.finditer(content):
                matched_text = match.group(0)
                new_value = old_to_new.get(matched_text)
                if not new_value:
                    unresolved.append(
                        {
                            "source_file": rel_win,
                            "matched_text": matched_text,
                            "reason": "NO_TARGET_MAPPING",
                        }
                    )
                    continue
                line_no = line_number_for_offset(starts, match.start())
                line_start = starts[line_no - 1]
                line_end = content.find("\n", line_start)
                if line_end == -1:
                    line_end = len(content)
                line_text = content[line_start:line_end]
                ref_id_seed = f"{rel_win}|{line_no}|{matched_text}|{new_value}"
                ref_id = sha256(ref_id_seed.encode("utf-8")).hexdigest()
                references.append(
                    {
                        "ref_id": ref_id,
                        "source_file_id": file_id,
                        "source_relpath": rel_win,
                        "ref_type": "PATH_STRING",
                        "old_value": matched_text,
                        "new_value": new_value,
                        "location": f"line:{line_no}",
                        "rewrite_plan_id": None,
                        "confidence": 1.0,
                        "evidence": hash_text(line_text),
                        "target_file_id": old_to_id.get(matched_text),
                    }
                )

    references.sort(key=lambda r: (r["source_relpath"] or "", r["location"]))

    reference_index = {
        "version": "1.0.0",
        "generated_utc": utc_now(),
        "references": references,
        "unresolved": unresolved,
    }
    backup_if_exists(reference_index_path)
    write_json(reference_index_path, reference_index)
    return reference_index


def generate_rewrite_patchset(
    repo_root: Path,
    reference_index: Dict[str, Any],
    rewrite_root: Path,
    evidence_dir: Path,
) -> Dict[str, Any]:
    plans_dir = rewrite_root / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    refs_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ref in reference_index.get("references", []):
        refs_by_file[ref["source_relpath"]].append(ref)

    plan_manifest = {
        "version": "1.0.0",
        "generated_utc": utc_now(),
        "plan_count": 0,
        "plans": [],
    }

    for source_rel, refs in sorted(refs_by_file.items()):
        source_path = repo_root / source_rel
        if not source_path.exists():
            continue
        plan_id = sha256(source_rel.encode("utf-8")).hexdigest()[:16]
        pre_hash = sha256(source_path.read_bytes()).hexdigest()
        operations = []
        for ref in refs:
            ref["rewrite_plan_id"] = plan_id
            operations.append(
                {
                    "ref_id": ref["ref_id"],
                    "old_value": ref["old_value"],
                    "new_value": ref["new_value"],
                    "location": ref["location"],
                }
            )

        plan = {
            "rewrite_plan_id": plan_id,
            "target_file_id": refs[0].get("source_file_id"),
            "target_relpath": source_rel,
            "strategy": "TEXT_REPLACE_SET",
            "pre_hash_sha256": pre_hash,
            "operations": operations,
            "dry_run_output_path": str(
                evidence_dir / "diffs" / "rewrite_diffs" / f"{plan_id}.diff"
            ),
        }
        write_json(plans_dir / f"{plan_id}.json", plan)
        plan_manifest["plans"].append(plan_id)

    plan_manifest["plan_count"] = len(plan_manifest["plans"])
    write_json(rewrite_root / "manifest.json", plan_manifest)
    return plan_manifest


def apply_registry_patch(
    registry_path: Path,
    move_records: List[Dict[str, Any]],
    evidence_dir: Path,
    baseline_path: Optional[Path] = None,
    apply_changes: bool = True,
) -> Dict[str, Any]:
    registry_source = baseline_path or registry_path
    registry = json.loads(registry_source.read_text(encoding="utf-8"))
    before_hash = sha256(json.dumps(registry, sort_keys=True).encode("utf-8")).hexdigest()

    column_headers = registry.get("column_headers") or {}
    patch_ops = []
    if "module_id" not in column_headers:
        patch_ops.append(
            {
                "op": "add",
                "path": "/column_headers/module_id",
                "value": "Dir ID of module root folder (section assignment)",
            }
        )
        column_headers["module_id"] = "Dir ID of module root folder (section assignment)"
        registry["column_headers"] = column_headers

    file_id_to_module = {
        move["file_id"]: move.get("dest_dir_id")
        for move in move_records
        if move.get("file_id") and move.get("dest_dir_id")
    }

    updated = 0
    for idx, rec in enumerate(registry.get("files") or []):
        if not isinstance(rec, dict):
            continue
        file_id = rec.get("file_id")
        if file_id not in file_id_to_module:
            continue
        desired = file_id_to_module[file_id]
        if not desired:
            continue
        current = rec.get("module_id")
        if current == desired:
            continue
        op = "replace" if "module_id" in rec else "add"
        patch_ops.append({"op": op, "path": f"/files/{idx}/module_id", "value": desired})
        rec["module_id"] = desired
        updated += 1

    after_hash = sha256(json.dumps(registry, sort_keys=True).encode("utf-8")).hexdigest()

    if apply_changes:
        backup_if_exists(registry_path)
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    diffs_dir = evidence_dir / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    patch_path = diffs_dir / "registry.patch.rfc6902.json"
    write_json(patch_path, patch_ops)

    hash_report = {
        "before_hash": before_hash,
        "after_hash": after_hash,
        "updated_records": updated,
        "patch_ops": len(patch_ops),
        "baseline": str(registry_source),
        "applied": apply_changes,
    }
    write_json(evidence_dir / "reports" / "before_after_hashes.json", hash_report)
    return hash_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase A patcher")
    parser.add_argument("--move-map", default="MOVE_MAP.json")
    parser.add_argument("--registry", default="01999000042260124503_governance_registry_unified.json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--reference-index", default="REFERENCE_INDEX.json")
    parser.add_argument("--rewrite-dir", default="REWRITE_PATCHSET")
    parser.add_argument("--evidence-dir", default="EVIDENCE_BUNDLE")
    parser.add_argument("--baseline", default=None, help="Baseline registry for evidence-only patch generation")
    parser.add_argument("--no-apply", action="store_true", help="Do not modify registry; only write evidence")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    move_map = json.loads((repo_root / args.move_map).read_text(encoding="utf-8"))
    move_records = move_map.get("moves", [])

    evidence_root = repo_root / args.evidence_dir
    reports_dir = evidence_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    reference_index_path = repo_root / args.reference_index
    reference_index = generate_reference_index(
        repo_root=repo_root,
        registry_path=repo_root / args.registry,
        move_records=move_records,
        reference_index_path=reference_index_path,
    )

    rewrite_manifest = generate_rewrite_patchset(
        repo_root=repo_root,
        reference_index=reference_index,
        rewrite_root=repo_root / args.rewrite_dir,
        evidence_dir=evidence_root,
    )
    # rewrite_plan_id values are injected during patchset creation
    write_json(reference_index_path, reference_index)

    baseline_path = Path(args.baseline) if args.baseline else None
    hash_report = apply_registry_patch(
        registry_path=repo_root / args.registry,
        move_records=move_records,
        evidence_dir=evidence_root,
        baseline_path=baseline_path,
        apply_changes=not args.no_apply,
    )

    report_lines = [
        "# Registry Patch Report",
        "",
        f"Generated UTC: {utc_now()}",
        f"Patch operations: {hash_report['patch_ops']}",
        f"Updated records: {hash_report['updated_records']}",
        f"Before hash: {hash_report['before_hash']}",
        f"After hash: {hash_report['after_hash']}",
        "",
        "## Reference Index",
        f"- references: {len(reference_index.get('references', []))}",
        f"- unresolved: {len(reference_index.get('unresolved', []))}",
        "",
        "## Rewrite Patchset",
        f"- plan_count: {rewrite_manifest.get('plan_count')}",
    ]
    (reports_dir / "registry_patch_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    rewrite_report = [
        "# Rewrite Plan Report",
        "",
        f"Generated UTC: {utc_now()}",
        f"Plans: {rewrite_manifest.get('plan_count')}",
    ]
    (reports_dir / "rewrite_plan_report.md").write_text("\n".join(rewrite_report), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
