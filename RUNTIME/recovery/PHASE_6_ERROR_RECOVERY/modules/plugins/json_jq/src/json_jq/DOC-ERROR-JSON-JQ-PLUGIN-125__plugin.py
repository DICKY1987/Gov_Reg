# DOC_LINK: DOC-ERROR-JSON-JQ-PLUGIN-125
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class JsonJqPlugin:
    plugin_id = "json_jq"
    name = "jq (JSON syntax)"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("jq") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["jq", "empty", str(file_path)]

    def execute(self, file_path: Path) -> PluginResult:
        cmd = self.build_command(file_path)
        env = scrub_env()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(file_path.parent),
                env=env,
                shell=False,
            )
        except Exception as exc:
            return PluginResult(
                plugin_id=self.plugin_id,
                success=False,
                stderr=str(exc),
                stdout="",
                returncode=1,
            )

        issues: List[PluginIssue] = []
        if proc.returncode != 0 and proc.stderr:
            # JSON syntax error; create single issue
            issues.append(
                PluginIssue(
                    tool="jq",
                    path=str(file_path),
                    line=None,
                    column=None,
                    code=None,
                    category="syntax",
                    severity="error",
                    message=proc.stderr.strip(),
                )
            )

        success = proc.returncode == 0
        return PluginResult(
            plugin_id=self.plugin_id,
            success=success,
            issues=issues,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            returncode=proc.returncode,
        )


def register():
    return JsonJqPlugin()
