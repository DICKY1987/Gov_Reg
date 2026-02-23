"""
IDPKG Runtime - Unified File+Directory ID Package

FILE_ID: 01999000042260126000
DOC_ID: P_01999000042260126000
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MODULE_DIR = Path(__file__).parent
REPO_ROOT = MODULE_DIR.parent

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

SCRIPTS_PATH = REPO_ROOT / "01260207201000001276_scripts"
if SCRIPTS_PATH.exists() and str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))

from P_01999000042260124030_shared_utils import atomic_json_write, atomic_json_read, utc_timestamp
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000069_dir_id_handler import DirIdManager
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from P_01999000042260125006_id_allocator_facade import allocate_file_id

IDPKG_TOOL_VERSION = "idpkg/1.0.0"


class IdpkgError(RuntimeError):
    """Base error for IDPKG runtime."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expand_path(value: str, base: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def normalize_relative_path(path: Path, root: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise IdpkgError(f"Path {path} is not under project root {root}") from exc
    rel_str = str(rel).replace("\\", "/")
    return rel_str if rel_str else "."


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


@dataclass
class IdpkgConfig:
    config_path: Path
    project_root_id: str
    project_root_path: Path
    staging_depth: int
    governed_min_depth: int
    exclusions: List[str]
    separator: str
    python_prefix: str
    registry_path: Path
    patch_output_dir: Path
    allocator_store_path: Path
    lock_timeout_ms: int
    contracts_dir: Path
    evidence_root: Path

    @classmethod
    def load(cls, config_path: Path) -> "IdpkgConfig":
        if not config_path.exists():
            raise IdpkgError(f"Missing config: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required = ["project_root_id", "project_root_path", "governance", "naming", "registry", "allocator"]
        for key in required:
            if key not in data:
                raise IdpkgError(f"Missing required config field: {key}")

        project_root_path = Path(data["project_root_path"]).resolve()
        governance = data.get("governance", {})
        staging_depth = int(governance.get("staging_depth", 0))
        governed_min_depth = int(governance.get("governed_min_depth", 1))

        if staging_depth != 0 or governed_min_depth != 1:
            raise IdpkgError("Governance depth must be staging_depth=0 and governed_min_depth=1")

        exclusions = data.get("exclusions", {}).get("patterns", [])
        naming = data.get("naming", {})
        separator = naming.get("separator")
        python_prefix = naming.get("python_prefix")
        if not separator:
            raise IdpkgError("Naming.separator is required")
        if python_prefix is None:
            raise IdpkgError("Naming.python_prefix is required")

        registry_cfg = data.get("registry", {})
        registry_path = expand_path(registry_cfg.get("registry_path", ""), project_root_path)
        patch_output_dir = expand_path(registry_cfg.get("patch_output_dir", ""), project_root_path)
        if not registry_path:
            raise IdpkgError("Registry.registry_path is required")
        if not patch_output_dir:
            raise IdpkgError("Registry.patch_output_dir is required")

        allocator_cfg = data.get("allocator", {})
        allocator_store_path = expand_path(allocator_cfg.get("allocator_store_path", ""), project_root_path)
        lock_timeout_ms = int(allocator_cfg.get("lock_timeout_ms", 0))
        if not allocator_store_path:
            raise IdpkgError("Allocator.allocator_store_path is required")

        contracts_dir = config_path.parent / "contracts"
        evidence_root = project_root_path / ".state" / "idpkg" / "evidence"

        return cls(
            config_path=config_path,
            project_root_id=str(data["project_root_id"]),
            project_root_path=project_root_path,
            staging_depth=staging_depth,
            governed_min_depth=governed_min_depth,
            exclusions=exclusions,
            separator=separator,
            python_prefix=python_prefix,
            registry_path=registry_path,
            patch_output_dir=patch_output_dir,
            allocator_store_path=allocator_store_path,
            lock_timeout_ms=lock_timeout_ms,
            contracts_dir=contracts_dir,
            evidence_root=evidence_root,
        )


@dataclass
class IdpkgContracts:
    config_schema: Dict[str, Any]
    dir_id_schema: Dict[str, Any]
    ingest_envelope_schema: Dict[str, Any]
    prefix_policy: Dict[str, Any]
    gate_catalog: Dict[str, Any]
    write_policy: Dict[str, Any]

    @classmethod
    def load(cls, contracts_dir: Path) -> "IdpkgContracts":
        def load_json(path: Path) -> Dict[str, Any]:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        config_schema = load_json(contracts_dir / "IDPKG_CONFIG.schema.json")
        dir_id_schema = load_json(contracts_dir / ".dir_id.schema.json")
        ingest_schema = load_json(contracts_dir / "UNIFIED_INGEST_ENVELOPE.schema.json")
        prefix_policy = load_json(contracts_dir / "PREFIX_POLICY.json")
        gate_catalog = load_json(contracts_dir / "GATE_CATALOG.json")
        write_policy = load_write_policy(contracts_dir / "WRITE_POLICY_IDPKG.yaml")

        return cls(
            config_schema=config_schema,
            dir_id_schema=dir_id_schema,
            ingest_envelope_schema=ingest_schema,
            prefix_policy=prefix_policy,
            gate_catalog=gate_catalog,
            write_policy=write_policy,
        )


def load_write_policy(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current_section: Optional[str] = None
    current_list: Optional[str] = None

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()

            if indent == 0 and stripped.endswith(":"):
                current_section = stripped[:-1]
                data[current_section] = {}
                current_list = None
                continue

            if current_section is None:
                continue

            if indent == 2:
                if stripped.endswith(":"):
                    key = stripped[:-1]
                    data[current_section][key] = []
                    current_list = key
                else:
                    key, value = stripped.split(":", 1)
                    value = value.strip()
                    if value.lower() in {"true", "false"}:
                        parsed: Any = value.lower() == "true"
                    elif value.isdigit():
                        parsed = int(value)
                    else:
                        parsed = value
                    data[current_section][key] = parsed
                    current_list = None
                continue

            if indent >= 4 and stripped.startswith("- ") and current_list:
                item = stripped[2:].strip()
                data[current_section][current_list].append(item)

    return data


class EvidenceWriter:
    def __init__(self, evidence_root: Path, run_id: str):
        self.root = evidence_root / run_id
        self.root.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, payload: Dict[str, Any]) -> Path:
        path = self.root / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path

    def write_event(self, event_id: str, suffix: str, payload: Dict[str, Any]) -> Path:
        filename = f"{event_id}_{suffix}.json"
        return self.write_json(filename, payload)


@dataclass
class FileIdentityResult:
    file_id: Optional[str]
    status: str
    renamed: bool
    original_path: Path
    current_path: Path
    prefix_ok: bool
    prefix_kind: Optional[str]
    error_message: Optional[str] = None


class FileIdentityResolver:
    def __init__(self, separator: str, python_prefix: str):
        self.separator = separator
        self.python_prefix = python_prefix

    def _parse_filename(self, filename: str) -> Tuple[bool, Optional[str], bool, str]:
        prefix = self.python_prefix
        sep = self.separator

        if filename.startswith(prefix):
            rest = filename[len(prefix):]
            if len(rest) >= 20 + len(sep) and rest[:20].isdigit() and rest[20:].startswith(sep):
                file_id = rest[:20]
                base = rest[20 + len(sep):]
                return True, file_id, True, base

        if len(filename) >= 20 + len(sep) and filename[:20].isdigit() and filename[20:].startswith(sep):
            file_id = filename[:20]
            base = filename[20 + len(sep):]
            return True, file_id, False, base

        return False, None, False, filename

    def resolve(self, file_path: Path, allow_allocate: bool, enforce_prefix: bool) -> FileIdentityResult:
        filename = file_path.name
        has_prefix, file_id, has_python_prefix, base_name = self._parse_filename(filename)
        is_python = file_path.suffix.lower() == ".py"

        prefix_ok = False
        rename_needed = False
        prefix_kind: Optional[str] = None

        if has_prefix and file_id:
            if is_python:
                prefix_ok = has_python_prefix
                prefix_kind = "python" if has_python_prefix else "regular"
                if not has_python_prefix:
                    rename_needed = True
            else:
                prefix_ok = not has_python_prefix
                prefix_kind = "regular" if not has_python_prefix else "python"
                if has_python_prefix:
                    rename_needed = True
        else:
            prefix_ok = False
            rename_needed = True

        if not has_prefix:
            if not allow_allocate:
                return FileIdentityResult(
                    file_id=None,
                    status="missing",
                    renamed=False,
                    original_path=file_path,
                    current_path=file_path,
                    prefix_ok=False,
                    prefix_kind=None,
                    error_message="Missing file_id prefix",
                )
            file_id = allocate_file_id(context=str(file_path))

        if rename_needed:
            if not enforce_prefix:
                return FileIdentityResult(
                    file_id=file_id,
                    status="noncanonical",
                    renamed=False,
                    original_path=file_path,
                    current_path=file_path,
                    prefix_ok=False,
                    prefix_kind=prefix_kind,
                    error_message="Prefix requires correction",
                )

            prefix = self.python_prefix if is_python else ""
            new_name = f"{prefix}{file_id}{self.separator}{base_name}"
            new_path = file_path.with_name(new_name)

            if new_path.exists() and new_path != file_path:
                return FileIdentityResult(
                    file_id=file_id,
                    status="error",
                    renamed=False,
                    original_path=file_path,
                    current_path=file_path,
                    prefix_ok=False,
                    prefix_kind=prefix_kind,
                    error_message=f"Target exists: {new_path}",
                )

            try:
                file_path.rename(new_path)
            except OSError as exc:
                return FileIdentityResult(
                    file_id=file_id,
                    status="error",
                    renamed=False,
                    original_path=file_path,
                    current_path=file_path,
                    prefix_ok=False,
                    prefix_kind=prefix_kind,
                    error_message=f"Rename failed: {exc}",
                )

            return FileIdentityResult(
                file_id=file_id,
                status="allocated" if not has_prefix else "renamed",
                renamed=True,
                original_path=file_path,
                current_path=new_path,
                prefix_ok=True,
                prefix_kind="python" if is_python else "regular",
            )

        return FileIdentityResult(
            file_id=file_id,
            status="exists",
            renamed=False,
            original_path=file_path,
            current_path=file_path,
            prefix_ok=prefix_ok,
            prefix_kind=prefix_kind,
        )


@dataclass
class RegistryPatchResult:
    patch_path: Optional[Path]
    operations: List[Dict[str, Any]]
    registry_updated: bool


class RegistryWriter:
    def __init__(self, registry_path: Path, patch_output_dir: Path, write_policy: Dict[str, Any]):
        self.registry_path = registry_path
        self.patch_output_dir = patch_output_dir
        self.write_policy = write_policy
        self.immutable_fields = write_policy.get("registry_write_policy", {}).get("immutable_fields", [])

    def load_registry(self) -> Dict[str, Any]:
        if self.registry_path.exists():
            return atomic_json_read(self.registry_path)
        return {
            "schema_version": "4.0",
            "generated": utc_now(),
            "files": [],
            "entries": [],
            "entities": [],
        }

    def _ensure_registry_shape(self, registry: Dict[str, Any]) -> None:
        if "files" not in registry:
            registry["files"] = []
        if "entries" not in registry:
            registry["entries"] = []
        if "entities" not in registry:
            registry["entities"] = []

    def _apply_patch(self, registry: Dict[str, Any], patch_ops: List[Dict[str, Any]]) -> Dict[str, Any]:
        updated = json.loads(json.dumps(registry))

        for op in patch_ops:
            path = op["path"].strip("/")
            parts = path.split("/") if path else []
            target = updated
            for part in parts[:-1]:
                if part.isdigit():
                    target = target[int(part)]
                else:
                    target = target[part]
            key = parts[-1] if parts else None
            if key is not None and key.isdigit():
                key = int(key)

            if op["op"] == "add":
                if isinstance(target, list) and isinstance(key, int):
                    if key == len(target):
                        target.append(op["value"])
                    else:
                        target.insert(key, op["value"])
                elif key is not None:
                    target[key] = op["value"]
            elif op["op"] == "replace":
                if key is None:
                    updated = op["value"]
                else:
                    target[key] = op["value"]
            elif op["op"] == "remove":
                if isinstance(target, list) and isinstance(key, int):
                    target.pop(key)
                elif key is not None:
                    target.pop(key, None)
            else:
                raise IdpkgError(f"Unsupported patch operation: {op['op']}")

        return updated

    def _write_patch(self, patch_ops: List[Dict[str, Any]], event_id: str) -> Path:
        self.patch_output_dir.mkdir(parents=True, exist_ok=True)
        patch_name = f"idpkg_patch_{event_id}.json"
        patch_path = self.patch_output_dir / patch_name
        with open(patch_path, "w", encoding="utf-8") as f:
            json.dump(patch_ops, f, indent=2)
        return patch_path

    def upsert_directory(self, record: Dict[str, Any], event_id: str, dry_run: bool) -> RegistryPatchResult:
        registry = self.load_registry()
        self._ensure_registry_shape(registry)
        entities = registry["entities"]

        existing_idx = None
        for idx, entity in enumerate(entities):
            if entity.get("entity_kind") == "directory" and entity.get("dir_id") == record.get("dir_id"):
                existing_idx = idx
                break

        patch_ops: List[Dict[str, Any]] = []

        if existing_idx is None:
            patch_ops.append({
                "op": "add",
                "path": f"/entities/{len(entities)}",
                "value": record,
            })
        else:
            existing = entities[existing_idx]
            for key, value in record.items():
                if key in self.immutable_fields and existing.get(key) not in (None, value):
                    raise IdpkgError(f"Immutable field change blocked: {key}")
                if existing.get(key) != value:
                    patch_ops.append({
                        "op": "replace",
                        "path": f"/entities/{existing_idx}/{key}",
                        "value": value,
                    })

        if dry_run or not patch_ops:
            return RegistryPatchResult(patch_path=None, operations=patch_ops, registry_updated=False)

        patch_path = self._write_patch(patch_ops, event_id)
        updated_registry = self._apply_patch(registry, patch_ops)
        atomic_json_write(self.registry_path, updated_registry)

        return RegistryPatchResult(patch_path=patch_path, operations=patch_ops, registry_updated=True)

    def upsert_file(self, record: Dict[str, Any], event_id: str, dry_run: bool) -> RegistryPatchResult:
        registry = self.load_registry()
        self._ensure_registry_shape(registry)
        files = registry["files"]

        existing_idx = None
        for idx, entry in enumerate(files):
            if entry.get("file_id") == record.get("file_id"):
                existing_idx = idx
                break

        if existing_idx is None:
            for idx, entry in enumerate(files):
                if entry.get("relative_path") == record.get("relative_path"):
                    existing_idx = idx
                    break

        patch_ops: List[Dict[str, Any]] = []

        if existing_idx is None:
            patch_ops.append({
                "op": "add",
                "path": f"/files/{len(files)}",
                "value": record,
            })
        else:
            existing = files[existing_idx]
            for key, value in record.items():
                if key in self.immutable_fields and existing.get(key) not in (None, value):
                    raise IdpkgError(f"Immutable field change blocked: {key}")
                if existing.get(key) != value:
                    patch_ops.append({
                        "op": "replace",
                        "path": f"/files/{existing_idx}/{key}",
                        "value": value,
                    })

        if dry_run or not patch_ops:
            return RegistryPatchResult(patch_path=None, operations=patch_ops, registry_updated=False)

        patch_path = self._write_patch(patch_ops, event_id)
        updated_registry = self._apply_patch(registry, patch_ops)
        atomic_json_write(self.registry_path, updated_registry)

        return RegistryPatchResult(patch_path=patch_path, operations=patch_ops, registry_updated=True)


class GateRunner:
    def __init__(self, gate_catalog: Dict[str, Any]):
        self.gates = gate_catalog.get("gates", [])
        self._handlers = {
            "X-G1": self._gate_allocator_outside_root,
            "X-G2": self._gate_allocator_reachable,
            "X-G3": self._gate_patch_only,
            "X-G4": self._gate_staging_no_register,
            "DIR-G1": self._gate_dir_anchor_present,
            "DIR-G2": self._gate_dir_anchor_valid,
            "DIR-G3": self._gate_dir_unique,
            "DIR-G4": self._gate_dir_registry_entry,
            "DIR-G5": self._gate_dir_parent_match,
            "FILE-G1": self._gate_file_prefix,
            "FILE-G2": self._gate_file_python_prefix,
            "FILE-G3": self._gate_file_unique,
            "FILE-G4": self._gate_file_registry_entry,
            "FILE-G5": self._gate_file_owning_dir,
        }

    def run(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        zone = envelope.get("zone")
        entity_kind = envelope.get("entity_kind")

        for gate in self.gates:
            gate_id = gate.get("gate_id")
            applies_zone = gate.get("applies_when", {}).get("zone", "any")
            gate_entity = gate.get("entity_kind", "any")

            if gate_entity not in ("any", entity_kind):
                results.append({"gate_id": gate_id, "status": "SKIP", "message": "Entity mismatch"})
                continue

            if applies_zone != "any" and applies_zone != zone:
                results.append({"gate_id": gate_id, "status": "SKIP", "message": "Zone mismatch"})
                continue

            handler = self._handlers.get(gate_id)
            if not handler:
                results.append({"gate_id": gate_id, "status": "SKIP", "message": "No handler"})
                continue

            passed, message = handler(envelope, context)
            results.append({
                "gate_id": gate_id,
                "status": "PASS" if passed else "FAIL",
                "message": message,
                "defect_code": gate.get("defect_code") if not passed else None,
                "severity": gate.get("severity"),
            })

        return results

    def _gate_allocator_outside_root(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        config: IdpkgConfig = context["config"]
        if is_within(config.allocator_store_path, config.project_root_path):
            return False, "Allocator store is inside project root"
        return True, "Allocator store outside project root"

    def _gate_allocator_reachable(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        config: IdpkgConfig = context["config"]
        try:
            config.allocator_store_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return False, f"Allocator store not reachable: {exc}"
        return True, "Allocator store reachable"

    def _gate_patch_only(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        if context.get("registry_updated") and not context.get("patch_written"):
            return False, "Registry update without patch"
        return True, "Registry patch present"

    def _gate_staging_no_register(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        if envelope.get("trigger_event_kind") == "PROMOTE_REQUESTED":
            return True, "Promotion bypasses staging"
        if context.get("registry_updated"):
            return False, "Staging item was registered"
        return True, "Staging item skipped"

    def _gate_dir_anchor_present(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        return (context.get("dir_anchor") is not None, "Dir anchor present" if context.get("dir_anchor") else "Missing .dir_id")

    def _gate_dir_anchor_valid(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        anchor = context.get("dir_anchor")
        if not anchor:
            return False, "Missing .dir_id"
        errors = context.get("dir_anchor_errors") or []
        if errors:
            return False, "; ".join(errors)
        return True, "Dir anchor valid"

    def _gate_dir_unique(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        registry = context.get("registry") or {}
        dir_id = context.get("dir_id")
        if not dir_id:
            return False, "Missing dir_id"
        duplicates = [
            e for e in registry.get("entities", [])
            if e.get("entity_kind") == "directory" and e.get("dir_id") == dir_id
        ]
        if len(duplicates) > 1:
            return False, "Duplicate dir_id in registry"
        return True, "dir_id unique"

    def _gate_dir_registry_entry(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        registry = context.get("registry") or {}
        dir_id = context.get("dir_id")
        for entity in registry.get("entities", []):
            if entity.get("entity_kind") == "directory" and entity.get("dir_id") == dir_id:
                return True, "Directory record present"
        return False, "Directory record missing"

    def _gate_dir_parent_match(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        depth = context.get("depth", 0)
        if depth < 2:
            return True, "Root-level directory"
        expected = context.get("derived_parent_dir_id")
        actual = context.get("parent_dir_id")
        if expected and actual and expected != actual:
            return False, f"parent_dir_id mismatch: expected {expected}, got {actual}"
        return True, "parent_dir_id matches"

    def _gate_file_prefix(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        result: FileIdentityResult = context.get("file_result")
        if result and result.file_id and result.prefix_ok:
            return True, "File prefix valid"
        return False, "File prefix missing or invalid"

    def _gate_file_python_prefix(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        result: FileIdentityResult = context.get("file_result")
        if not result:
            return False, "Missing file result"
        is_python = result.current_path.suffix.lower() == ".py"
        if not is_python:
            return True, "Non-python file"
        if result.prefix_kind == "python":
            return True, "Python prefix present"
        return False, "Python prefix missing"

    def _gate_file_unique(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        registry = context.get("registry") or {}
        file_id = context.get("file_id")
        if not file_id:
            return False, "Missing file_id"
        duplicates = [
            f for f in registry.get("files", [])
            if f.get("file_id") == file_id
        ]
        if len(duplicates) > 1:
            return False, "Duplicate file_id in registry"
        return True, "file_id unique"

    def _gate_file_registry_entry(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        registry = context.get("registry") or {}
        file_id = context.get("file_id")
        for entry in registry.get("files", []):
            if entry.get("file_id") == file_id:
                return True, "File record present"
        return False, "File record missing"

    def _gate_file_owning_dir(self, envelope: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        expected = context.get("derived_parent_dir_id")
        actual = context.get("owning_dir_id")
        if expected and actual and expected != actual:
            return False, f"owning_dir_id mismatch: expected {expected}, got {actual}"
        if expected and not actual:
            return False, "Missing owning_dir_id"
        return True, "owning_dir_id matches"


class IdpkgEngine:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = REPO_ROOT / ".idpkg" / "config.json"
        self.config = IdpkgConfig.load(config_path)
        self.contracts = IdpkgContracts.load(self.config.contracts_dir)

        self.zone_classifier = ZoneClassifier(exclusions=self.config.exclusions)
        self.dir_manager = DirIdManager()
        self.dir_resolver = DirectoryIdentityResolver(
            project_root=self.config.project_root_path,
            project_root_id=self.config.project_root_id,
            zone_classifier=self.zone_classifier,
            dir_id_manager=self.dir_manager,
        )
        self.file_resolver = FileIdentityResolver(
            separator=self.config.separator,
            python_prefix=self.config.python_prefix,
        )
        self.registry_writer = RegistryWriter(
            registry_path=self.config.registry_path,
            patch_output_dir=self.config.patch_output_dir,
            write_policy=self.contracts.write_policy,
        )
        self.gate_runner = GateRunner(self.contracts.gate_catalog)
        self._validate_config_schema()
        self._validate_prefix_policy()

    def _new_run_id(self) -> str:
        return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")

    def _validate_config_schema(self) -> None:
        schema = self.contracts.config_schema
        with open(self.config.config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for field in schema.get("required", []):
            if field not in cfg:
                raise IdpkgError(f"Config missing required field: {field}")

    def _validate_prefix_policy(self) -> None:
        rules = self.contracts.prefix_policy.get("rules", [])
        python_rule = next((r for r in rules if r.get("match_extension") == "py"), None)
        if python_rule and python_rule.get("prefix") != self.config.python_prefix:
            raise IdpkgError("Config python_prefix does not match PREFIX_POLICY.json")

    def _build_envelope(self, path: Path, trigger_event_kind: str, entity_kind: Optional[str]) -> Dict[str, Any]:
        if trigger_event_kind.startswith("DIR_"):
            entity_kind = "directory"
        elif trigger_event_kind.startswith("FILE_"):
            entity_kind = "file"
        elif trigger_event_kind == "PROMOTE_REQUESTED" and entity_kind is None:
            entity_kind = "directory" if path.is_dir() else "file"

        if entity_kind not in ("file", "directory"):
            raise IdpkgError(f"Invalid entity kind for event {trigger_event_kind}")

        relative_path = normalize_relative_path(path, self.config.project_root_path)
        depth = self.zone_classifier.compute_depth(relative_path)
        zone = self.zone_classifier.compute_zone(relative_path, depth)

        envelope = {
            "trigger_event_kind": trigger_event_kind,
            "entity_kind": entity_kind,
            "observed_at_utc": utc_now(),
            "project_root_id": self.config.project_root_id,
            "project_root_path": str(self.config.project_root_path),
            "relative_path": relative_path,
            "depth": depth,
            "zone": zone,
        }

        self._validate_envelope(envelope)
        return envelope

    def _validate_envelope(self, envelope: Dict[str, Any]) -> None:
        schema = self.contracts.ingest_envelope_schema
        for field in schema.get("required", []):
            if field not in envelope:
                raise IdpkgError(f"Ingest envelope missing field: {field}")

        trigger_enum = schema.get("properties", {}).get("trigger_event_kind", {}).get("enum", [])
        if trigger_enum and envelope.get("trigger_event_kind") not in trigger_enum:
            raise IdpkgError(f"Invalid trigger_event_kind: {envelope.get('trigger_event_kind')}")

        entity_enum = schema.get("properties", {}).get("entity_kind", {}).get("enum", [])
        if entity_enum and envelope.get("entity_kind") not in entity_enum:
            raise IdpkgError(f"Invalid entity_kind: {envelope.get('entity_kind')}")

    def _validate_dir_anchor(self, anchor: Optional[Any]) -> List[str]:
        if not anchor:
            return ["Missing .dir_id"]

        payload = anchor.to_dict() if hasattr(anchor, "to_dict") else anchor
        schema = self.contracts.dir_id_schema
        errors: List[str] = []

        for field in schema.get("required", []):
            if field not in payload or payload.get(field) in ("", None):
                errors.append(f"{field} is required")

        dir_id = payload.get("dir_id")
        pattern = schema.get("properties", {}).get("dir_id", {}).get("pattern")
        if pattern and dir_id and not re.match(pattern, dir_id):
            errors.append("dir_id does not match schema pattern")

        allocated_at = payload.get("allocated_at_utc")
        if allocated_at:
            try:
                datetime.fromisoformat(allocated_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append("allocated_at_utc is not valid ISO 8601")

        return errors

    def _derive_parent_dir_id(self, directory: Path) -> Optional[str]:
        parent = directory.parent
        while True:
            anchor = self.dir_manager.read_dir_id(parent)
            if anchor:
                return anchor.dir_id
            if parent == self.config.project_root_path or parent == parent.parent:
                break
            parent = parent.parent
        return None

    def _directory_record(self, envelope: Dict[str, Any], anchor: Optional[Any], parent_dir_id: Optional[str]) -> Dict[str, Any]:
        record = {
            "record_kind": "entity",
            "entity_kind": "directory",
            "dir_id": anchor.dir_id if anchor else None,
            "relative_path": envelope["relative_path"],
            "project_root_id": self.config.project_root_id,
            "depth": envelope["depth"],
            "zone": envelope["zone"],
            "parent_dir_id": parent_dir_id,
            "allocated_at_utc": anchor.allocated_at_utc if anchor else None,
            "allocator_version": anchor.allocator_version if anchor else None,
            "updated_utc": utc_now(),
            "tool_version": IDPKG_TOOL_VERSION,
        }
        return record

    def _file_record(self, envelope: Dict[str, Any], file_path: Path, file_id: str, owning_dir_id: Optional[str]) -> Dict[str, Any]:
        return {
            "file_id": file_id,
            "relative_path": envelope["relative_path"],
            "filename": file_path.name,
            "extension": file_path.suffix.lstrip("."),
            "repo_root_id": self.config.project_root_id,
            "record_kind": "entity",
            "dir_id": owning_dir_id,
            "owning_dir_id": owning_dir_id,
            "depth": envelope["depth"],
            "zone": envelope["zone"],
            "created_utc": utc_now(),
            "updated_utc": utc_now(),
            "tool_version": IDPKG_TOOL_VERSION,
        }

    def ingest_event(
        self,
        path: Path,
        trigger_event_kind: str,
        entity_kind: Optional[str] = None,
        repair: bool = False,
        dry_run: bool = False,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        run_id = run_id or self._new_run_id()
        evidence = EvidenceWriter(self.config.evidence_root, run_id)
        envelope = self._build_envelope(path, trigger_event_kind, entity_kind)
        event_id = safe_slug(f"{trigger_event_kind}_{envelope['relative_path']}")

        evidence.write_event(event_id, "ingest_event", envelope)

        zone = envelope["zone"]
        is_promotion = trigger_event_kind == "PROMOTE_REQUESTED"
        if zone == "excluded":
            gate_results = self.gate_runner.run(envelope, {"config": self.config})
            evidence.write_event(event_id, "gate_report", {"results": gate_results})
            return {"status": "skipped", "reason": "excluded", "run_id": run_id}

        if zone == "staging" and not is_promotion:
            gate_results = self.gate_runner.run(envelope, {"config": self.config, "registry_updated": False})
            evidence.write_event(event_id, "gate_report", {"results": gate_results})
            return {"status": "skipped", "reason": "staging", "run_id": run_id}

        registry_updated = False
        patch_written = False
        allocation_performed = False
        record = None
        registry_snapshot = None
        file_result: Optional[FileIdentityResult] = None
        dir_anchor = None
        parent_dir_id = None
        derived_parent_dir_id = None

        if envelope["entity_kind"] == "directory":
            allocate = repair or is_promotion or trigger_event_kind in {"DIR_CREATED", "DIR_MOVED"}
            result = self.dir_resolver.resolve_identity(path, allocate_if_missing=allocate)
            dir_anchor = result.anchor
            allocation_performed = result.status == "allocated"
            if dir_anchor:
                evidence.write_event(event_id, "dir_anchor", dir_anchor.to_dict())
            if allocation_performed:
                evidence.write_event(event_id, "allocator_allocation", {
                    "entity_kind": "directory",
                    "dir_id": result.dir_id,
                    "relative_path": envelope["relative_path"],
                })
            parent_dir_id = dir_anchor.parent_dir_id if dir_anchor else None
            derived_parent_dir_id = self._derive_parent_dir_id(path)
            record = self._directory_record(envelope, dir_anchor, parent_dir_id)
            patch_result = self.registry_writer.upsert_directory(record, event_id, dry_run)
        else:
            if envelope["entity_kind"] == "file":
                parent_dir = path.parent
                if zone == "governed" or is_promotion:
                    self.dir_resolver.resolve_identity(parent_dir, allocate_if_missing=True)
                derived_parent_dir_id = self._derive_parent_dir_id(parent_dir)
                file_result = self.file_resolver.resolve(
                    path,
                    allow_allocate=repair or is_promotion or trigger_event_kind in {"FILE_CREATED", "FILE_MOVED"},
                    enforce_prefix=repair or is_promotion or trigger_event_kind in {"FILE_CREATED", "FILE_MOVED"},
                )
                if file_result.renamed:
                    evidence.write_event(event_id, "rename_action", {
                        "from": str(file_result.original_path),
                        "to": str(file_result.current_path),
                        "file_id": file_result.file_id,
                    })
                if file_result.file_id:
                    allocation_performed = file_result.status == "allocated"
                    if allocation_performed:
                        evidence.write_event(event_id, "allocator_allocation", {
                            "entity_kind": "file",
                            "file_id": file_result.file_id,
                            "relative_path": envelope["relative_path"],
                        })
                    record = self._file_record(envelope, file_result.current_path, file_result.file_id, derived_parent_dir_id)
                    patch_result = self.registry_writer.upsert_file(record, event_id, dry_run)
                else:
                    patch_result = RegistryPatchResult(patch_path=None, operations=[], registry_updated=False)
            else:
                raise IdpkgError("Unsupported entity kind")

        registry_updated = patch_result.registry_updated if patch_result else False
        patch_written = patch_result.patch_path is not None if patch_result else False

        if patch_result and patch_result.patch_path:
            evidence.write_event(event_id, "registry_patch", {
                "patch_path": str(patch_result.patch_path),
                "operations": patch_result.operations,
            })

        if record and not dry_run:
            registry_snapshot = self.registry_writer.load_registry()

        anchor_errors = self._validate_dir_anchor(dir_anchor) if dir_anchor else []

        gate_context = {
            "config": self.config,
            "registry_updated": registry_updated,
            "patch_written": patch_written,
            "allocation_performed": allocation_performed,
            "registry": registry_snapshot,
            "dir_anchor": dir_anchor,
            "dir_anchor_errors": anchor_errors,
            "dir_id": record.get("dir_id") if record else None,
            "depth": envelope["depth"],
            "parent_dir_id": parent_dir_id,
            "derived_parent_dir_id": derived_parent_dir_id,
            "file_result": file_result,
            "file_id": record.get("file_id") if record else None,
            "owning_dir_id": record.get("owning_dir_id") if record else None,
        }

        gate_results = self.gate_runner.run(envelope, gate_context)
        evidence.write_event(event_id, "gate_report", {"results": gate_results})

        return {
            "status": "ok" if not any(r["status"] == "FAIL" and r.get("severity") == "BLOCK" for r in gate_results) else "failed",
            "run_id": run_id,
            "event_id": event_id,
            "registry_updated": registry_updated,
            "patch_path": str(patch_result.patch_path) if patch_result and patch_result.patch_path else None,
        }

    def scan(self, repair: bool) -> Dict[str, Any]:
        run_id = self._new_run_id()
        directories_scanned = 0
        files_scanned = 0
        failures = 0

        for directory in self._walk_directories():
            directories_scanned += 1
            result = self.ingest_event(directory, "DIR_CREATED", repair=repair, dry_run=not repair, run_id=run_id)
            if result.get("status") == "failed":
                failures += 1

        for file_path in self._walk_files():
            files_scanned += 1
            result = self.ingest_event(file_path, "FILE_CREATED", repair=repair, dry_run=not repair, run_id=run_id)
            if result.get("status") == "failed":
                failures += 1

        return {
            "run_id": run_id,
            "directories_scanned": directories_scanned,
            "files_scanned": files_scanned,
            "failures": failures,
            "mode": "fix" if repair else "report",
        }

    def promote(self, target: Path, repair: bool = True) -> Dict[str, Any]:
        run_id = self._new_run_id()
        failures = 0

        if target.is_dir():
            for directory in self._walk_directories(root=target):
                result = self.ingest_event(directory, "PROMOTE_REQUESTED", repair=repair, dry_run=not repair, run_id=run_id)
                if result.get("status") == "failed":
                    failures += 1
            for file_path in self._walk_files(root=target):
                result = self.ingest_event(file_path, "PROMOTE_REQUESTED", repair=repair, dry_run=not repair, run_id=run_id)
                if result.get("status") == "failed":
                    failures += 1
        else:
            result = self.ingest_event(target, "PROMOTE_REQUESTED", repair=repair, dry_run=not repair, run_id=run_id)
            if result.get("status") == "failed":
                failures += 1

        return {"run_id": run_id, "failures": failures}

    def watch(self, interval: float = 2.0) -> None:
        snapshot = self._snapshot_tree()
        print("IDPKG watch started. Press Ctrl+C to stop.")
        while True:
            time.sleep(interval)
            next_snapshot = self._snapshot_tree()
            self._process_snapshot_changes(snapshot, next_snapshot)
            snapshot = next_snapshot

    def verify(self) -> Dict[str, Any]:
        test_root = self.config.project_root_path / "idpkg_verify_tmp"
        test_root.mkdir(parents=True, exist_ok=True)
        (test_root / "src").mkdir(parents=True, exist_ok=True)
        test_file = test_root / "src" / "verify_sample.py"
        test_file.write_text("print('verify')\n", encoding="utf-8")

        results = []
        results.append(self.ingest_event(test_root / "src", "DIR_CREATED", repair=True))
        results.append(self.ingest_event(test_file, "FILE_CREATED", repair=True))

        zone_root = self.zone_classifier.compute_zone(".", 0)
        zone_src = self.zone_classifier.compute_zone("idpkg_verify_tmp/src", 2)
        anchor = self.dir_manager.read_dir_id(test_root / "src")
        anchor_errors = self._validate_dir_anchor(anchor) if anchor else ["Missing .dir_id"]
        patch_files = list(self.config.patch_output_dir.glob("idpkg_patch_*.json"))

        return {
            "status": "ok" if all(r.get("status") == "ok" for r in results) else "failed",
            "events": results,
            "verify_root": str(test_root),
            "zone_checks": {"root": zone_root, "src": zone_src},
            "dir_anchor_errors": anchor_errors,
            "patch_files": [str(p) for p in patch_files[:5]],
        }

    def _walk_directories(self, root: Optional[Path] = None) -> Iterable[Path]:
        root = root or self.config.project_root_path
        for entry in root.rglob("*"):
            if entry.is_dir():
                rel = normalize_relative_path(entry, self.config.project_root_path)
                if self.zone_classifier.should_skip(rel):
                    continue
                yield entry

    def _walk_files(self, root: Optional[Path] = None) -> Iterable[Path]:
        root = root or self.config.project_root_path
        for entry in root.rglob("*"):
            if entry.is_file():
                if entry.name == ".dir_id":
                    continue
                rel = normalize_relative_path(entry, self.config.project_root_path)
                if self.zone_classifier.should_skip(rel):
                    continue
                yield entry

    def _snapshot_tree(self) -> Dict[str, Tuple[bool, float]]:
        snapshot: Dict[str, Tuple[bool, float]] = {}
        for path in self.config.project_root_path.rglob("*"):
            rel = normalize_relative_path(path, self.config.project_root_path)
            if self.zone_classifier.should_skip(rel):
                continue
            try:
                snapshot[rel] = (path.is_dir(), path.stat().st_mtime)
            except FileNotFoundError:
                continue
        return snapshot

    def _process_snapshot_changes(self, previous: Dict[str, Tuple[bool, float]], current: Dict[str, Tuple[bool, float]]) -> None:
        previous_paths = set(previous.keys())
        current_paths = set(current.keys())

        added = current_paths - previous_paths
        removed = previous_paths - current_paths
        common = previous_paths & current_paths

        for rel in added:
            is_dir = current[rel][0]
            abs_path = self.config.project_root_path / rel
            event = "DIR_CREATED" if is_dir else "FILE_CREATED"
            self.ingest_event(abs_path, event, repair=True)

        for rel in removed:
            is_dir = previous[rel][0]
            abs_path = self.config.project_root_path / rel
            event = "DIR_DELETED" if is_dir else "FILE_DELETED"
            self.ingest_event(abs_path, event, repair=True)

        for rel in common:
            is_dir, mtime = current[rel]
            prev_mtime = previous[rel][1]
            if not is_dir and mtime != prev_mtime:
                abs_path = self.config.project_root_path / rel
                self.ingest_event(abs_path, "FILE_MODIFIED", repair=True)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="IDPKG CLI")
    parser.add_argument("--config", type=Path, help="Path to .idpkg/config.json")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Validate config and contracts")

    scan_parser = subparsers.add_parser("scan", help="Scan for IDPKG compliance")
    scan_parser.add_argument("--fix", action="store_true", help="Apply fixes during scan")

    watch_parser = subparsers.add_parser("watch", help="Watch filesystem for changes")
    watch_parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")

    promote_parser = subparsers.add_parser("promote", help="Promote staging path into governed handling")
    promote_parser.add_argument("path", type=Path, help="Target file or directory")

    subparsers.add_parser("verify", help="Verify IDPKG system")

    args = parser.parse_args(argv)
    engine = IdpkgEngine(args.config)

    if args.command == "init":
        print(f"Config loaded: {engine.config.config_path}")
        print(f"Contracts loaded: {engine.config.contracts_dir}")
        return 0

    if args.command == "scan":
        report = engine.scan(repair=args.fix)
        print(json.dumps(report, indent=2))
        return 0 if report["failures"] == 0 else 1

    if args.command == "watch":
        engine.watch(interval=args.interval)
        return 0

    if args.command == "promote":
        result = engine.promote(args.path)
        print(json.dumps(result, indent=2))
        return 0 if result["failures"] == 0 else 1

    if args.command == "verify":
        result = engine.verify()
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "ok" else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
