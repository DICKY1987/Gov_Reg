"""Import call graph builder."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


class CallGraphBuilder:
    """Build import graph: module -> set of importers."""

    def __init__(self, repo_root: Path, inventory: Iterable[dict]):
        self.repo_root = repo_root
        self.inventory = list(inventory)
        self._path_index = {rec["path"]: rec for rec in self.inventory}
        self._module_index = self._build_module_index()

    def build(self) -> Dict[str, Set[str]]:
        graph: Dict[str, Set[str]] = defaultdict(set)
        for record in self.inventory:
            imports = record.get("imports") or []
            importer_path = record.get("path")
            if not importer_path:
                continue
            for imp in imports:
                imported_path = self._resolve_import_to_path(imp, importer_path)
                if imported_path:
                    graph[imported_path].add(importer_path)
        return graph

    def _build_module_index(self) -> Dict[str, str]:
        module_index: Dict[str, str] = {}
        for record in self.inventory:
            path = record.get("path")
            if not path or not path.endswith(".py"):
                continue
            rel_path = Path(path)
            module_name = self._module_name_from_path(rel_path)
            if module_name:
                module_index[module_name] = path
        return module_index

    def _module_name_from_path(self, rel_path: Path) -> Optional[str]:
        parts = list(rel_path.parts)
        if not parts:
            return None
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        if not parts:
            return None
        return ".".join(parts)

    def _resolve_import_to_path(self, imp: dict, importer_path: str) -> Optional[str]:
        module = imp.get("module") or ""
        level = int(imp.get("level", 0) or 0)
        if level > 0:
            importer_dir = Path(importer_path).parent
            base = importer_dir
            for _ in range(level - 1):
                base = base.parent
            if module:
                base = base / module.replace(".", "/")
            rel = self._resolve_module_path(base)
            if rel:
                return rel
            return None
        if module in self._module_index:
            return self._module_index[module]
        module_path = Path(module.replace(".", "/"))
        rel = self._resolve_module_path(module_path)
        return rel

    def _resolve_module_path(self, module_path: Path) -> Optional[str]:
        py_path = module_path.with_suffix(".py")
        init_path = module_path / "__init__.py"
        if str(py_path) in self._path_index:
            return str(py_path)
        if str(init_path) in self._path_index:
            return str(init_path)
        if (self.repo_root / py_path).exists():
            return str(py_path)
        if (self.repo_root / init_path).exists():
            return str(init_path)
        return None
