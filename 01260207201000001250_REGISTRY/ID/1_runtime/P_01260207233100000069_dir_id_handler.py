from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json
import re

ID_PATTERN = re.compile(r"^\d{20}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class DirIdAnchor:
    dir_id: str
    allocator_version: str
    allocated_at_utc: str
    project_root_id: str
    relative_path: str
    depth: Optional[int] = None
    zone: Optional[str] = None
    parent_dir_id: Optional[str] = None
    created_by: Optional[str] = None
    canonicality_law_version: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    extra_fields: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not ID_PATTERN.match(self.dir_id):
            raise ValueError(f"Invalid dir_id format: {self.dir_id}")
        if not ID_PATTERN.match(self.project_root_id):
            raise ValueError(f"Invalid project_root_id format: {self.project_root_id}")
        datetime.fromisoformat(self.allocated_at_utc.replace("Z", "+00:00"))
        if self.parent_dir_id is not None and not ID_PATTERN.match(self.parent_dir_id):
            raise ValueError(f"Invalid parent_dir_id format: {self.parent_dir_id}")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dir_id": self.dir_id,
            "allocator_version": self.allocator_version,
            "allocated_at_utc": self.allocated_at_utc,
            "project_root_id": self.project_root_id,
            "relative_path": self.relative_path,
        }
        optional_fields = (
            "depth",
            "zone",
            "parent_dir_id",
            "created_by",
            "canonicality_law_version",
            "metadata",
            "notes",
        )
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                payload[field_name] = value
        payload.update(self.extra_fields)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DirIdAnchor":
        required = {
            "dir_id",
            "allocator_version",
            "allocated_at_utc",
            "project_root_id",
            "relative_path",
        }
        missing = [field_name for field_name in required if field_name not in payload]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(sorted(missing))}")

        known = {
            "dir_id",
            "allocator_version",
            "allocated_at_utc",
            "project_root_id",
            "relative_path",
            "depth",
            "zone",
            "parent_dir_id",
            "created_by",
            "canonicality_law_version",
            "metadata",
            "notes",
        }
        extra_fields = {key: value for key, value in payload.items() if key not in known}

        return cls(
            dir_id=str(payload["dir_id"]),
            allocator_version=str(payload["allocator_version"]),
            allocated_at_utc=str(payload["allocated_at_utc"]),
            project_root_id=str(payload["project_root_id"]),
            relative_path=str(payload["relative_path"]),
            depth=payload.get("depth"),
            zone=payload.get("zone"),
            parent_dir_id=payload.get("parent_dir_id"),
            created_by=payload.get("created_by"),
            canonicality_law_version=payload.get("canonicality_law_version"),
            metadata=payload.get("metadata"),
            notes=payload.get("notes"),
            extra_fields=extra_fields,
        )


class DirIdManager:
    DIR_ID_FILENAME = ".dir_id"

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root.resolve() if project_root is not None else None

    def get_dir_id_path(self, directory: Path) -> Path:
        return Path(directory) / self.DIR_ID_FILENAME

    def exists(self, directory: Path) -> bool:
        return self.get_dir_id_path(directory).is_file()

    def read_dir_id(self, directory: Path) -> Optional[DirIdAnchor]:
        path = self.get_dir_id_path(directory)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in .dir_id: {exc}") from exc
        return DirIdAnchor.from_dict(payload)

    def write_dir_id(self, directory: Path, anchor: DirIdAnchor, overwrite: bool = False) -> None:
        path = self.get_dir_id_path(directory)
        if path.exists() and not overwrite:
            raise FileExistsError(f".dir_id already exists at {path}")

        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(".dir_id.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(anchor.to_dict(), handle, indent=2)
                handle.write("\n")
            temp_path.replace(path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def validate_dir_id(self, target: Path | DirIdAnchor) -> tuple[bool, list[str]]:
        errors: list[str] = []
        directory: Path | None = None

        if isinstance(target, Path):
            directory = target
            try:
                anchor = self.read_dir_id(target)
            except ValueError as exc:
                return False, [str(exc)]
            if anchor is None:
                return False, ["Missing .dir_id file"]
        else:
            anchor = target

        if not ID_PATTERN.match(anchor.dir_id):
            errors.append("dir_id must be a 20-digit numeric value")
        if not ID_PATTERN.match(anchor.project_root_id):
            errors.append("project_root_id must be a 20-digit numeric value")
        try:
            datetime.fromisoformat(anchor.allocated_at_utc.replace("Z", "+00:00"))
        except ValueError:
            errors.append("allocated_at_utc is not valid ISO 8601")

        if self.project_root is not None and directory is not None:
            try:
                actual_relative = str(directory.resolve().relative_to(self.project_root)).replace("\\", "/")
            except ValueError:
                errors.append(f"Directory {directory} is not under project root {self.project_root}")
            else:
                if actual_relative in {"", "."}:
                    actual_relative = "."
                if anchor.relative_path != actual_relative:
                    errors.append(
                        f"relative_path mismatch: .dir_id says '{anchor.relative_path}' but actual is '{actual_relative}'"
                    )

        return len(errors) == 0, errors

    def create_anchor(
        self,
        dir_id: str,
        relative_path: str,
        project_root_id: str,
        allocator_version: str = "1.0.0",
        depth: Optional[int] = None,
        zone: Optional[str] = None,
        parent_dir_id: Optional[str] = None,
        created_by: Optional[str] = None,
        canonicality_law_version: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> DirIdAnchor:
        return create_anchor(
            dir_id=dir_id,
            relative_path=relative_path,
            project_root_id=project_root_id,
            allocator_version=allocator_version,
            depth=depth,
            zone=zone,
            parent_dir_id=parent_dir_id,
            created_by=created_by,
            canonicality_law_version=canonicality_law_version,
            metadata=metadata,
            notes=notes,
        )


def create_anchor(
    dir_id: str,
    relative_path: str,
    project_root_id: str,
    allocator_version: str = "1.0.0",
    depth: Optional[int] = None,
    zone: Optional[str] = None,
    parent_dir_id: Optional[str] = None,
    created_by: Optional[str] = None,
    canonicality_law_version: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    notes: Optional[str] = None,
) -> DirIdAnchor:
    return DirIdAnchor(
        dir_id=dir_id,
        allocator_version=allocator_version,
        allocated_at_utc=_utc_now(),
        project_root_id=project_root_id,
        relative_path=relative_path,
        depth=depth,
        zone=zone,
        parent_dir_id=parent_dir_id,
        created_by=created_by,
        canonicality_law_version=canonicality_law_version,
        metadata=metadata,
        notes=notes,
    )
