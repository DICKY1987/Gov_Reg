#!/usr/bin/env python3
"""
Phase A planner for module section refactor.

Generates:
- classification rules (evidence)
- classification report (evidence)
- MOVE_MAP.json (move_enabled false)
- MOVE_MAP_APPROVAL.json (optional, move_enabled reflects eligibility)
- HUMAN_MOVE_REVIEW.md (evidence)
- move_plan_report.md (evidence)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RULES: Dict[str, Any] = {
    "version": "1.0.0",
    "classifier_id": "module_section_classifier_v1",
    "default_outcome": "UNCLASSIFIED",
    "outcomes": [
        "REGISTRY_FILES",
        "ID_FILES",
        "TEMPLATE_OPERATIONS",
        "MULTI_CLI_PLANNING",
        "AMBIGUOUS",
        "UNCLASSIFIED",
        "EXCLUDED",
    ],
    "normalization": {
        "path_separator": "/",
        "case_sensitive": False,
        "trim_prefixes": ["./", ".\\"],
    },
    "global_excludes": {
        "path_globs": [
            "**/.git/**",
            "**/.state/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.log",
            "**/*.tmp",
            "**/*.bak",
            "**/*.zip",
            "**/*.7z",
        ]
    },
    "rules": [
        {
            "rule_id": "REG-001",
            "priority": 1,
            "section": "REGISTRY_FILES",
            "match_any": {
                "path_globs": ["**/REGISTRY/**", "**/*REGISTRY*/**"],
                "name_regex": [r"(?i)^.*registry.*\.(json|yaml|yml|jsonl|csv|md)$"],
                "content_regex": [r"\"column_headers\"\s*:", r"\"files\"\s*:\s*\["],
            },
            "exclude_any": {
                "name_regex": [r"(?i)counter_store", r"(?i)id_canonicality", r"(?i)id_patterns"]
            },
        },
        {
            "rule_id": "ID-001",
            "priority": 2,
            "section": "ID_FILES",
            "match_any": {
                "path_globs": [
                    "**/ID/**",
                    "**/*ID*/**",
                    "**/identity/**",
                    "**/allocat*/**",
                    "**/validators/**id*/**",
                ],
                "name_regex": [
                    r"(?i)^P_\d{20}_.*\.py$",
                    r"(?i)^.*(id_allocator|allocate_.*id|id_assign|add_ids|sync_registry_.*|verify_system)\.py$",
                    r"(?i)^.*(ID_CANONICALITY|ID_PATTERNS|COUNTER_STORE).*\.(json|yaml|yml)$",
                    r"(?i)^.*(dir_id|file_id|doc_id).*\.(md|json|yaml|yml|py)$",
                ],
                "content_regex": [
                    r"(?i)\bfile_id\b",
                    r"(?i)\bdir_id\b",
                    r"(?i)\bdoc_id\b",
                    r"(?i)\bCOUNTER_STORE\b",
                    r"(?i)\bCOUNTER_MAX\b",
                    r"(?i)\b\^\d\{20\}\$\b",
                ],
            },
        },
        {
            "rule_id": "TPL-001",
            "priority": 3,
            "section": "TEMPLATE_OPERATIONS",
            "match_any": {
                "path_globs": [
                    "**/templates/**",
                    "**/*template*/**",
                    "**/PATCHES/**",
                    "**/*patch*/**",
                    "**/template_ops/**",
                ],
                "name_regex": [
                    r"(?i)^.*(TEMPLATE|AUTONOMOUS_DELIVERY_TEMPLATE|TEMPLATE_V\d+).*\.(json|yaml|yml|md)$",
                    r"(?i)^.*\.patch\.json$",
                    r"(?i)^.*rfc-?6902.*\.json$",
                    r"(?i)^.*(apply_patch|patch_apply|template_expand|template_render|template_validate).*\.([Pp][Yy]|ps1)$",
                ],
                "content_regex": [
                    r"(?i)RFC-?6902",
                    r"(?i)\"op\"\s*:\s*\"(add|remove|replace|move|copy|test)\"",
                    r"(?i)\"path\"\s*:\s*\"/",
                ],
            },
        },
        {
            "rule_id": "MCP-001",
            "priority": 4,
            "section": "MULTI_CLI_PLANNING",
            "match_any": {
                "path_globs": [
                    "**/LP_LONG_PLAN/**",
                    "**/LONG_PLAN/**",
                    "**/MASTER_SPLINTER/**",
                    "**/newPhasePlanProcess/**",
                    "**/phase*/**",
                    "**/sections/**",
                    "**/plans/**",
                ],
                "name_regex": [
                    r"(?i)^\d{20}_PH-\d{3}.*\.(json|md|yaml|yml)$",
                    r"(?i)^.*(phase_contract|phase_plan|execution_plan|plan_process|plan_cli|wiring|orchestrator).*\.(json|md|py|yaml|yml)$",
                    r"(?i)^sec_\d{3}.*\.(json|md|yaml|yml)$",
                ],
                "content_regex": [
                    r"(?i)\"phase\"\s*:",
                    r"(?i)\"tasks\"\s*:",
                    r"(?i)\"artifacts\"\s*:",
                    r"(?i)\"validations\"\s*:",
                    r"(?i)langgraph",
                    r"(?i)langchain",
                    r"(?i)multi-?cli",
                    r"(?i)conversion",
                    r"(?i)bridge",
                    r"(?i)envelope_contract",
                ],
            },
        },
    ],
    "tie_break": {"enabled": False, "strategy": "FAIL_CLOSED"},
    "precedence": [
        "REGISTRY_FILES",
        "ID_FILES",
        "TEMPLATE_OPERATIONS",
        "MULTI_CLI_PLANNING",
    ],
    "ambiguity_rules": [
        "REGISTRY_PATH_AND_ID_FILENAME",
        "MCP_AND_TEMPLATE_PATH_OR_NAME",
        "ID_CONTENT_ONLY_WITH_OTHER_PATH_OR_NAME",
    ],
}

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

FILE_ID_RE = re.compile(r"^\d{20}$")
DIR_ID_RE = re.compile(r"^\d{20}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_registry_path(raw_path: Optional[str], repo_root: Path) -> Optional[str]:
    if not raw_path:
        return None
    path_text = raw_path.replace("\\", "/").strip()
    if re.match(r"^[A-Za-z]:/", path_text):
        try:
            return Path(path_text).resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return None
    root_name = repo_root.name
    if path_text.startswith(root_name + "/"):
        path_text = path_text[len(root_name) + 1 :]
    for prefix in RULES["normalization"]["trim_prefixes"]:
        if path_text.startswith(prefix.replace("\\", "/")):
            path_text = path_text[len(prefix) :]
    return path_text.lstrip("/")


def to_windows_path(path_posix: Optional[str]) -> Optional[str]:
    if path_posix is None:
        return None
    return path_posix.replace("/", "\\")


def load_text(path: Path, max_bytes: int) -> Optional[str]:
    if not path.exists():
        return None
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(max_bytes)
    except OSError:
        return None


def match_globs(path_norm: str, patterns: List[str], case_sensitive: bool) -> List[str]:
    if not patterns:
        return []
    text = path_norm if case_sensitive else path_norm.lower()
    matched = []
    for pattern in patterns:
        pat = pattern if case_sensitive else pattern.lower()
        if fnmatch.fnmatch(text, pat) or (pat.startswith("**/") and fnmatch.fnmatch(text, pat[3:])):
            matched.append(pattern)
    return matched


def match_regex(text: str, patterns: List[re.Pattern]) -> List[str]:
    matched = []
    for pattern in patterns:
        if pattern.search(text):
            matched.append(pattern.pattern)
    return matched


def load_dir_id(dir_path: Path) -> Optional[str]:
    dir_id_path = dir_path / ".dir_id"
    if not dir_id_path.exists():
        return None
    try:
        data = json.loads(dir_id_path.read_text(encoding="utf-8"))
        dir_id = data.get("dir_id")
        return dir_id if isinstance(dir_id, str) else None
    except (OSError, json.JSONDecodeError):
        return None


def parse_dir_id_from_name(name: str) -> Optional[str]:
    match = re.match(r"^(\d{20})_", name)
    if not match:
        return None
    return match.group(1)


def build_dest_roots(repo_root: Path) -> Dict[str, Dict[str, str]]:
    roots = {
        "REGISTRY_FILES": repo_root / "01260207201000001250_REGISTRY",
        "ID_FILES": repo_root / "01260207201000001162_GEU" / "01260207201000001165_ID",
        "MULTI_CLI_PLANNING": repo_root / "01260207201000001221_Multi CLI",
        "TEMPLATE_OPERATIONS": repo_root / "newPhasePlanProcess",
    }
    resolved = {}
    for key, path in roots.items():
        dir_id = load_dir_id(path) or parse_dir_id_from_name(path.name)
        resolved[key] = {
            "abs_path": str(path.resolve()),
            "rel_path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
            "dir_id": dir_id or "",
        }
    return resolved


def classify_record(
    file_record: Dict[str, Any],
    repo_root: Path,
    compiled_rules: List[Dict[str, Any]],
    compiled_excludes: List[str],
    max_content_bytes: int,
) -> Dict[str, Any]:
    raw_rel = file_record.get("relative_path")
    file_id = str(file_record.get("file_id") or "")
    normalized = normalize_registry_path(raw_rel, repo_root)
    filename = Path(normalized).name if normalized else ""
    exists_on_disk = False
    abs_path = None
    if normalized:
        abs_path = (repo_root / normalized).resolve()
        exists_on_disk = abs_path.exists()

    case_sensitive = RULES["normalization"]["case_sensitive"]
    path_norm = normalized or ""
    path_matches_exclude = match_globs(path_norm, compiled_excludes, case_sensitive)
    if path_matches_exclude:
        return {
            "file_id": file_id,
            "relative_path_raw": raw_rel,
            "relative_path_normalized": normalized,
            "filename": filename,
            "exists_on_disk": exists_on_disk,
            "classification": "EXCLUDED",
            "match_rule_id": None,
            "match_basis": None,
            "match_signals": [],
            "ambiguous_reasons": [],
            "excluded_by": path_matches_exclude,
            "abs_path": str(abs_path) if abs_path else None,
        }

    content = load_text(abs_path, max_content_bytes) if abs_path else None

    rule_matches: List[Dict[str, Any]] = []
    for rule in compiled_rules:
        exclude = rule.get("exclude_any", {})
        excluded_by = []
        if filename and exclude.get("name_regex"):
            excluded_by = match_regex(filename, exclude["name_regex"])
        if excluded_by:
            continue

        match_any = rule.get("match_any", {})
        path_hits = match_globs(path_norm, match_any.get("path_globs", []), case_sensitive)
        name_hits = match_regex(filename, match_any.get("name_regex", [])) if filename else []
        content_hits = match_regex(content, match_any.get("content_regex", [])) if content else []

        if path_hits or name_hits or content_hits:
            bases = []
            if path_hits:
                bases.append("path")
            if name_hits:
                bases.append("name")
            if content_hits:
                bases.append("content")
            signals = [f"path:{pat}" for pat in path_hits]
            signals += [f"name:{pat}" for pat in name_hits]
            signals += [f"content:{pat}" for pat in content_hits]
            rule_matches.append(
                {
                    "rule_id": rule["rule_id"],
                    "section": rule["section"],
                    "priority": rule["priority"],
                    "bases": bases,
                    "signals": signals,
                    "path_hits": path_hits,
                    "name_hits": name_hits,
                    "content_hits": content_hits,
                }
            )

    if not rule_matches:
        return {
            "file_id": file_id,
            "relative_path_raw": raw_rel,
            "relative_path_normalized": normalized,
            "filename": filename,
            "exists_on_disk": exists_on_disk,
            "classification": "UNCLASSIFIED",
            "match_rule_id": None,
            "match_basis": None,
            "match_signals": [],
            "ambiguous_reasons": [],
            "abs_path": str(abs_path) if abs_path else None,
        }

    ambiguous_reasons = detect_ambiguity(rule_matches)
    if ambiguous_reasons:
        return {
            "file_id": file_id,
            "relative_path_raw": raw_rel,
            "relative_path_normalized": normalized,
            "filename": filename,
            "exists_on_disk": exists_on_disk,
            "classification": "AMBIGUOUS",
            "match_rule_id": None,
            "match_basis": None,
            "match_signals": [],
            "ambiguous_reasons": ambiguous_reasons,
            "abs_path": str(abs_path) if abs_path else None,
        }

    chosen = sorted(rule_matches, key=lambda r: r["priority"])[0]
    match_basis = "content"
    if "path" in chosen["bases"]:
        match_basis = "path"
    elif "name" in chosen["bases"]:
        match_basis = "name"

    return {
        "file_id": file_id,
        "relative_path_raw": raw_rel,
        "relative_path_normalized": normalized,
        "filename": filename,
        "exists_on_disk": exists_on_disk,
        "classification": chosen["section"],
        "match_rule_id": chosen["rule_id"],
        "match_basis": match_basis,
        "match_signals": chosen["signals"],
        "ambiguous_reasons": [],
        "abs_path": str(abs_path) if abs_path else None,
    }


def detect_ambiguity(rule_matches: List[Dict[str, Any]]) -> List[str]:
    sections = {match["section"]: match for match in rule_matches}
    reasons = []

    reg_match = sections.get("REGISTRY_FILES")
    id_match = sections.get("ID_FILES")
    tpl_match = sections.get("TEMPLATE_OPERATIONS")
    mcp_match = sections.get("MULTI_CLI_PLANNING")

    if reg_match and id_match:
        reg_path = reg_match["path_hits"]
        id_name = [sig for sig in id_match["signals"] if sig.startswith("name:")]
        if reg_path and id_name:
            reasons.append("REGISTRY_PATH_AND_ID_FILENAME")

    if mcp_match and tpl_match:
        mcp_path_or_name = mcp_match["path_hits"] or mcp_match["name_hits"]
        tpl_path_or_name = tpl_match["path_hits"] or tpl_match["name_hits"]
        if mcp_path_or_name and tpl_path_or_name:
            reasons.append("MCP_AND_TEMPLATE_PATH_OR_NAME")

    if id_match:
        id_bases = set(id_match["bases"])
        if id_bases == {"content"}:
            other_path_name = False
            for match in rule_matches:
                if match["section"] == "ID_FILES":
                    continue
                if match["path_hits"] or match["name_hits"]:
                    other_path_name = True
                    break
            if other_path_name:
                reasons.append("ID_CONTENT_ONLY_WITH_OTHER_PATH_OR_NAME")

    return reasons


def build_move_record(
    classification: Dict[str, Any],
    dest_roots: Dict[str, Dict[str, str]],
    repo_root: Path,
) -> Dict[str, Any]:
    section = classification["classification"]
    source_rel = classification["relative_path_normalized"]
    source_abs = classification["abs_path"]
    dest_root = dest_roots[section]
    dest_root_rel = dest_root["rel_path"]

    source_rel_norm = source_rel or ""
    dest_rel = source_rel_norm
    if source_rel_norm and not source_rel_norm.lower().startswith(dest_root_rel.lower() + "/"):
        dest_rel = f"{dest_root_rel}/{source_rel_norm}"

    dest_abs = str((repo_root / dest_rel).resolve()) if dest_rel else None

    source_dir_id = None
    if source_rel_norm:
        parent_dir = (repo_root / source_rel_norm).resolve().parent
        source_dir_id = load_dir_id(parent_dir) or parse_dir_id_from_name(parent_dir.name)

    record = {
        "file_id": classification["file_id"],
        "entity_type": "file",
        "category": section,
        "source_relpath": to_windows_path(source_rel_norm),
        "dest_dir_id": dest_root.get("dir_id"),
        "dest_dir_relpath": to_windows_path(dest_root_rel),
        "dest_relpath": to_windows_path(dest_rel),
        "match_rule_id": classification["match_rule_id"],
        "match_basis": classification["match_basis"],
        "match_signals": classification["match_signals"],
        "confidence": "HIGH" if classification["match_basis"] in {"path", "name"} else "MED",
        "move_enabled": False,
        "eligible": False,
        "eligibility_issues": [],
        "source_dir_id": source_dir_id,
        "source_abs_path": source_abs,
        "dest_root_abs_path": dest_root.get("abs_path"),
        "dest_abs_path": dest_abs,
    }
    return record


def evaluate_eligibility(
    record: Dict[str, Any], classification: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    issues = []
    file_id = record.get("file_id")
    if not file_id or not FILE_ID_RE.match(file_id):
        issues.append("SKIPPED_NO_ID")

    if not classification.get("exists_on_disk"):
        issues.append("MISSING_SOURCE")

    if not classification.get("relative_path_normalized"):
        issues.append("MISSING_RELATIVE_PATH")

    dest_dir_id = record.get("dest_dir_id") or ""
    if dest_dir_id and not DIR_ID_RE.match(dest_dir_id):
        issues.append("INVALID_DEST_DIR_ID")

    source_abs = record.get("source_abs_path")
    dest_abs = record.get("dest_abs_path")
    if dest_abs and source_abs and dest_abs != source_abs and Path(dest_abs).exists():
        issues.append("DESTINATION_COLLISION")

    eligible = not issues
    return eligible, issues


def backup_if_exists(path: Path) -> None:
    if not path.exists():
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".backup_{timestamp}")
    path.rename(backup_path)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase A module section planner")
    parser.add_argument("--registry", default="01999000042260124503_governance_registry_unified.json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--evidence-dir", default="EVIDENCE_BUNDLE")
    parser.add_argument("--move-map", default="MOVE_MAP.json")
    parser.add_argument("--move-map-approval", default="MOVE_MAP_APPROVAL.json")
    parser.add_argument("--max-content-bytes", type=int, default=200000)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    registry_path = repo_root / args.registry
    evidence_root = repo_root / args.evidence_dir
    reports_dir = evidence_root / "reports"

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    file_records = registry.get("files") or []

    compiled_rules = []
    for rule in RULES["rules"]:
        compiled_rules.append(
            {
                "rule_id": rule["rule_id"],
                "priority": rule["priority"],
                "section": rule["section"],
                "match_any": {
                    "path_globs": rule["match_any"].get("path_globs", []),
                    "name_regex": [re.compile(p) for p in rule["match_any"].get("name_regex", [])],
                    "content_regex": [re.compile(p) for p in rule["match_any"].get("content_regex", [])],
                },
                "exclude_any": {
                    "name_regex": [re.compile(p) for p in rule.get("exclude_any", {}).get("name_regex", [])]
                },
            }
        )

    compiled_excludes = RULES["global_excludes"]["path_globs"]
    dest_roots = build_dest_roots(repo_root)

    classification_results = []
    move_records = []
    counts_by_category: Dict[str, int] = {}
    skipped_ambiguous = 0
    skipped_unclassified = 0
    skipped_excluded = 0

    for record in sorted(file_records, key=lambda r: str(r.get("file_id", ""))):
        if not isinstance(record, dict):
            continue
        classification = classify_record(
            record,
            repo_root,
            compiled_rules,
            compiled_excludes,
            args.max_content_bytes,
        )
        classification_results.append(classification)

        section = classification["classification"]
        if section == "AMBIGUOUS":
            skipped_ambiguous += 1
            continue
        if section == "UNCLASSIFIED":
            skipped_unclassified += 1
            continue
        if section == "EXCLUDED":
            skipped_excluded += 1
            continue
        if section not in dest_roots:
            continue

        counts_by_category[section] = counts_by_category.get(section, 0) + 1
        move_record = build_move_record(classification, dest_roots, repo_root)
        eligible, issues = evaluate_eligibility(move_record, classification)
        move_record["eligible"] = eligible
        move_record["eligibility_issues"] = issues
        move_records.append(move_record)

    move_records.sort(key=lambda r: (r["file_id"], r["source_relpath"] or ""))

    run_id = f"phaseA_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    backup_if_exists(Path(args.move_map))
    backup_if_exists(reports_dir / "HUMAN_MOVE_REVIEW.md")
    backup_if_exists(reports_dir / "move_plan_report.md")

    move_map = {
        "schema_version": "1.0.0",
        "generated_utc": utc_now(),
        "run_id": run_id,
        "repo_root": str(repo_root),
        "constraints": {
            "no_overwrites": True,
            "preserve_extension": True,
            "allow_collisions": False,
        },
        "scope": {
            "include_sections": list(dest_roots.keys()),
            "exclude_globs": RULES["global_excludes"]["path_globs"],
        },
        "dir_id_resolution": dest_roots,
        "counts_by_category": counts_by_category,
        "moves": move_records,
    }

    write_json(Path(args.move_map), move_map)

    move_map_approval = {
        **move_map,
        "moves": [
            {**move, "move_enabled": bool(move.get("eligible"))} for move in move_records
        ],
    }
    write_json(Path(args.move_map_approval), move_map_approval)

    classification_report = {
        "generated_utc": utc_now(),
        "run_id": run_id,
        "rules": RULES,
        "summary": {
            "total_records": len(file_records),
            "ambiguous": skipped_ambiguous,
            "unclassified": skipped_unclassified,
            "excluded": skipped_excluded,
            "candidates": len(move_records),
        },
        "records": classification_results,
    }
    write_json(reports_dir / "classification_report.json", classification_report)
    write_json(reports_dir / "classification_rules.json", RULES)

    # Build HUMAN_MOVE_REVIEW.md
    total_candidates = len(move_records)
    total_eligible = sum(1 for r in move_records if r.get("eligible"))
    skipped_no_id = sum(1 for r in move_records if "SKIPPED_NO_ID" in r.get("eligibility_issues", []))
    skipped_collision = sum(
        1 for r in move_records if "DESTINATION_COLLISION" in r.get("eligibility_issues", [])
    )
    skipped_missing = sum(1 for r in move_records if "MISSING_SOURCE" in r.get("eligibility_issues", []))

    review_lines = [
        "# HUMAN MOVE REVIEW",
        "",
        "## Summary Totals",
        f"- total candidates: {total_candidates}",
        f"- total eligible: {total_eligible}",
        f"- skipped (no file_id): {skipped_no_id}",
        f"- skipped (ambiguous category): {skipped_ambiguous}",
        f"- skipped (destination collision): {skipped_collision}",
        f"- skipped (missing source): {skipped_missing}",
        "",
        "## Move Records",
        "| file_id | category | current_absolute_path | current_relative_path | destination_root_absolute_path | destination_absolute_path | destination_relative_path | source_dir_id | dest_dir_id | move_enabled |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    def esc(value: Optional[str]) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|")

    for move in move_records:
        review_lines.append(
            "| {file_id} | {category} | {current_abs} | {current_rel} | {dest_root_abs} | {dest_abs} | {dest_rel} | {source_dir_id} | {dest_dir_id} | {move_enabled} |".format(
                file_id=esc(move.get("file_id")),
                category=esc(move.get("category")),
                current_abs=esc(move.get("source_abs_path")),
                current_rel=esc(move.get("source_relpath")),
                dest_root_abs=esc(move.get("dest_root_abs_path")),
                dest_abs=esc(move.get("dest_abs_path")),
                dest_rel=esc(move.get("dest_relpath")),
                source_dir_id=esc(move.get("source_dir_id")),
                dest_dir_id=esc(move.get("dest_dir_id")),
                move_enabled="true" if move.get("eligible") else "false",
            )
        )

    (reports_dir / "HUMAN_MOVE_REVIEW.md").parent.mkdir(parents=True, exist_ok=True)
    (reports_dir / "HUMAN_MOVE_REVIEW.md").write_text("\n".join(review_lines), encoding="utf-8")

    # Move plan report
    plan_lines = [
        "# Move Plan Report",
        "",
        f"Run ID: {run_id}",
        f"Generated UTC: {utc_now()}",
        "",
        "## Destination Roots",
    ]
    for section, info in dest_roots.items():
        plan_lines.append(f"- {section}: {info['rel_path']} (dir_id={info.get('dir_id')})")

    plan_lines += [
        "",
        "## Mapping Rule",
        "- If a file is already under its destination root, destination_relpath == source_relpath.",
        "- Otherwise, destination_relpath = <dest_root_relpath>/<source_relpath> (full re-root).",
        "",
        "## Counts",
        f"- candidates: {total_candidates}",
        f"- eligible: {total_eligible}",
        f"- ambiguous skipped: {skipped_ambiguous}",
        f"- unclassified skipped: {skipped_unclassified}",
        f"- excluded skipped: {skipped_excluded}",
        f"- missing source skipped: {skipped_missing}",
        f"- destination collision skipped: {skipped_collision}",
    ]

    (reports_dir / "move_plan_report.md").write_text("\n".join(plan_lines), encoding="utf-8")

    run_manifest = {
        "run_id": run_id,
        "generated_utc": utc_now(),
        "tool": Path(__file__).name,
        "registry": str(registry_path),
        "move_map": str(Path(args.move_map).resolve()),
        "evidence_dir": str(evidence_root),
        "content_hash": sha256(json.dumps(RULES, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    write_json(evidence_root / "run_manifest.json", run_manifest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
