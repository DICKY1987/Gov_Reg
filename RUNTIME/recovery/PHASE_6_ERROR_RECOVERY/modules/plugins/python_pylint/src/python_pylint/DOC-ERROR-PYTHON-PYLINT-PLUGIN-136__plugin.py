# DOC_LINK: DOC-ERROR-PYTHON-PYLINT-PLUGIN-136
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


PYLINT_USAGE_ERROR_BIT = 32


class PylintPlugin:
    plugin_id = "python_pylint"
    name = "Pylint"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("pylint") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["pylint", "--output-format=json", str(file_path)]

    def execute(self, file_path: Path) -> PluginResult:
        cmd = self.build_command(file_path)
        env = scrub_env()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(file_path.parent),
                env=env,
                shell=False,
            )
        except Exception as exc:
            return PluginResult(
                plugin_id=self.plugin_id,
                success=False,
                issues=[],
                stdout="",
                stderr=str(exc),
                returncode=1,
            )

        issues: List[PluginIssue] = []
        try:
            data = json.loads(proc.stdout or "[]")
            # Data is a list of message dicts
            for m in data:
                mtype = (m.get("type") or "").lower()
                msg = m.get("message")
                code = m.get("message-id") or m.get("symbol")
                path = m.get("path") or str(file_path)
                line = m.get("line")
                col = m.get("column")

                # Category mapping: E/F -> syntax; W/C/R -> style/other
                if mtype in {"error", "fatal"}:
                    category = "syntax"
                    severity = "error"
                elif mtype == "warning":
                    category = "style"
                    severity = "warning"
                elif mtype in {"convention", "refactor"}:
                    category = "style"
                    severity = "info"
                else:
                    category = "other"
                    severity = "info"

                issues.append(
                    PluginIssue(
                        tool="pylint",
                        path=path,
                        line=line,
                        column=col,
                        code=str(code) if code is not None else None,
                        category=category,
                        severity=severity,
                        message=msg,
                    )
                )
        except Exception:
            pass

        success = (proc.returncode & PYLINT_USAGE_ERROR_BIT) == 0
        return PluginResult(
            plugin_id=self.plugin_id,
            success=success,
            issues=issues,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            returncode=proc.returncode,
        )


def register():
    return PylintPlugin()

