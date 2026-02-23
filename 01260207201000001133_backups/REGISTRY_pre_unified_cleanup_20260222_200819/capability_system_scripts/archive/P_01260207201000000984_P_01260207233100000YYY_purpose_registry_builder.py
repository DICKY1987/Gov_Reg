"""Purpose registry builder."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.P_01999000042260124484_geu_governance.P_01999000042260124490_io_utils import read_json, write_json
from src.capability_mapping.P_01260207233100000YYY_call_graph_builder import CallGraphBuilder


class PurposeRegistryBuilder:
    """Map files to capabilities."""

    def __init__(self, capabilities_path: Path, inventory_path: Path, repo_root: Path):
        self.repo_root = repo_root
        self.capabilities = read_json(capabilities_path)
        self.inventory = self._load_inventory(inventory_path)
        self.file_index = {rec["path"]: rec for rec in self.inventory}
        self.cap_index = {cap["capability_id"]: cap for cap in self.capabilities.get("capabilities", [])}

    def build_registry(self, output_path: Path, evidence_dir: Path) -> bool:
        gate_scope = self._determine_gate_scope()
        mappings, review_queue = self._map_files_to_capabilities(gate_scope)
        mappings = self._enrich_with_call_graph(mappings)

        validation = self._validate_registry(mappings, gate_scope)

        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "inputs": {
                "capabilities": ".state/purpose_mapping/CAPABILITIES.json",
                "inventory": ".state/purpose_mapping/FILE_INVENTORY.jsonl",
            },
            "gate_scope_policy": {
                "include_classifications": ["python_entrypoint", "schema_json"],
                "include_required_references": True,
            },
            "mappings": mappings,
            "unmapped_gate_scope_files": validation["unmapped_gate_scope_files"],
            "unimplemented_capabilities": validation["unimplemented_capabilities"],
            "duplicate_primary_implementations": validation["duplicate_primary_implementations"],
            "review_queue": review_queue,
            "warnings": validation["warnings"],
        }

        write_json(output_path, result, indent=2, sort_keys=True)

        evidence = {
            "mapping_count": len(mappings),
            "review_queue_count": len(review_queue),
            "unmapped_gate_scope_files": validation["unmapped_gate_scope_files"],
            "unimplemented_capabilities": validation["unimplemented_capabilities"],
            "output_path": str(output_path),
        }
        write_json(evidence_dir / "step3_purpose_registry_generation.json", evidence, indent=2, sort_keys=True)

        ok = not validation["unmapped_gate_scope_files"] and not validation["unimplemented_capabilities"]
        return ok

    def _load_inventory(self, inventory_path: Path) -> List[Dict]:
        records = []
        for line in inventory_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            records.append(json.loads(line))
        return records

    def _determine_gate_scope(self) -> Set[str]:
        gate_scope: Set[str] = set()
        for rec in self.inventory:
            if rec.get("classification") in {"python_entrypoint", "schema_json"}:
                gate_scope.add(rec["path"])
            for ref in rec.get("required_exists_paths", []) or []:
                if ref in self.file_index:
                    gate_scope.add(ref)

        for cap in self.capabilities.get("capabilities", []):
            for candidate in cap.get("candidate_files", []) or []:
                gate_scope.add(candidate)

        return gate_scope

    def _map_files_to_capabilities(self, gate_scope: Set[str]) -> Tuple[List[Dict], List[Dict]]:
        mappings: List[Dict] = []
        review_queue: List[Dict] = []

        for rec in sorted(self.inventory, key=lambda r: r["path"]):
            path = rec["path"]
            classification = rec.get("classification")
            defines = rec.get("defines", [])
            consumes = rec.get("required_exists_paths", [])
            produces = [p for p in rec.get("path_literals", []) if p.startswith(".state/")]

            mapping = {
                "file": path,
                "classification": classification,
                "primary_capability_id": None,
                "secondary_capability_ids": [],
                "exports": defines,
                "consumes": consumes,
                "produces": produces,
                "called_by_observed": [],
                "called_by_declared": [],
                "mapping_confidence": "low",
                "justification": "",
            }

            if classification == "schema_json":
                cap_id = self._schema_capability_id(rec)
                mapping.update({
                    "primary_capability_id": cap_id,
                    "mapping_confidence": "high",
                    "justification": "schema file",
                })
            elif self._has_gate_signal(path, rec):
                gate_caps = self._gate_capability_ids(path)
                cap_id = gate_caps[0] if gate_caps else self._gate_capability_id(path)
                mapping.update({
                    "primary_capability_id": cap_id,
                    "secondary_capability_ids": sorted(set(gate_caps[1:])),
                    "mapping_confidence": "high",
                    "justification": "gate marker detected",
                })
            elif classification == "python_entrypoint" and rec.get("argparse_commands"):
                primary_id = f"CAP-CLI-{self._sanitize_id(Path(path).stem)}"
                secondary = [f"CAP-CLI-{self._sanitize_id(cmd)}" for cmd in rec.get("argparse_commands", [])]
                mapping.update({
                    "primary_capability_id": primary_id,
                    "secondary_capability_ids": sorted(set(secondary)),
                    "mapping_confidence": "high",
                    "justification": "CLI entrypoint with argparse commands",
                })
            elif self._candidate_capability_id(path):
                mapping.update({
                    "primary_capability_id": self._candidate_capability_id(path),
                    "mapping_confidence": "medium",
                    "justification": "candidate file match",
                })
            elif classification == "python_module":
                mapping.update({
                    "primary_capability_id": "CAP-LIB-SHARED_SUPPORT",
                    "mapping_confidence": "medium",
                    "justification": "library module",
                })
            else:
                mapping.update({
                    "mapping_confidence": "low",
                    "justification": "no deterministic mapping rule",
                })

            if not mapping["primary_capability_id"]:
                review_queue.append({"file": path, "reason": mapping["justification"]})
                if path in gate_scope:
                    mapping["primary_capability_id"] = "CAP-UNMAPPED-REVIEW"

            mappings.append(mapping)

        return mappings, review_queue

    def _enrich_with_call_graph(self, mappings: List[Dict]) -> List[Dict]:
        builder = CallGraphBuilder(self.repo_root, self.inventory)
        graph = builder.build()
        for mapping in mappings:
            called_by = sorted(graph.get(mapping["file"], set()))
            mapping["called_by_observed"] = called_by
        return mappings

    def _validate_registry(self, mappings: List[Dict], gate_scope: Set[str]) -> Dict:
        mapped_files = {m["file"] for m in mappings if m.get("primary_capability_id")}
        unmapped_gate_scope_files = sorted(f for f in gate_scope if f not in mapped_files)

        implemented = [
            cap["capability_id"]
            for cap in self.capabilities.get("capabilities", [])
            if cap.get("status") == "implemented"
        ]
        implemented_set = set(implemented)
        mapped_caps = set()
        for mapping in mappings:
            primary = mapping.get("primary_capability_id")
            if primary:
                mapped_caps.add(primary)
            for secondary in mapping.get("secondary_capability_ids") or []:
                mapped_caps.add(secondary)
        unimplemented_capabilities = sorted(implemented_set - mapped_caps)

        primary_counts: Dict[str, int] = {}
        for mapping in mappings:
            cap_id = mapping.get("primary_capability_id")
            if not cap_id:
                continue
            primary_counts[cap_id] = primary_counts.get(cap_id, 0) + 1
        duplicate_primary_implementations = sorted(
            cap_id for cap_id, count in primary_counts.items() if count > 1
        )

        return {
            "unmapped_gate_scope_files": unmapped_gate_scope_files,
            "unimplemented_capabilities": unimplemented_capabilities,
            "duplicate_primary_implementations": duplicate_primary_implementations,
            "warnings": [],
        }

    def _schema_capability_id(self, record: Dict) -> str:
        title = record.get("title") or Path(record["path"]).stem
        cap_id = f"CAP-SCHEMA-{self._sanitize_id(title)}"
        return cap_id

    def _has_gate_signal(self, path: str, record: Dict) -> bool:
        if record.get("defines"):
            for name in record["defines"]:
                if name.startswith("validate_"):
                    return True
        try:
            text = (self.repo_root / path).read_text(encoding="utf-8")
        except Exception:
            return False
        return re.search(r"GATE-\d{3}", text) is not None

    def _gate_capability_ids(self, path: str) -> List[str]:
        try:
            text = (self.repo_root / path).read_text(encoding="utf-8")
        except Exception:
            return []
        ids = []
        for match in re.finditer(r"GATE-(\d{3})(?:\s*[:\-]\s*(.*))?", text):
            gate_num = match.group(1)
            desc = (match.group(2) or f"Gate {gate_num}").strip()
            ids.append(f"CAP-GATE-{gate_num}-{self._sanitize_id(desc)}")
        return ids

    def _gate_capability_id(self, path: str) -> str:
        try:
            text = (self.repo_root / path).read_text(encoding="utf-8")
        except Exception:
            return "CAP-GATE-UNKNOWN"
        match = re.search(r"GATE-(\d{3})(?:\s*[:\-]\s*(.*))?", text)
        if not match:
            return "CAP-GATE-UNKNOWN"
        gate_num = match.group(1)
        desc = (match.group(2) or "Gate").strip()
        return f"CAP-GATE-{gate_num}-{self._sanitize_id(desc)}"

    def _candidate_capability_id(self, path: str) -> str:
        for cap in self.capabilities.get("capabilities", []):
            if path in (cap.get("candidate_files") or []):
                return cap["capability_id"]
        return ""

    @staticmethod
    def _sanitize_id(text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text.strip())
        return cleaned.strip("_").upper() or "UNKNOWN"
