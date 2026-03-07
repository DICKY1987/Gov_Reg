# DOC_LINK: DOC-ERROR-JS-ESLINT-PLUGIN-126
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class ESLintPlugin:
    plugin_id = "js_eslint"
    name = "ESLint"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("eslint") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["eslint", "-f", "json", str(file_path)]

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
        try:
            if proc.stdout.strip():
                data = json.loads(proc.stdout)
                for file_result in data:
                    file_path_str = file_result.get("filePath") or str(file_path)
                    messages = file_result.get("messages", [])
                    for msg in messages:
                        line = msg.get("line")
                        col = msg.get("column")
                        rule_id = msg.get("ruleId")
                        message_text = msg.get("message")
                        severity_num = msg.get("severity", 1)

                        # Map severity: 2→error, 1→warning
                        severity = "error" if severity_num == 2 else "warning"

                        issues.append(
                            PluginIssue(
                                tool="eslint",
                                path=file_path_str,
                                line=line,
                                column=col,
                                code=rule_id,
                                category="style",
                                severity=severity,
                                message=message_text,
                            )
                        )
        except Exception:
            pass

        # ESLint returns 0 when no issues, 1 when issues found — both successful
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
    return ESLintPlugin()
