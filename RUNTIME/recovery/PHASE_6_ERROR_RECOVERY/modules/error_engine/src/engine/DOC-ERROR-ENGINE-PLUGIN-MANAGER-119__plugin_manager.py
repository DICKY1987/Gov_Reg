# DOC_LINK: DOC-ERROR-ENGINE-PLUGIN-MANAGER-119
"""Plugin discovery and execution implementation (minimal, deterministic).

Discovers plugins under `src/plugins/*/` that contain a `manifest.json` and
`plugin.py` exposing a `register()` function returning a `BasePlugin` instance.
"""
# DOC_ID: DOC-ERROR-ENGINE-PLUGIN-MANAGER-119
from __future__ import annotations

import importlib.util
import json
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from phase6_error_recovery.modules.error_engine.src.shared.utils.types import PluginManifest, PluginResult


class PluginManager:
    """Loads plugins from the ``src/plugins`` package and prepares them for use."""

    def __init__(self, plugins_path: Optional[Path] = None) -> None:
        # Default to error/plugins/ unless overridden
        import os
        default_path = Path(__file__).parent.parent / "plugins"
        env_path = os.getenv("PIPELINE_ERROR_PLUGINS_PATH")
        self._plugins_path = plugins_path or (Path(env_path) if env_path else default_path)
        self._plugins: Dict[str, BasePlugin] = {}

    def discover(self) -> None:
        """Search the plugins directory and register available plugins."""
        self._plugins.clear()
        if not self._plugins_path.exists():
            return
        for plugin_dir in sorted(self._plugins_path.iterdir()):
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / "manifest.json"
            plugin_py = plugin_dir / "plugin.py"
            if not (manifest_path.exists() and plugin_py.exists()):
                continue
            try:
                plugin = self._load_plugin(manifest_path)
                if plugin.check_tool_available():
                    self._plugins[plugin.plugin_id] = plugin
            except Exception:
                # Skip broken plugins; deterministic behavior prefers partial availability
                continue

    def get_plugins_for_file(self, file_path: Path) -> List["BasePlugin"]:
        """Return plugins applicable to the supplied file path in DAG order."""
        ext = file_path.suffix.lower().lstrip(".")
        applicable: List[BasePlugin] = []
        for p in self._plugins.values():
            exts = [e.lower().lstrip(".") for e in p.manifest.get("file_extensions", [])]
            if not exts or ext in exts:
                applicable.append(p)

        # Build dependency graph among applicable plugins
        id_set = {p.plugin_id for p in applicable}
        graph: Dict[str, List[str]] = {}
        for p in applicable:
            deps = [d for d in p.manifest.get("requires", []) if d in id_set]
            graph[p.plugin_id] = deps
        try:
            order_ids = list(TopologicalSorter(graph).static_order())
        except Exception:
            # Fallback: stable name sort if graph invalid
            order_ids = sorted(id_set)

        # Map to plugin instances in that order
        ordered = [self._plugins[pid] for pid in order_ids if pid in self._plugins]
        return ordered

    def _load_plugin(self, manifest_path: Path) -> "BasePlugin":
        """Load a plugin using its manifest definition."""
        plugin_dir = manifest_path.parent
        manifest: PluginManifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        plugin_py = plugin_dir / "plugin.py"
        mod_name = f"plugins.{plugin_dir.name}.plugin"
        spec = importlib.util.spec_from_file_location(mod_name, str(plugin_py))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to load plugin module: {plugin_py}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        if not hasattr(module, "register"):
            raise RuntimeError(f"Plugin missing register(): {plugin_py}")
        plugin: BasePlugin = module.register()
        plugin.manifest = manifest
        plugin.plugin_id = manifest.get("plugin_id", getattr(plugin, "plugin_id", plugin_dir.name))
        plugin.name = manifest.get("name", getattr(plugin, "name", plugin_dir.name))
        return plugin

    def run_plugins(self, plugins: Iterable["BasePlugin"], file_path: Path) -> List[PluginResult]:
        """Execute the provided plugins sequentially."""
        results: List[PluginResult] = []
        for p in plugins:
            try:
                res = p.execute(file_path)
            except Exception as exc:  # plugin failure becomes a failed result
                res = PluginResult(
                    plugin_id=p.plugin_id,
                    success=False,
                    issues=[],
                    stdout="",
                    stderr=str(exc),
                    returncode=1,
                )
            results.append(res)
        return results


class BasePlugin:
    """Base class for validator plugins referenced throughout the documentation."""

    plugin_id: str
    manifest: PluginManifest
    name: str

    def build_command(self, file_path: Path) -> List[str]:  # pragma: no cover - placeholder
        raise NotImplementedError

    def check_tool_available(self) -> bool:  # pragma: no cover - placeholder
        # Minimal default: assume available
        return True

