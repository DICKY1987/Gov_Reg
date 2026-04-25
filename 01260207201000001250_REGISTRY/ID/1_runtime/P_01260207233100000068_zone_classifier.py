from __future__ import annotations

from pathlib import Path
from typing import Iterable
import sys

MODULE_DIR = Path(__file__).resolve().parent
VALIDATORS_DIR = MODULE_DIR / "validators"

if str(VALIDATORS_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_DIR))

from P_01999000042260125067_zone_classifier import (  # type: ignore[import-not-found]
    DEFAULT_EXCLUSIONS,
    ZoneClassifier as _CoreZoneClassifier,
    compute_depth as _core_compute_depth,
    compute_zone as _core_compute_zone,
)


def _relative_string(path_like: str | Path, project_root: Path | None) -> str:
    if isinstance(path_like, Path):
        if path_like.is_absolute() and project_root is not None:
            try:
                path_like = path_like.resolve().relative_to(project_root.resolve())
            except ValueError:
                path_like = path_like.resolve()
        value = str(path_like)
    else:
        value = path_like

    value = value.replace("\\", "/").strip()
    if value in {"", ".", "/"}:
        return "."
    return value.strip("/")


def compute_depth(relative_path: str | Path) -> int:
    return _core_compute_depth(_relative_string(relative_path, None))


def compute_zone(
    path_or_depth: str | Path | int,
    relative_path: str | Path | int | None = None,
    exclusions: Iterable[str] | None = None,
    project_root: Path | None = None,
) -> str:
    if isinstance(path_or_depth, int):
        depth = path_or_depth
        rel = _relative_string(relative_path if relative_path is not None else ".", project_root)
    else:
        rel = _relative_string(path_or_depth, project_root)
        depth = relative_path if isinstance(relative_path, int) else _core_compute_depth(rel)
    return _core_compute_zone(depth, rel, list(exclusions) if exclusions is not None else None)


class ZoneClassifier:
    def __init__(self, project_root: Path | None = None, exclusions: list[str] | None = None):
        self.project_root = (project_root or Path.cwd()).resolve()
        self.exclusions = exclusions if exclusions is not None else list(DEFAULT_EXCLUSIONS)
        self._delegate = _CoreZoneClassifier(self.project_root, self.exclusions)

    def compute_depth(self, relative_path: str | Path) -> int:
        return compute_depth(relative_path)

    def compute_zone(self, relative_path: str | Path, depth: int | None = None) -> str:
        return compute_zone(relative_path, depth, self.exclusions, self.project_root)

    def should_skip(self, relative_path: str | Path) -> bool:
        return self.compute_zone(relative_path) == "excluded"

    def classify_path(self, abs_path: Path) -> tuple[int, str]:
        if not abs_path.is_absolute():
            abs_path = (self.project_root / abs_path).resolve()
        return self._delegate.classify_path(abs_path)

    def is_governed(self, abs_path: Path) -> bool:
        return self.classify_path(abs_path)[1] == "governed"

    def is_excluded(self, abs_path: Path) -> bool:
        return self.classify_path(abs_path)[1] == "excluded"

    def is_staging(self, abs_path: Path) -> bool:
        return self.classify_path(abs_path)[1] == "staging"
