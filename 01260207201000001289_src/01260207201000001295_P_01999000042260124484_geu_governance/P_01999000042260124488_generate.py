"""GEU governance artifact generators.

FILE_ID: 0199900004226012488
DOC_ID: DOC-CORE-GEU-GOVERNANCE-GENERATE-0199900004226012488
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator

from .P_01999000042260124487_constants import (
    ENTRIES_DIR,
    FILE_REGISTRY_OVERLAY_PATH,
    FILE_REGISTRY_PATH,
    GEU_EDGE_SCHEMA_PATH,
    GEU_EDGES_PATH,
    GEU_INDEX_PATH,
)
from .P_01999000042260124490_io_utils import read_json, write_json, write_jsonl
from .P_01999000042260124492_validation import validate_geu_entries, all_memberships

JSON = Dict[str, Any]

def generate_geu_index(entries: List[JSON]) -> JSON:
    items = []
    for e in sorted(entries, key=lambda x: x["geu_id"]):
        items.append({
            "geu_id": e["geu_id"],
            "geu_type": e["geu_type"],
            "geu_key": e["geu_key"],
            "anchor_file_id": e["anchor_file_id"],
        })
    return {"generated": True, "entry_count": len(items), "entries": items}

def generate_edges(entries: List[JSON]) -> List[JSON]:
    edges: List[JSON] = []
    for e in entries:
        gid = e["geu_id"]
        edges.append({
            "edge_type": "MEMBER_OF_GEU",
            "source_file_id": e["anchor_file_id"],
            "target_geu_id": gid,
            "role_slot": e["anchor_role_slot"],
            "shared_access": e["anchor_shared_access"],
        })
        for m in e.get("members", []):
            edges.append({
                "edge_type": "MEMBER_OF_GEU",
                "source_file_id": m["file_id"],
                "target_geu_id": gid,
                "role_slot": m["role_slot"],
                "shared_access": m.get("shared_access", "NONE"),
            })
        for o in e.get("outputs", []):
            edges.append({
                "edge_type": "MEMBER_OF_GEU",
                "source_file_id": o["file_id"],
                "target_geu_id": gid,
                "role_slot": o["output_kind"],
                "shared_access": o.get("shared_access", "NONE"),
            })
        for t in e.get("tests", []):
            edges.append({
                "edge_type": "MEMBER_OF_GEU",
                "source_file_id": t["file_id"],
                "target_geu_id": gid,
                "role_slot": "TEST",
                "shared_access": t.get("shared_access", "NONE"),
            })
        for dep in e.get("depends_on_geu_ids", []):
            edges.append({"edge_type": "GEU_DEPENDS_ON", "source_geu_id": gid, "target_geu_id": dep})

    def key(edge: JSON) -> Tuple:
        et = edge["edge_type"]
        if et == "GEU_DEPENDS_ON":
            return (0, edge["source_geu_id"], edge["target_geu_id"])
        return (1, edge["source_file_id"], edge["target_geu_id"], edge.get("role_slot", ""))
    return sorted(edges, key=key)

def generate_file_registry_overlay(entries: List[JSON]) -> JSON:
    memberships = all_memberships(entries)
    by_file: Dict[str, List[Tuple[str, str, str]]] = {}
    for fid, gid, role, sa in memberships:
        by_file.setdefault(fid, []).append((gid, role, sa))

    overlay: Dict[str, Any] = {"generated": True, "files": {}}
    for fid, uses in sorted(by_file.items(), key=lambda x: x[0]):
        geu_ids = sorted({gid for gid, _, _ in uses})
        is_shared = len(geu_ids) > 1
        owners = [gid for gid, _, sa in uses if sa == "OWNER"]
        owner_geu_id = owners[0] if len(owners) == 1 else None
        primary_geu_id = owner_geu_id or (geu_ids[0] if geu_ids else None)
        overlay["files"][fid] = {
            "geu_ids": geu_ids,
            "primary_geu_id": primary_geu_id,
            "is_shared": is_shared,
            "owner_geu_id": owner_geu_id,
        }
    return overlay

def validate_edges_schema(edges: List[JSON]) -> List[str]:
    schema = read_json(GEU_EDGE_SCHEMA_PATH)
    v = Draft202012Validator(schema)
    errors: List[str] = []
    for i, e in enumerate(edges):
        for err in sorted(v.iter_errors(e), key=lambda x: x.json_path):
            errors.append(f"Edge[{i}] {err.json_path}: {err.message}")
    return errors

def write_generated_artifacts(*, write: bool = True) -> Dict[str, Any]:
    entries, findings = validate_geu_entries(entries_dir=ENTRIES_DIR, file_registry_path=FILE_REGISTRY_PATH)
    index = generate_geu_index(entries)
    edges = generate_edges(entries)
    overlay = generate_file_registry_overlay(entries)
    edge_schema_errors = validate_edges_schema(edges)
    return {"entries": entries, "findings": findings, "index": index, "edges": edges, "overlay": overlay, "edge_schema_errors": edge_schema_errors, "write": write}

def persist_generated_artifacts(bundle: Dict[str, Any]) -> None:
    write_json(GEU_INDEX_PATH, bundle["index"])
    write_jsonl(GEU_EDGES_PATH, bundle["edges"])
    write_json(FILE_REGISTRY_OVERLAY_PATH, bundle["overlay"])
