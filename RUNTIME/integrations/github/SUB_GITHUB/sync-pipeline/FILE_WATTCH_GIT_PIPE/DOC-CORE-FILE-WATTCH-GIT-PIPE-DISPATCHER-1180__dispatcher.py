# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-DISPATCHER-1180
from __future__ import annotations

import importlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from fwgp import events
from fwgp.state import StateStore


@dataclass
class LoadedPlugin:
    key: str  # module:Class
    instance: Any


class Dispatcher:
    def __init__(self, state: StateStore, logger, timeout_sec: float = 2.0):
        self.state = state
        self.logger = logger
        self.timeout_sec = timeout_sec
        self.plugins: List[LoadedPlugin] = []
        self.pool = ThreadPoolExecutor(max_workers=8)

    def load_plugins(self, plugin_specs: List[str]) -> None:
        self.plugins.clear()
        for spec in plugin_specs:
            try:
                module_name, class_name = spec.split(":", 1)
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                inst = cls()
                self.plugins.append(LoadedPlugin(key=spec, instance=inst))
                self.logger.info("Loaded plugin: %s", spec)
            except Exception as e:
                self.logger.error("Failed to load plugin %s: %s", spec, e)

    def _call(self, plugin: LoadedPlugin, method: str, *args, **kwargs):
        if self.state.is_disabled(plugin.key):
            return None
        fn = getattr(plugin.instance, method, None)
        if not callable(fn):
            return None
        fut = self.pool.submit(fn, *args, **kwargs)
        try:
            return fut.result(timeout=self.timeout_sec)
        except TimeoutError:
            self.logger.error("Plugin %s.%s timed out", plugin.key, method)
            self.state.record_failure(plugin.key)
        except Exception as e:
            self.logger.error("Plugin %s.%s failed: %s", plugin.key, method, e)
            self.state.record_failure(plugin.key)
        return None

    # Hook invocations
    def on_file_detected(self, evt: events.FileDetectedEvent, ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.ON_FILE_DETECTED.value, evt, ctx)

    def before_stage(self, req: events.StageRequest, ctx: Dict[str, Any]) -> Tuple[bool, List[str]]:
        allow = True
        reasons: List[str] = []
        for p in self.plugins:
            res = self._call(p, events.Hook.BEFORE_STAGE.value, req, ctx)
            if hasattr(res, "allow") and res and res.allow is False:
                allow = False
                if getattr(res, "reasons", None):
                    reasons.extend(res.reasons)
        return allow, reasons

    def after_stage(self, req: events.StageRequest, ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.AFTER_STAGE.value, req, ctx)

    def before_commit(self, req: events.CommitRequest, ctx: Dict[str, Any]):
        allow = True
        message_override = None
        sign = False
        for p in self.plugins:
            res = self._call(p, events.Hook.BEFORE_COMMIT.value, req, ctx)
            if hasattr(res, "allow") and res and res.allow is False:
                allow = False
            if hasattr(res, "message_override") and res and res.message_override:
                message_override = res.message_override
            if hasattr(res, "sign") and res and res.sign:
                sign = True
        return allow, message_override, sign

    def after_commit(self, commit_sha: Optional[str], ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.AFTER_COMMIT.value, commit_sha, ctx)

    def before_push(self, req: events.PushRequest, ctx: Dict[str, Any]):
        allow = True
        force = False
        for p in self.plugins:
            res = self._call(p, events.Hook.BEFORE_PUSH.value, req, ctx)
            if hasattr(res, "allow") and res and res.allow is False:
                allow = False
            if hasattr(res, "force") and res and res.force:
                force = True
        return allow, force

    def after_push(self, req: events.PushRequest, ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.AFTER_PUSH.value, req, ctx)

    def before_pull(self, req: events.PullRequest, ctx: Dict[str, Any]):
        allow = True
        strategy = None
        for p in self.plugins:
            res = self._call(p, events.Hook.BEFORE_PULL.value, req, ctx)
            if hasattr(res, "allow") and res and res.allow is False:
                allow = False
            if hasattr(res, "strategy") and res and res.strategy:
                strategy = res.strategy
        return allow, strategy

    def after_pull(self, res: events.PullResult, ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.AFTER_PULL.value, res, ctx)

    def on_conflict(self, info: events.ConflictInfo, ctx: Dict[str, Any]):
        for p in self.plugins:
            self._call(p, events.Hook.ON_CONFLICT.value, info, ctx)
