"""Capability discovery logic."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from P_01260207233100000010_canonical_hash import hash_file_content
from P_01999000042260124490_io_utils import write_json
from P_01260207201000000864_P_01260207233100000YYY_argparse_extractor import extract_argparse_commands


class CapabilityDiscoverer:
    """Discover capabilities from CLI, gates, and schemas."""

    def discover_all(self, repo_root: Path, output_path: Path, evidence_dir: Path) -> Tuple[bool, Dict]:
        capabilities: List[Dict] = []
        warnings: List[str] = []
        conflicts: List[Dict] = []

        capabilities.extend(self.discover_from_cli(repo_root / "scripts"))
        capabilities.extend(self.discover_from_gates(repo_root))
        capabilities.extend(self.discover_from_schemas(repo_root / "schemas"))

        resolved, conflicts = self.deduplicate_and_resolve_conflicts(capabilities)

        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "precedence_rule": ["code", "schemas", "template_specs", "docs"],
            "capabilities": resolved,
            "capability_conflicts": conflicts,
            "warnings": warnings,
        }

        if not resolved:
            warnings.append("No capabilities discovered")

        write_json(output_path, result, indent=2, sort_keys=True)

        evidence = {
            "capability_count": len(resolved),
            "conflict_count": len(conflicts),
            "warnings": warnings,
            "output_path": str(output_path),
            "output_sha256": hash_file_content(output_path),
        }
        write_json(evidence_dir / "step1_capabilities_generation.json", evidence, indent=2, sort_keys=True)
        write_json(evidence_dir / "step1_capabilities_sha256.json", {"sha256": evidence["output_sha256"]}, indent=2, sort_keys=True)

        ok = len(resolved) > 0 and len({c["capability_id"] for c in resolved}) == len(resolved)
        return ok, result

    def discover_from_cli(self, scripts_dir: Path) -> List[Dict]:
        capabilities: List[Dict] = []
        if not scripts_dir.exists():
            return capabilities

        for path in sorted(scripts_dir.rglob("*.py")):
            try:
                source_text = path.read_text(encoding="utf-8")
            except Exception:
                continue

            try:
                commands = extract_argparse_commands(source_text)
            except (SyntaxError, ValueError):
                continue
            except Exception:
                continue
            for cmd in commands:
                cap_id = f"CAP-CLI-{self._sanitize_id(cmd.name)}"
                name = self._title_from_command(cmd.name)
                capabilities.append({
                    "capability_id": cap_id,
                    "name": name,
                    "domain": "cli",
                    "status": "implemented",
                    "source_rank": 1,
                    "source_evidence": [
                        {
                            "path": path.relative_to(scripts_dir.parent).as_posix(),
                            "evidence_type": "ast",
                            "detail": f"argparse subcommand '{cmd.name}'",
                            "line_number": cmd.lineno,
                        }
                    ],
                    "expected_artifacts": [],
                    "candidate_files": [path.relative_to(scripts_dir.parent).as_posix()],
                })

        return capabilities

    def discover_from_gates(self, repo_root: Path) -> List[Dict]:
        capabilities: List[Dict] = []
        pattern = re.compile(r"GATE-(\d{3})(?:\s*[:\-]\s*(.*))?")
        exclude_dirs = {".git", ".state", ".worktrees", ".venv", "node_modules"}

        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = Path(root) / name
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                for match in pattern.finditer(text):
                    gate_num = match.group(1)
                    desc = (match.group(2) or "").strip()
                    name = desc if desc else f"Gate {gate_num}"
                    cap_id = f"CAP-GATE-{gate_num}-{self._sanitize_id(name)}"
                    line_number = text[: match.start()].count("\n") + 1
                    capabilities.append({
                        "capability_id": cap_id,
                        "name": name,
                        "domain": "gate",
                        "status": "implemented",
                        "source_rank": 1,
                        "source_evidence": [
                            {
                            "path": path.relative_to(repo_root).as_posix(),
                                "evidence_type": "string_match",
                                "detail": match.group(0),
                                "line_number": line_number,
                            }
                        ],
                        "expected_artifacts": [],
                    "candidate_files": [path.relative_to(repo_root).as_posix()],
                    })

        return capabilities

    def discover_from_schemas(self, schemas_dir: Path) -> List[Dict]:
        capabilities: List[Dict] = []
        if not schemas_dir.exists():
            return capabilities

        for path in sorted(schemas_dir.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            title = data.get("title") or path.stem
            cap_id = f"CAP-SCHEMA-{self._sanitize_id(title)}"
            capabilities.append({
                "capability_id": cap_id,
                "name": title,
                "domain": "schema",
                "status": "implemented",
                "source_rank": 2,
                "source_evidence": [
                    {
                        "path": path.relative_to(schemas_dir.parent).as_posix(),
                        "evidence_type": "schema_id",
                        "detail": data.get("$id") or title,
                        "line_number": 1,
                    }
                ],
                "expected_artifacts": [],
                "candidate_files": [path.relative_to(schemas_dir.parent).as_posix()],
            })

        return capabilities

    def deduplicate_and_resolve_conflicts(self, capabilities: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        by_id: Dict[str, List[Dict]] = {}
        for cap in capabilities:
            by_id.setdefault(cap["capability_id"], []).append(cap)

        resolved: List[Dict] = []
        conflicts: List[Dict] = []

        for cap_id in sorted(by_id.keys()):
            group = by_id[cap_id]
            if len(group) == 1:
                cap = group[0]
                cap.pop("source_rank", None)
                resolved.append(cap)
                continue

            group_sorted = sorted(group, key=lambda c: c.get("source_rank", 999))
            winner = group_sorted[0]
            conflicts.append({
                "capability_id": cap_id,
                "chosen_source": winner.get("source_evidence"),
                "discarded_sources": [g.get("source_evidence") for g in group_sorted[1:]],
            })
            winner.pop("source_rank", None)
            resolved.append(winner)

        return resolved, conflicts

    @staticmethod
    def _sanitize_id(text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text.strip())
        return cleaned.strip("_").upper() or "UNKNOWN"

    @staticmethod
    def _title_from_command(command: str) -> str:
        return " ".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", command) if part)
