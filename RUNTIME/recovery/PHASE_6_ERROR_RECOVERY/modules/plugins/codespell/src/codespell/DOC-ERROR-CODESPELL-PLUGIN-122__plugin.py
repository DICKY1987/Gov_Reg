# DOC_LINK: DOC-ERROR-CODESPELL-PLUGIN-122
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class CodespellPlugin:
    plugin_id = "codespell"
    name = "codespell"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("codespell") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["codespell", str(file_path)]

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
        # Parse output format: file:line: word ==> suggestion
        pattern = re.compile(r"^(.+?):(\d+):\s*(.+)$")
        for line in proc.stdout.splitlines():
            match = pattern.match(line)
            if match:
                path_str, line_num, message = match.groups()
                issues.append(
                    PluginIssue(
                        tool="codespell",
                        path=path_str,
                        line=int(line_num),
                        column=None,
                        code=None,
                        category="style",
                        severity="warning",
                        message=message.strip(),
                    )
                )

        success = proc.returncode in {0, 1}
        return PluginResult(
            plugin_id=self.plugin_id,
            success=success,
            issues=issues,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            returncode=proc.returncode,
        )


def register():
    return CodespellPlugin()
