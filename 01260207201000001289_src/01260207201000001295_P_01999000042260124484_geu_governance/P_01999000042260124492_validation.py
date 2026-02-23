"""GEU governance validation engine.

FILE_ID: 0199900004226012492
DOC_ID: DOC-CORE-GEU-GOVERNANCE-VALIDATION-0199900004226012492
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from jsonschema import Draft202012Validator

from .P_01999000042260124487_constants import (
    ENTRIES_DIR,
    FILE_REGISTRY_PATH,
    GEU_ENTRY_SCHEMA_PATH,
    ROLE_SLOTS_SSOT_PATH,
    SLOT_MATRIX_SSOT_PATH,
)
from .P_01999000042260124490_io_utils import read_json, file_id_index_from_registry

JSON = Dict[str, Any]

# Stable rule IDs / error codes

R_UNIQUE_GEU_ID = "GEUVAL-R001"
R_FILENAME_MATCH = "GEUVAL-R002"
R_SCHEMA_VALID = "GEUVAL-R003"
R_REF_FILE_EXISTS = "GEUVAL-R004"
R_NO_DUP_MEMBER_FILE = "GEUVAL-R005"
R_SLOT_MATRIX = "GEUVAL-R006"
R_SHARED_OWNERSHIP = "GEUVAL-R007"
R_NO_ORPHAN_CRITICAL = "GEUVAL-R008"
R_DEPENDENCIES = "GEUVAL-R009"

CRITICAL_LAYERS = {"VALIDATION", "GATES"}  # governance-critical
CRITICAL_ARTIFACT_KINDS = {"SCHEMA"}       # governance-critical

@dataclasses.dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str  # "ERROR" | "WARN"
    message: str
    geu_id: Optional[str] = None
    file_id: Optional[str] = None
    entry_path: Optional[str] = None
    remediation: Optional[str] = None

def _load_entry_schema() -> JSON:
    return read_json(GEU_ENTRY_SCHEMA_PATH)

def _load_role_slots() -> List[str]:
    return read_json(ROLE_SLOTS_SSOT_PATH)

def _load_slot_matrix() -> JSON:
    return read_json(SLOT_MATRIX_SSOT_PATH)

def _entry_file_path(entry: JSON) -> Optional[str]:
    return entry.get("__file_path__")

def _role_coverage(entry: JSON) -> Set[str]:
    roles: Set[str] = set()
    roles.add(entry["anchor_role_slot"])
    for m in entry.get("members", []):
        roles.add(m["role_slot"])
    for o in entry.get("outputs", []):
        roles.add(o["output_kind"])
    for _t in entry.get("tests", []):
        roles.add("TEST")
    return roles

def all_memberships(entries: List[JSON]) -> List[Tuple[str, str, str, str]]:
    """Return (file_id, geu_id, role, shared_access) for every membership."""
    out: List[Tuple[str, str, str, str]] = []
    for e in entries:
        gid = e["geu_id"]
        out.append((e["anchor_file_id"], gid, e["anchor_role_slot"], e["anchor_shared_access"]))
        for m in e.get("members", []):
            out.append((m["file_id"], gid, m["role_slot"], m.get("shared_access", "NONE")))
        for o in e.get("outputs", []):
            out.append((o["file_id"], gid, o["output_kind"], o.get("shared_access", "NONE")))
        for t in e.get("tests", []):
            out.append((t["file_id"], gid, "TEST", t.get("shared_access", "NONE")))
    return out

def validate_geu_entries(
    *,
    entries_dir: Path = ENTRIES_DIR,
    file_registry_path: Path = FILE_REGISTRY_PATH,
) -> Tuple[List[JSON], List[Finding]]:
    findings: List[Finding] = []

    schema = _load_entry_schema()
    validator = Draft202012Validator(schema)

    # Load entries, annotate with file path for reporting
    entries: List[JSON] = []
    if entries_dir.exists():
        for p in sorted(entries_dir.glob("*.json"), key=lambda x: x.name):
            # Skip non-entry files (like seed_report.json)
            # Accept files starting with digits OR DOC-GEU-ENTRY prefix
            if not (p.name[0].isdigit() or p.name.startswith("DOC-GEU-ENTRY")):
                continue
            e = read_json(p)
            e["__file_path__"] = str(p.as_posix())
            entries.append(e)

    # R001: unique geu_id
    seen: Dict[str, str] = {}
    for e in entries:
        gid = e.get("geu_id")
        p = _entry_file_path(e)
        if not gid:
            continue
        if gid in seen:
            findings.append(Finding(
                rule_id=R_UNIQUE_GEU_ID, severity="ERROR",
                message=f"Duplicate geu_id {gid} in {p} and {seen[gid]}",
                geu_id=gid, entry_path=p,
                remediation="Ensure each GEU entry file has a globally unique geu_id."
            ))
        else:
            seen[gid] = p or "<?>"

    # R002: filename must match geu_id
    for e in entries:
        gid = e.get("geu_id")
        p = _entry_file_path(e)
        if gid and p:
            expected = f"{gid}.json"
            if Path(p).name != expected:
                findings.append(Finding(
                    rule_id=R_FILENAME_MATCH, severity="ERROR",
                    message=f"Entry filename {Path(p).name} does not match geu_id {gid} (expected {expected})",
                    geu_id=gid, entry_path=p,
                    remediation="Rename the file to <geu_id>.json or update geu_id to match."
                ))

    # R003: JSON Schema validation (ignore internal metadata field)
    for e in entries:
        gid = e.get("geu_id")
        p = _entry_file_path(e)
        clean = dict(e)
        clean.pop("__file_path__", None)
        for err in sorted(validator.iter_errors(clean), key=lambda x: x.json_path):
            findings.append(Finding(
                rule_id=R_SCHEMA_VALID, severity="ERROR",
                message=f"Schema validation error at {err.json_path}: {err.message}",
                geu_id=gid, entry_path=p,
                remediation="Fix the GEU entry to satisfy geu_entry.schema.json."
            ))

    # R005: no duplicate file_id in members[]
    for e in entries:
        gid = e.get("geu_id")
        p = _entry_file_path(e)
        member_ids = [m.get("file_id") for m in e.get("members", [])]
        dup = {x for x in member_ids if x and member_ids.count(x) > 1}
        if dup:
            findings.append(Finding(
                rule_id=R_NO_DUP_MEMBER_FILE, severity="ERROR",
                message=f"Duplicate members.file_id(s) found: {sorted(dup)}",
                geu_id=gid, entry_path=p,
                remediation="Each file_id may appear at most once in members[]."
            ))

    # Load file registry if present
    file_index: Dict[str, JSON] = {}
    registry_loaded = False
    if file_registry_path.exists():
        reg = read_json(file_registry_path)
        file_index = file_id_index_from_registry(reg)
        registry_loaded = True

    # R004: all referenced file_ids exist
    if registry_loaded:
        for e in entries:
            gid = e.get("geu_id")
            p = _entry_file_path(e)
            refs = [e.get("anchor_file_id")]
            refs += [m.get("file_id") for m in e.get("members", [])]
            refs += [o.get("file_id") for o in e.get("outputs", [])]
            refs += [t.get("file_id") for t in e.get("tests", [])]
            missing = [rid for rid in refs if rid and rid not in file_index]
            if missing:
                findings.append(Finding(
                    rule_id=R_REF_FILE_EXISTS, severity="ERROR",
                    message=f"Referenced file_id(s) not found in file registry: {sorted(set(missing))}",
                    geu_id=gid, entry_path=p,
                    remediation="Add missing file records to governance_registry.json or correct the references."
                ))
    else:
        findings.append(Finding(
            rule_id=R_REF_FILE_EXISTS, severity="WARN",
            message=f"File registry not found at {file_registry_path.as_posix()}; referential checks skipped.",
            remediation="Create governance_registry.json or pass --file-registry PATH when running validation."
        ))

    # R006: slot matrix enforcement by geu_type
    slot_matrix = _load_slot_matrix()
    for e in entries:
        gid = e.get("geu_id")
        gtype = e.get("geu_type")
        p = _entry_file_path(e)
        if not gtype or gtype not in slot_matrix:
            findings.append(Finding(
                rule_id=R_SLOT_MATRIX, severity="ERROR",
                message=f"Unknown geu_type '{gtype}' (no slot matrix entry).",
                geu_id=gid, entry_path=p,
                remediation="Add geu_type to slot_matrix.json or correct geu_type in entry."
            ))
            continue
        required_roles = set(slot_matrix[gtype]["required"])
        present = _role_coverage(e)
        missing = sorted(required_roles - present)
        if missing:
            findings.append(Finding(
                rule_id=R_SLOT_MATRIX, severity="ERROR",
                message=f"GEU missing required role slots for type {gtype}: {missing}. Present: {sorted(present)}",
                geu_id=gid, entry_path=p,
                remediation="Add required role artifacts to members/outputs/tests or adjust slot matrix intentionally."
            ))

    # R009: dependency integrity (exists, no self-deps, no cycles)
    geu_ids = {e.get("geu_id") for e in entries if e.get("geu_id")}
    for e in entries:
        gid = e.get("geu_id")
        p = _entry_file_path(e)
        deps = e.get("depends_on_geu_ids", []) or []
        if len(deps) != len(set(deps)):
            findings.append(Finding(
                rule_id=R_DEPENDENCIES, severity="ERROR",
                message=f"Duplicate depends_on_geu_ids in GEU {gid}: {deps}",
                geu_id=gid, entry_path=p,
                remediation="Deduplicate depends_on_geu_ids."
            ))
        for d in deps:
            if d == gid:
                findings.append(Finding(
                    rule_id=R_DEPENDENCIES, severity="ERROR",
                    message=f"GEU {gid} depends on itself.",
                    geu_id=gid, entry_path=p,
                    remediation="Remove self-dependency."
                ))
            elif d not in geu_ids:
                findings.append(Finding(
                    rule_id=R_DEPENDENCIES, severity="ERROR",
                    message=f"GEU {gid} depends on missing geu_id {d}.",
                    geu_id=gid, entry_path=p,
                    remediation="Create the dependency GEU entry or remove the reference."
                ))

    # cycle detection (DFS)
    graph = {e["geu_id"]: list(e.get("depends_on_geu_ids", []) or []) for e in entries if e.get("geu_id")}
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle = stack[stack.index(node):] + [node]
            findings.append(Finding(
                rule_id=R_DEPENDENCIES, severity="ERROR",
                message=f"Dependency cycle detected: {' -> '.join(cycle)}",
                geu_id=node,
                remediation="Break the cycle by removing or re-pointing one depends_on edge."
            ))
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for n in sorted(graph.keys()):
        if n not in visited:
            dfs(n, [])

    # R007: shared file semantics via shared_access
    memberships = all_memberships(entries)
    by_file: Dict[str, List[Tuple[str, str, str]]] = {}
    for fid, gid, role, sa in memberships:
        by_file.setdefault(fid, []).append((gid, role, sa))

    for fid, uses in by_file.items():
        if len(uses) == 1:
            gid, _role, sa = uses[0]
            if sa != "NONE":
                findings.append(Finding(
                    rule_id=R_SHARED_OWNERSHIP, severity="ERROR",
                    message=f"file_id {fid} has shared_access={sa} but appears in only one GEU ({gid}).",
                    file_id=fid, geu_id=gid,
                    remediation="Set shared_access=NONE for non-shared files."
                ))
            continue

        owners = [(gid, role) for gid, role, sa in uses if sa == "OWNER"]
        if len(owners) != 1:
            findings.append(Finding(
                rule_id=R_SHARED_OWNERSHIP, severity="ERROR",
                message=f"Shared file_id {fid} must have exactly one OWNER; found {owners or 'none'}. Uses: {uses}",
                file_id=fid,
                remediation="Set shared_access=OWNER on exactly one membership and CONSUMER on all others."
            ))

        for gid, _role, sa in uses:
            if sa == "NONE":
                findings.append(Finding(
                    rule_id=R_SHARED_OWNERSHIP, severity="ERROR",
                    message=f"Shared file_id {fid} appears in multiple GEUs but membership in {gid} has shared_access=NONE.",
                    file_id=fid, geu_id=gid,
                    remediation="Set shared_access=CONSUMER (or OWNER for exactly one GEU)."
                ))

    # R008: no orphan governance-critical files (validators/gates/schemas)
    if registry_loaded:
        critical_file_ids: Set[str] = set()
        for fid, rec in file_index.items():
            layer = rec.get("layer")
            kind = rec.get("artifact_kind")
            if layer in CRITICAL_LAYERS or kind in CRITICAL_ARTIFACT_KINDS:
                critical_file_ids.add(fid)

        member_file_ids: Set[str] = {fid for fid, _gid, _role, _sa in memberships}
        orphans = sorted(critical_file_ids - member_file_ids)
        if orphans:
            findings.append(Finding(
                rule_id=R_NO_ORPHAN_CRITICAL, severity="ERROR",
                message=f"Orphan governance-critical file_id(s) (not in any GEU): {orphans}",
                remediation="Add these files to an appropriate GEU entry (or create a new GEU)."
            ))

    return entries, findings
