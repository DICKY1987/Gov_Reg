"""Purpose registry builder."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

from P_01999000042260124490_io_utils import read_json, write_json
from P_01260207201000000981_01999000042260130004_call_graph_builder import CallGraphBuilder


class PurposeRegistryBuilder:
    """Map files to capabilities."""

    def __init__(self, capabilities_path: Path, inventory_path: Path, repo_root: Path, vocab_path: Path = None, overrides_path: Path = None):
        self.repo_root = repo_root
        self.capabilities = read_json(capabilities_path)
        self.inventory = self._load_inventory(inventory_path)
        self.file_index = {rec["path"]: rec for rec in self.inventory}
        self.cap_index = {cap["capability_id"]: cap for cap in self.capabilities.get("capabilities", [])}
        self.vocab = read_json(vocab_path) if vocab_path and vocab_path.exists() else None
        self.overrides = read_json(overrides_path) if overrides_path and overrides_path.exists() else {}

    def build_registry(self, output_path: Path, evidence_dir: Path) -> bool:
        gate_scope = self._determine_gate_scope()
        warnings_list = []
        mappings, review_queue = self._map_files_to_capabilities(gate_scope, warnings_list)
        mappings = self._enrich_with_call_graph(mappings)

        validation = self._validate_registry(mappings, gate_scope)
        validation["warnings"].extend(warnings_list)

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
            "warnings_count": len(validation["warnings"]),
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

    def _map_files_to_capabilities(self, gate_scope: Set[str], warnings: List[str]) -> Tuple[List[Dict], List[Dict]]:
        mappings: List[Dict] = []
        review_queue: List[Dict] = []

        for rec in sorted(self.inventory, key=lambda r: r["path"]):
            path = rec["path"]
            classification = rec.get("classification")
            defines = rec.get("defines", [])
            consumes = rec.get("required_exists_paths", [])
            produces = [p for p in rec.get("path_literals", []) if p.startswith(".state/")]
            path_literals = rec.get("path_literals", [])
            imports = rec.get("imports", [])
            subprocess_calls = rec.get("subprocess_calls", [])
            file_id = rec.get("file_id")

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
                "signal_sources": [],
            }

            if classification == "schema_json":
                cap_id = self._schema_capability_id(rec)
                mapping.update({
                    "primary_capability_id": cap_id,
                    "mapping_confidence": "high",
                    "justification": "schema file",
                    "signal_sources": ["classification:schema_json"],
                })
            elif self._has_gate_signal(path, rec):
                gate_caps = self._gate_capability_ids(path)
                cap_id = gate_caps[0] if gate_caps else self._gate_capability_id(path)
                mapping.update({
                    "primary_capability_id": cap_id,
                    "secondary_capability_ids": sorted(set(gate_caps[1:])),
                    "mapping_confidence": "high",
                    "justification": "gate marker detected",
                    "signal_sources": ["gate_marker"],
                })
            elif classification == "python_entrypoint" and rec.get("argparse_commands"):
                primary_id = f"CAP-CLI-{self._sanitize_id(Path(path).stem)}"
                secondary = [f"CAP-CLI-{self._sanitize_id(cmd)}" for cmd in rec.get("argparse_commands", [])]
                mapping.update({
                    "primary_capability_id": primary_id,
                    "secondary_capability_ids": sorted(set(secondary)),
                    "mapping_confidence": "high",
                    "justification": "CLI entrypoint with argparse commands",
                    "signal_sources": ["classification:python_entrypoint", "argparse_commands"],
                })
            elif self._check_id_allocation_signal(path_literals):
                mapping.update({
                    "primary_capability_id": "CAP-IDS-ALLOCATE",
                    "mapping_confidence": "high",
                    "justification": "ID allocation file access detected",
                    "signal_sources": ["path_literals:COUNTER_STORE|_ID_LEDGER"],
                })
            elif self._check_validation_signal(imports):
                mapping.update({
                    "primary_capability_id": "CAP-REGISTRY-VALIDATE",
                    "mapping_confidence": "high",
                    "justification": "schema validation detected",
                    "signal_sources": ["imports:jsonschema|fastjsonschema"],
                })
            elif self._check_evidence_emit_signal(produces):
                mapping.update({
                    "primary_capability_id": "CAP-EVIDENCE-EMIT",
                    "mapping_confidence": "medium",
                    "justification": "evidence file production detected",
                    "signal_sources": ["produces:.state/evidence/"],
                })
            elif self._check_orchestration_signal(subprocess_calls, imports):
                mapping.update({
                    "primary_capability_id": "CAP-ORCHESTRATION-RUN",
                    "mapping_confidence": "medium",
                    "justification": "orchestration subprocess execution detected",
                    "signal_sources": ["subprocess_calls", "imports:orchestration"],
                })
            elif self._check_archive_signal(path_literals):
                mapping.update({
                    "primary_capability_id": "CAP-ARCHIVE-ARCHIVE_MOVE",
                    "mapping_confidence": "medium",
                    "justification": "archive operations detected",
                    "signal_sources": ["path_literals:archive|_backups|_ARCHIVE"],
                })
            elif self._check_registry_patch_signal(path_literals):
                mapping.update({
                    "primary_capability_id": "CAP-REGISTRY-PATCH_APPLY",
                    "mapping_confidence": "medium",
                    "justification": "registry SSOT modification detected",
                    "signal_sources": ["path_literals:REGISTRY_file.json"],
                })
            elif self._check_geu_registry_vocab(defines):
                cap_id = self._infer_from_vocabulary(defines)
                if cap_id:
                    mapping.update({
                        "primary_capability_id": cap_id,
                        "mapping_confidence": "medium",
                        "justification": "GEU/REGISTRY vocabulary keywords detected",
                        "signal_sources": ["defines:vocabulary_match"],
                    })
            elif self._candidate_capability_id(path):
                mapping.update({
                    "primary_capability_id": self._candidate_capability_id(path),
                    "mapping_confidence": "medium",
                    "justification": "candidate file match",
                    "signal_sources": ["candidate_files"],
                })
            elif classification == "python_module":
                mapping.update({
                    "primary_capability_id": "CAP-LIB-SHARED_SUPPORT",
                    "mapping_confidence": "medium",
                    "justification": "library module",
                    "signal_sources": ["classification:python_module"],
                })
            else:
                mapping.update({
                    "mapping_confidence": "low",
                    "justification": "no deterministic mapping rule",
                    "signal_sources": [],
                })

            override = self._check_override(file_id, path)
            if override:
                mapping.update({
                    "primary_capability_id": override.get("primary_capability_id", mapping["primary_capability_id"]),
                    "mapping_confidence": "pinned",
                    "justification": f"human override: {override.get('reason', 'manual classification')}",
                    "signal_sources": ["override"],
                })

            if mapping["primary_capability_id"] and self.vocab:
                self._validate_against_vocab(mapping["primary_capability_id"], path, warnings)

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

    def _check_id_allocation_signal(self, path_literals: List[str]) -> bool:
        for lit in path_literals:
            if "COUNTER_STORE" in lit or "_ID_LEDGER" in lit:
                return True
        return False

    def _check_validation_signal(self, imports: List[str]) -> bool:
        validation_imports = {"jsonschema", "fastjsonschema"}
        for imp in imports:
            if any(vi in imp for vi in validation_imports):
                return True
        return False

    def _check_evidence_emit_signal(self, produces: List[str]) -> bool:
        return any(".state/evidence/" in p for p in produces)

    def _check_orchestration_signal(self, subprocess_calls: List, imports: List[str]) -> bool:
        if not subprocess_calls:
            return False
        orchestration_imports = {"subprocess", "multiprocessing", "concurrent"}
        for imp in imports:
            if any(oi in imp for oi in orchestration_imports):
                return True
        return False

    def _check_archive_signal(self, path_literals: List[str]) -> bool:
        archive_keywords = {".archive", "_backups", "_ARCHIVE", "archive/"}
        return any(keyword in lit for lit in path_literals for keyword in archive_keywords)

    def _check_registry_patch_signal(self, path_literals: List[str]) -> bool:
        return any("REGISTRY_file.json" in lit for lit in path_literals)

    def _check_geu_registry_vocab(self, defines: List[str]) -> bool:
        vocab_keywords = {"validate_", "reconcile_", "allocate_", "promote_", "scan_", "extract_"}
        return any(any(d.startswith(kw) for kw in vocab_keywords) for d in defines)

    def _infer_from_vocabulary(self, defines: List[str]) -> str:
        for d in defines:
            if d.startswith("validate_"):
                return "CAP-REGISTRY-VALIDATE"
            elif d.startswith("reconcile_"):
                return "CAP-IDS-RECONCILE"
            elif d.startswith("allocate_"):
                return "CAP-IDS-ALLOCATE"
            elif d.startswith("promote_"):
                return "CAP-REGISTRY-PROMOTE"
            elif d.startswith("scan_"):
                return "CAP-REGISTRY-SCAN"
            elif d.startswith("extract_"):
                return "CAP-GOVERNANCE-EXTRACT_FACTS"
        return ""

    def _check_override(self, file_id: str, path: str) -> Dict:
        overrides = self.overrides.get("overrides", {})
        if file_id and file_id in overrides:
            return overrides[file_id]
        if path in overrides:
            return overrides[path]
        return {}

    def _validate_against_vocab(self, cap_id: str, path: str, warnings: List[str]) -> None:
        if not self.vocab:
            return
        components = self.vocab.get("components", [])
        capabilities = self.vocab.get("capabilities", {})
        
        if cap_id.startswith("CAP-"):
            parts = cap_id.split("-")
            if len(parts) >= 2:
                component = parts[1]
                capability = "_".join(parts[2:]) if len(parts) >= 3 else None
                
                if component not in components and not cap_id.startswith("CAP-CLI-") and not cap_id.startswith("CAP-SCHEMA-") and not cap_id.startswith("CAP-GATE-") and cap_id != "CAP-LIB-SHARED_SUPPORT" and cap_id != "CAP-UNMAPPED-REVIEW":
                    warning = f"Component '{component}' not in vocab for {path} (cap_id={cap_id})"
                    warnings.append(warning)
                    print(f"WARNING: {warning}")
                
                if capability and component in capabilities:
                    if capability not in capabilities[component]:
                        warning = f"Capability '{capability}' not in vocab for component '{component}' in {path}"
                        warnings.append(warning)
                        print(f"WARNING: {warning}")
