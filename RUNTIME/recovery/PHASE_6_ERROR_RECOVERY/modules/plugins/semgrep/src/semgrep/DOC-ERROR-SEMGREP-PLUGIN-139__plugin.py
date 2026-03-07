# DOC_LINK: DOC-ERROR-SEMGREP-PLUGIN-139
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class SemgrepPlugin:
    plugin_id = "semgrep"
    name = "Semgrep"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("semgrep") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return [
            "semgrep",
            "--json",
            "--quiet",
            "--include",
            str(file_path),
            "--config",
            "auto",
        ]

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
                stderr=str(exc),
                stdout="",
                returncode=1,
            )

        issues: List[PluginIssue] = []
        try:
            if proc.stdout.strip():
                data = json.loads(proc.stdout)
                results = data.get("results", [])
                for result in results:
                    path_str = result.get("path") or str(file_path)
                    start = result.get("start", {})
                    line = start.get("line")
                    col = start.get("col")
                    check_id = result.get("check_id")
                    message = result.get("extra", {}).get("message")
                    severity_str = result.get("extra", {}).get("severity", "WARNING").upper()

                    # Map severity: ERROR→error, WARNING→warning, INFO→info
                    severity_map = {
                        "ERROR": "error",
                        "WARNING": "warning",
                        "INFO": "info",
                    }
                    severity = severity_map.get(severity_str, "warning")

                    issues.append(
                        PluginIssue(
                            tool="semgrep",
                            path=path_str,
                            line=line,
                            column=col,
                            code=check_id,
                            category="security",
                            severity=severity,
                            message=message,
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
    return SemgrepPlugin()
