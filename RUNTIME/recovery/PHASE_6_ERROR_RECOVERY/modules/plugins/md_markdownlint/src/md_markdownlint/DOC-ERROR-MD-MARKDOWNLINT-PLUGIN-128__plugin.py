# DOC_LINK: DOC-ERROR-MD-MARKDOWNLINT-PLUGIN-128
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


class MarkdownlintPlugin:
    plugin_id = "md_markdownlint"
    name = "markdownlint-cli"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("markdownlint") is not None

    def build_command(self, file_path: Path) -> List[str]:
        # Try JSON format first, fallback to text parsing
        return ["markdownlint", "-j", str(file_path)]

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

        # Try JSON parsing
        try:
            if proc.stdout.strip():
                data = json.loads(proc.stdout)
                for file_key, violations in data.items():
                    for violation in violations:
                        line = violation.get("lineNumber")
                        rule_names = violation.get("ruleNames", [])
                        rule_code = rule_names[0] if rule_names else None
                        message = violation.get("ruleDescription")

                        issues.append(
                            PluginIssue(
                                tool="markdownlint",
                                path=file_key,
                                line=line,
                                column=None,
                                code=rule_code,
                                category="style",
                                severity="warning",
                                message=message,
                            )
                        )
        except json.JSONDecodeError:
            # Fallback: parse text format file:line rule message
            pattern = re.compile(r"^(.+?):(\d+)(?::(\d+))?\s+(\S+)\s+(.+)$")
            for line in proc.stdout.splitlines():
                match = pattern.match(line)
                if match:
                    path_str, line_num, col_num, rule, message = match.groups()
                    issues.append(
                        PluginIssue(
                            tool="markdownlint",
                            path=path_str,
                            line=int(line_num),
                            column=int(col_num) if col_num else None,
                            code=rule,
                            category="style",
                            severity="warning",
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
    return MarkdownlintPlugin()
