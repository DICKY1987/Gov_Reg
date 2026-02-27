"""File inventory builder."""
from __future__ import annotations

import ast
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from P_01260202173939000061_component_extractor import ComponentVisitor
from P_01260202173939000063_dependency_analyzer import analyze_dependencies
from P_01260202173939000083_i_o_surface_analyzer import analyze_io_surface
from P_01260207233100000010_canonical_hash import hash_file_content
from P_01999000042260124490_io_utils import write_json, write_jsonl
from P_01260207201000000864_01999000042260130001_argparse_extractor import extract_argparse_commands


class FileInventoryBuilder:
    """Build a deterministic inventory of repository files."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.exclude_dirs = {
            ".git",
            ".state",
            ".state_temp",
            ".worktrees",
            ".venv",
            "node_modules",
            ".pytest_cache",
        }

    def build_inventory(self, output_path: Path, evidence_dir: Path) -> bool:
        records = []
        for path in self._walk_repo():
            record = self._analyze_file(path)
            if record:
                records.append(record)

        write_jsonl(output_path, records)

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(records),
            "output_path": str(output_path),
            "output_sha256": hash_file_content(output_path),
        }
        write_json(evidence_dir / "step2_inventory_summary.json", summary, indent=2, sort_keys=True)
        write_json(evidence_dir / "step2_inventory_sha256.json", {"sha256": summary["output_sha256"]}, indent=2, sort_keys=True)

        has_python = any(r.get("ext") == ".py" for r in records)
        has_schema = any(r.get("classification") == "schema_json" for r in records)
        return len(records) > 0 and (has_python or has_schema)

    def _walk_repo(self) -> List[Path]:
        paths: List[Path] = []
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            for name in files:
                if name.endswith(".regenerated.json"):
                    continue
                full_path = Path(root) / name
                rel_path = full_path.relative_to(self.repo_root)
                paths.append(rel_path)
        return sorted(paths)

    def _analyze_file(self, rel_path: Path) -> Optional[Dict]:
        full_path = self.repo_root / rel_path
        if not full_path.is_file():
            return None

        ext = full_path.suffix.lower()
        classification = self._classify_file(rel_path, full_path)
        record: Dict[str, Optional[object]] = {
            "path": rel_path.as_posix(),
            "ext": ext,
            "classification": classification,
            "size_bytes": full_path.stat().st_size,
            "sha256": hash_file_content(full_path),
            "is_executable_candidate": classification == "python_entrypoint",
        }

        if ext == ".py":
            record.update(self._analyze_python_file(full_path))
        elif ext == ".json":
            record.update(self._analyze_json_file(full_path))

        return record

    def _classify_file(self, rel_path: Path, full_path: Path) -> str:
        name = rel_path.name.lower()
        ext = full_path.suffix.lower()
        if ext == ".py":
            if name.startswith("test_") or name.endswith("_test.py"):
                return "python_test"
            if rel_path.parts and rel_path.parts[0].lower() == "scripts":
                return "python_entrypoint"
            try:
                text = full_path.read_text(encoding="utf-8")
                if "if __name__ == \"__main__\"" in text:
                    return "python_entrypoint"
            except Exception:
                pass
            return "python_module"
        if ext == ".json":
            try:
                data = json.loads(full_path.read_text(encoding="utf-8"))
                if "$schema" in data or "$id" in data:
                    return "schema_json"
            except Exception:
                pass
            if "template" in name or "spec" in name:
                return "template_json"
            return "data"
        if ext in {".yml", ".yaml"}:
            return "config"
        if ext == ".md":
            if any(token in name for token in ["spec", "instruction", "requirement"]):
                return "spec_doc"
            return "doc"
        return "unknown"

    def _analyze_python_file(self, full_path: Path) -> Dict:
        try:
            source = full_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return {
                "imports": [],
                "defines": [],
                "argparse_commands": [],
                "subprocess_calls": [],
                "path_literals": [],
                "required_exists_guess": False,
                "required_exists_paths": [],
            }

        components = ComponentVisitor(source)
        components.visit(tree)
        defines = [c["name"] for c in components.classes] + [f["name"] for f in components.functions]
        defines = sorted(set(defines))

        deps = analyze_dependencies(full_path)
        imports = deps.get("py_imports_list", []) if deps.get("success") else []

        argparse_cmds = []
        try:
            result = extract_argparse_commands(full_path)
            if result.get("success"):
                argparse_cmds = [cmd.get("name") for cmd in result.get("commands", []) if cmd.get("name")]
        except Exception:
            pass

        io_surface = analyze_io_surface(tree)
        subprocess_calls = [
            api for api in io_surface.get("py_security_sensitive_apis", [])
            if "subprocess" in api.get("function", "") or api.get("function") == "os.system"
        ]

        path_literals = self._extract_path_literals(source)
        required_exists_paths = [p for p in path_literals if (self.repo_root / p).exists()]

        return {
            "imports": imports,
            "defines": defines,
            "argparse_commands": sorted(set(argparse_cmds)),
            "subprocess_calls": subprocess_calls,
            "path_literals": path_literals,
            "required_exists_guess": bool(required_exists_paths),
            "required_exists_paths": required_exists_paths,
        }

    def _analyze_json_file(self, full_path: Path) -> Dict:
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {
                    "json_parseable": True,
                    "schema_id": data.get("$id"),
                    "title": data.get("title"),
                }
            return {"json_parseable": True, "schema_id": None, "title": None}
        except json.JSONDecodeError:
            return {"json_parseable": False, "schema_id": None, "title": None}

    @staticmethod
    def _extract_path_literals(source: str) -> List[str]:
        pattern = re.compile(r"[\"']([^\"']*[\\/][^\"']*)[\"']")
        matches = [m.group(1) for m in pattern.finditer(source)]
        cleaned = []
        for item in matches:
            if len(item) > 2:
                cleaned.append(item.replace("\\", "/"))
        return sorted(set(cleaned))
