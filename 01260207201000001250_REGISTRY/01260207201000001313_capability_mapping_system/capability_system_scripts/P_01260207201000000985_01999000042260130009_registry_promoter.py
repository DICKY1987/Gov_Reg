"""Registry promotion step."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from P_01260207233100000010_canonical_hash import hash_canonical_data
from P_01999000042260124490_io_utils import read_json, write_json
from P_01260207201000000834_apply_patch import apply_patch


class RegistryPromoter:
    """Promote purpose mappings into the SSOT registry."""

    REQUIRED_HEADERS = {"one_line_purpose", "py_capability_tags", "py_capability_facts_hash"}

    def __init__(self, repo_root: Path, registry_root: Path, evidence_dir: Path):
        self.repo_root = repo_root
        self.registry_root = registry_root
        self.evidence_dir = evidence_dir

    def promote(self, mapping_path: Path, capabilities_path: Path, registry_path: Path, column_dict_path: Path, mode: str) -> bool:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        mapping = read_json(mapping_path)
        capabilities = read_json(capabilities_path)
        registry = read_json(registry_path)
        column_dict = read_json(column_dict_path)

        write_json(self.evidence_dir / "registry_paths_resolved.json", {
            "registry_path": str(registry_path),
            "column_dictionary_path": str(column_dict_path),
            "mapping_path": str(mapping_path),
        }, indent=2, sort_keys=True)

        headers = set(column_dict.get("headers", {}).keys())
        missing_headers = sorted(self.REQUIRED_HEADERS - headers)
        if missing_headers:
            write_json(self.evidence_dir / "apply_result.json", {
                "success": False,
                "error": f"Missing required headers: {missing_headers}",
            }, indent=2, sort_keys=True)
            return False

        before_snapshot = self._snapshot_registry(registry)
        write_json(self.evidence_dir / "before_snapshot.json", before_snapshot, indent=2, sort_keys=True)

        try:
            patch_ops, diff_summary = self._build_patch(mapping, capabilities, registry)
        except Exception as exc:
            write_json(self.evidence_dir / "apply_result.json", {
                "success": False,
                "error": str(exc),
            }, indent=2, sort_keys=True)
            return False
        patch_path = self.evidence_dir / "patch_ssot_purpose_mapping.rfc6902.json"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_path.write_text(json.dumps(patch_ops, indent=2) + "\n", encoding="utf-8")

        dry_run = mode != "apply"
        apply_result = apply_patch(registry_path, patch_path, self.evidence_dir, dry_run=dry_run)
        write_json(self.evidence_dir / "apply_result.json", apply_result, indent=2, sort_keys=True)

        after_registry = read_json(registry_path) if mode == "apply" else apply_result
        after_snapshot = self._snapshot_registry(after_registry, use_result=(mode != "apply"))
        write_json(self.evidence_dir / "after_snapshot.json", after_snapshot, indent=2, sort_keys=True)

        write_json(self.evidence_dir / "diff_summary.json", diff_summary, indent=2, sort_keys=True)
        write_json(self.evidence_dir / "ssot_writeback_sha256.json", {
            "patched_hash": apply_result.get("patched_hash"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2, sort_keys=True)

        return True

    def _build_patch(self, mapping: Dict, capabilities: Dict, registry: Dict) -> Tuple[List[Dict], Dict]:
        cap_index = {cap["capability_id"]: cap for cap in capabilities.get("capabilities", [])}
        files = registry.get("files", [])
        path_to_index = {}
        for i, rec in enumerate(files):
            rel = rec.get("relative_path")
            if rel in path_to_index:
                raise ValueError(f"Duplicate relative_path in registry: {rel}")
            path_to_index[rel] = i

        ops: List[Dict] = []
        updated_files: List[str] = []
        skipped_new_files: List[str] = []

        for mapping_rec in sorted(mapping.get("mappings", []), key=lambda m: m["file"]):
            file_path = mapping_rec.get("file")
            if file_path not in path_to_index:
                # File exists in mapping but not in registry - probably new file
                skipped_new_files.append(file_path)
                continue
            idx = path_to_index[file_path]

            primary = mapping_rec.get("primary_capability_id")
            secondary = mapping_rec.get("secondary_capability_ids") or []
            tags = sorted({t for t in [primary] + list(secondary) if t})

            cap_name = cap_index.get(primary, {}).get("name") if primary else None
            one_line_purpose = f"{primary}: {cap_name}" if primary and cap_name else (primary or "")

            facts = {
                "file": file_path,
                "primary_capability_id": primary,
                "secondary_capability_ids": secondary,
                "exports": mapping_rec.get("exports") or [],
                "consumes": mapping_rec.get("consumes") or [],
                "produces": mapping_rec.get("produces") or [],
                "called_by_observed": mapping_rec.get("called_by_observed") or [],
            }
            facts_hash = hash_canonical_data(facts)

            notes = None
            justification = mapping_rec.get("justification")
            if justification:
                notes = f"capmap:confidence={mapping_rec.get('mapping_confidence')}; justification={justification}"
                if len(notes) > 500:
                    notes = notes[:500]

            field_ops = [
                ("one_line_purpose", one_line_purpose),
                ("py_capability_tags", tags),
                ("py_capability_facts_hash", facts_hash),
            ]
            if notes:
                field_ops.append(("notes", notes))

            for field, value in field_ops:
                path = f"/files/{idx}/{field}"
                op = "replace" if field in files[idx] else "add"
                ops.append({"op": op, "path": path, "value": value})

            updated_files.append(file_path)

        diff_summary = {
            "files_updated": sorted(updated_files),
            "files_skipped_new": sorted(skipped_new_files),
            "operations_count": len(ops),
        }
        return ops, diff_summary

    @staticmethod
    def _snapshot_registry(registry: Dict, use_result: bool = False) -> Dict:
        if use_result:
            return {
                "patched_hash": registry.get("patched_hash"),
                "operations_count": registry.get("operations_count"),
                "timestamp": registry.get("timestamp"),
            }
        files = registry.get("files", [])
        sample = [
            {"file_id": rec.get("file_id"), "relative_path": rec.get("relative_path")}
            for rec in files[:5]
        ]
        return {
            "file_count": len(files),
            "sample": sample,
        }
