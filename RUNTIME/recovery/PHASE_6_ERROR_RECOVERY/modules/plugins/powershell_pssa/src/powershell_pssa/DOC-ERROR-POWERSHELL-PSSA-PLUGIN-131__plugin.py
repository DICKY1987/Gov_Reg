# DOC_LINK: DOC-ERROR-POWERSHELL-PSSA-PLUGIN-131
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class PSScriptAnalyzerPlugin:
    plugin_id = "powershell_pssa"
    name = "PSScriptAnalyzer"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("pwsh") is not None

    def build_command(self, file_path: Path) -> List[str]:
        cmd_str = (
            f"Invoke-ScriptAnalyzer -Path '{file_path}' "
            f"-Severity Error,Warning,Information | ConvertTo-Json -Depth 5"
        )
        return ["pwsh", "-NoProfile", "-Command", cmd_str]

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
                # Handle both single object and array
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    rule_name = item.get("RuleName")
                    message = item.get("Message")
                    severity_str = item.get("Severity", "").lower()
                    line = item.get("Line")
                    col = item.get("Column")
                    script_path = item.get("ScriptPath") or str(file_path)

                    # Map severity: Error→error, Warning→warning, Information→info
                    severity_map = {
                        "error": "error",
                        "warning": "warning",
                        "information": "info",
                    }
                    severity = severity_map.get(severity_str, "warning")

                    # Category: parse errors→syntax, otherwise style
                    category = "syntax" if "ParseError" in (rule_name or "") else "style"

                    issues.append(
                        PluginIssue(
                            tool="PSScriptAnalyzer",
                            path=script_path,
                            line=line,
                            column=col,
                            code=rule_name,
                            category=category,
                            severity=severity,
                            message=message,
                        )
                    )
        except Exception:
            pass

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
    return PSScriptAnalyzerPlugin()
