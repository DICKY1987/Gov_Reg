# DOC_LINK: DOC-CORE-PLUGINS-SECRETS-SCANNER-394
from __future__ import annotations

import re
from typing import Any, Dict

from fwgp import events
from fwgp.plugins.base import BasePlugin, PluginManifest


SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9\-_]{16,}['\"]"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"][A-Za-z0-9\-_]{16,}['\"]"),
]


class SecretsScanner(BasePlugin):
    manifest = PluginManifest(
        name="SecretsScanner",
        version="0.1.0",
        description="Blocks commit if potential secrets are detected in staged files.",
    )

    def beforeCommit(self, req: events.CommitRequest, ctx: Dict[str, Any]) -> events.CommitDecision:
        repo_path: str = ctx.get("repo_path", "")
        # Lightweight scan: Open files by name (staged summary) and scan contents.
        offenders = []
        for rel in req.staged_summary:
            try:
                content = (ctx.get("open_file") or (lambda p: open(p, "r", encoding="utf-8", errors="ignore")))(
                    f"{repo_path}/{rel}"
                ).read()
            except Exception:
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(content):
                    offenders.append(rel)
                    break
        if offenders:
            return events.CommitDecision(
                allow=False,
                message_override=None,
            )
        return events.CommitDecision(allow=True)

