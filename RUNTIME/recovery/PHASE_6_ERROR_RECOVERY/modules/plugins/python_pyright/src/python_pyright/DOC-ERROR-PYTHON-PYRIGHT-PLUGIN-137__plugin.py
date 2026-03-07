# DOC_LINK: DOC-ERROR-PYTHON-PYRIGHT-PLUGIN-137
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class PyrightPlugin:
    plugin_id = "python_pyright"
    name = "Pyright Type Checker"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("pyright") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["pyright", str(file_path), "--outputjson"]

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
            data = json.loads(proc.stdout or "{}")
            for d in data.get("generalDiagnostics", []) or []:
                path = d.get("file") or str(file_path)
                rng = d.get("range", {}).get("start", {})
                line = rng.get("line")
                col = rng.get("character")
                sev = (d.get("severity") or "error").lower()
                severity = "error" if sev == "error" else "warning"
                code = d.get("rule") or d.get("code")
                msg = d.get("message")
                issues.append(
                    PluginIssue(
                        tool="pyright",
                        path=path,
                        line=(line + 1) if isinstance(line, int) else None,
                        column=(col + 1) if isinstance(col, int) else None,
                        code=str(code) if code is not None else None,
                        category="type",
                        severity=severity,
                        message=msg,
                    )
                )
        except Exception:
            pass

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
    return PyrightPlugin()

