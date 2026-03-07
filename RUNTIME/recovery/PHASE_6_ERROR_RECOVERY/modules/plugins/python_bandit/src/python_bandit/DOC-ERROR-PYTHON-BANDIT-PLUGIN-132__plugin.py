# DOC_LINK: DOC-ERROR-PYTHON-BANDIT-PLUGIN-132
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class BanditPlugin:
    plugin_id = "python_bandit"
    name = "Bandit Security Scanner"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("bandit") is not None

    def build_command(self, file_path: Path) -> List[str]:
        # Scan a single file quietly, JSON output
        return ["bandit", "-f", "json", "-q", str(file_path)]

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
            for r in data.get("results", []) or []:
                path = r.get("filename") or str(file_path)
                line = r.get("line_number")
                test_id = r.get("test_id")
                sev = (r.get("issue_severity") or "LOW").upper()
                msg = r.get("issue_text")
                severity = "error" if sev == "HIGH" else ("warning" if sev == "MEDIUM" else "info")
                issues.append(
                    PluginIssue(
                        tool="bandit",
                        path=path,
                        line=line,
                        column=None,
                        code=str(test_id) if test_id else None,
                        category="security",
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
    return BanditPlugin()

