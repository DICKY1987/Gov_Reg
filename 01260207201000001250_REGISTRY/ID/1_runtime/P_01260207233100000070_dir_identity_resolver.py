from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sys

MODULE_DIR = Path(__file__).resolve().parent
ALLOCATORS_DIR = MODULE_DIR / "allocators"

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(ALLOCATORS_DIR) not in sys.path:
    sys.path.insert(0, str(ALLOCATORS_DIR))

from P_01260207233100000068_zone_classifier import ZoneClassifier, compute_depth
from P_01260207233100000069_dir_id_handler import DirIdAnchor, DirIdManager, create_anchor
from P_01999000042260125006_id_allocator_facade import allocate_dir_id


@dataclass
class IdentityResolutionResult:
    dir_id: Optional[str]
    status: str
    anchor: Optional[DirIdAnchor]
    zone: str
    depth: int
    needs_allocation: bool
    error_message: Optional[str] = None


class DirectoryIdentityResolver:
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        zone_classifier: ZoneClassifier | None = None,
        dir_id_manager: DirIdManager | None = None,
    ):
        self.project_root = project_root.resolve()
        self.project_root_id = project_root_id
        self.zone_classifier = zone_classifier or ZoneClassifier(project_root=self.project_root)
        self.dir_id_manager = dir_id_manager or DirIdManager(project_root=self.project_root)

    def resolve_identity(self, directory: Path, allocate_if_missing: bool = False) -> IdentityResolutionResult:
        directory = directory.resolve()
        try:
            relative_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=None,
                zone="unknown",
                depth=-1,
                needs_allocation=False,
                error_message=f"Directory {directory} not under project root {self.project_root}",
            )

        if relative_path in {"", "."}:
            relative_path = "."

        depth = compute_depth(relative_path)
        zone = self.zone_classifier.compute_zone(relative_path, depth)

        try:
            anchor = self.dir_id_manager.read_dir_id(directory)
        except ValueError as exc:
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=None,
                zone=zone,
                depth=depth,
                needs_allocation=(zone == "governed"),
                error_message=str(exc),
            )

        if anchor is not None:
            is_valid, errors = self.dir_id_manager.validate_dir_id(directory)
            if is_valid:
                return IdentityResolutionResult(
                    dir_id=anchor.dir_id,
                    status="exists",
                    anchor=anchor,
                    zone=zone,
                    depth=depth,
                    needs_allocation=False,
                )
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=anchor,
                zone=zone,
                depth=depth,
                needs_allocation=True,
                error_message="; ".join(errors),
            )

        if zone != "governed":
            return IdentityResolutionResult(
                dir_id=None,
                status="skipped",
                anchor=None,
                zone=zone,
                depth=depth,
                needs_allocation=False,
            )

        if not allocate_if_missing:
            return IdentityResolutionResult(
                dir_id=None,
                status="missing",
                anchor=None,
                zone=zone,
                depth=depth,
                needs_allocation=True,
            )

        try:
            dir_id, _metadata = allocate_dir_id(
                relative_path=relative_path,
                context=f"resolve:{relative_path}",
            )
            new_anchor = create_anchor(
                dir_id=dir_id,
                relative_path=relative_path,
                project_root_id=self.project_root_id,
                depth=depth,
                zone=zone,
                parent_dir_id=self._find_parent_dir_id(directory),
                created_by="resolver",
            )
            self.dir_id_manager.write_dir_id(directory, new_anchor)
        except Exception as exc:
            return IdentityResolutionResult(
                dir_id=None,
                status="error",
                anchor=None,
                zone=zone,
                depth=depth,
                needs_allocation=True,
                error_message=f"Allocation failed: {exc}",
            )

        return IdentityResolutionResult(
            dir_id=dir_id,
            status="allocated",
            anchor=new_anchor,
            zone=zone,
            depth=depth,
            needs_allocation=False,
        )

    def _find_parent_dir_id(self, directory: Path) -> Optional[str]:
        parent = directory.parent
        while True:
            anchor = self.dir_id_manager.read_dir_id(parent)
            if anchor is not None:
                return anchor.dir_id
            if parent == self.project_root or parent == parent.parent:
                break
            parent = parent.parent
        return None

    def allocate_new_id(self, directory: Path) -> IdentityResolutionResult:
        return self.resolve_identity(directory, allocate_if_missing=True)
