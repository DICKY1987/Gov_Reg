# DOC_LINK: DOC-CORE-PLUGINS-LINT-FORMATTER-393
from __future__ import annotations

from typing import Any, Dict

from fwgp import events
from fwgp.plugins.base import BasePlugin, PluginManifest


class LintFormatter(BasePlugin):
    manifest = PluginManifest(
        name="LintFormatter",
        version="0.1.0",
        description="Advisory plugin that logs lint/format suggestions (stub).",
    )

    def onFileDetected(self, evt: events.FileDetectedEvent, ctx: Dict[str, Any]) -> None:
        logger = ctx.get("logger")
        if logger:
            logger.info("[LintFormatter] Detected change: %s (%s)", evt.path, evt.change_type)

