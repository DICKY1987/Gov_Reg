# DOC_LINK: DOC-ERROR-GITLEAKS-PLUGIN-124
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class GitleaksPlugin:
    plugin_id = "gitleaks"
    name = "Gitleaks"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("gitleaks") is not None

    def build_command(self, file_path: Path) -> List[str]:
        # Gitleaks scans directories, so use parent directory
        return [
            "gitleaks",
            "detect",
            "--no-git",
            "--no-banner",
            "--report-format",
            "json",
            "--source",
            str(file_path.parent),
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
                # Gitleaks returns array of findings
                if isinstance(data, list):
                    for finding in data:
                        found_file = finding.get("File")
                        # Filter to only include the target file
                        if found_file and Path(found_file).name == file_path.name:
                            line = finding.get("StartLine")
                            rule_id = finding.get("RuleID")
                            message = finding.get("Description") or "Secret detected"

                            issues.append(
                                PluginIssue(
                                    tool="gitleaks",
                                    path=found_file,
                                    line=line,
                                    column=None,
                                    code=rule_id,
                                    category="security",
                                    severity="error",
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
    return GitleaksPlugin()
