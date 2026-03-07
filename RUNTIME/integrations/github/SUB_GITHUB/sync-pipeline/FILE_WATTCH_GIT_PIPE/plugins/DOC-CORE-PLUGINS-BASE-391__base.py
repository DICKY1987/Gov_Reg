# DOC_LINK: DOC-CORE-PLUGINS-BASE-391
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from fwgp import events


@dataclass
class PluginManifest:
    name: str
    version: str = "0.1.0"
    author: Optional[str] = None
    description: Optional[str] = None


class BasePlugin:
    manifest: PluginManifest

    def __init__(self):
        # Subclasses should set self.manifest accordingly
        if not hasattr(self, "manifest"):
            self.manifest = PluginManifest(name=self.__class__.__name__)

    # Hook defaults: no-op implementations
    def onFileDetected(self, evt: events.FileDetectedEvent, ctx: Dict[str, Any]) -> None:
        return None

    def beforeStage(self, req: events.StageRequest, ctx: Dict[str, Any]) -> events.StageDecision:
        return events.StageDecision(allow=True)

    def afterStage(self, req: events.StageRequest, ctx: Dict[str, Any]) -> None:
        return None

    def beforeCommit(self, req: events.CommitRequest, ctx: Dict[str, Any]) -> events.CommitDecision:
        return events.CommitDecision(allow=True)

    def afterCommit(self, commit_sha: Optional[str], ctx: Dict[str, Any]) -> None:
        return None

    def beforePush(self, req: events.PushRequest, ctx: Dict[str, Any]) -> events.PushDecision:
        return events.PushDecision(allow=True)

    def afterPush(self, req: events.PushRequest, ctx: Dict[str, Any]) -> None:
        return None

    def beforePull(self, req: events.PullRequest, ctx: Dict[str, Any]) -> events.PullDecision:
        return events.PullDecision(allow=True)

    def afterPull(self, res: events.PullResult, ctx: Dict[str, Any]) -> None:
        return None

    def onConflict(self, info: events.ConflictInfo, ctx: Dict[str, Any]):
        return None
