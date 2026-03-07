# DOC_LINK: DOC-CORE-PLUGINS-COMMIT-MSG-392
from __future__ import annotations

from typing import Any, Dict

from fwgp import events
from fwgp.plugins.base import BasePlugin, PluginManifest


class CommitMessage(BasePlugin):
    manifest = PluginManifest(
        name="CommitMessage",
        version="0.1.0",
        description="Generates a conventional commit message if none is provided.",
    )

    def beforeCommit(self, req: events.CommitRequest, ctx: Dict[str, Any]) -> events.CommitDecision:
        if not req.staged_summary:
            return events.CommitDecision(allow=False)
        # Simple heuristic message
        first = req.staged_summary[0]
        extras = len(req.staged_summary) - 1
        msg = f"chore(auto): update {first}" + (f" (+{extras} files)" if extras > 0 else "")
        return events.CommitDecision(allow=True, message_override=msg)

