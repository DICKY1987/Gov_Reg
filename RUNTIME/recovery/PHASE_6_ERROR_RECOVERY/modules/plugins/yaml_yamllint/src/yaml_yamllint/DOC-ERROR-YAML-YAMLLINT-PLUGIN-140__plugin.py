# DOC_LINK: DOC-ERROR-YAML-YAMLLINT-PLUGIN-140
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class YamllintPlugin:
    plugin_id = "yaml_yamllint"
    name = "yamllint"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("yamllint") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["yamllint", "-f", "parsable", str(file_path)]

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
        # Parse output format: file:line:col: [severity] message (rule)
        pattern = re.compile(
            r"^(.+?):(\d+):(\d+):\s*\[(error|warning)\]\s*(.+?)(?:\s+\((.+?)\))?$"
        )
        for line in proc.stdout.splitlines():
            match = pattern.match(line)
            if match:
                path_str, line_num, col_num, severity, message, rule = match.groups()
                # Category: parser errors→syntax, otherwise style
                category = "syntax" if "syntax error" in message.lower() else "style"
                issues.append(
                    PluginIssue(
                        tool="yamllint",
                        path=path_str,
                        line=int(line_num),
                        column=int(col_num),
                        code=rule,
                        category=category,
                        severity=severity,
                        message=message,
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
    return YamllintPlugin()
