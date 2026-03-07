# DOC_LINK: DOC-ERROR-PYTHON-SAFETY-PLUGIN-138
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginIssue, PluginResult


def _find_requirements(start: Path) -> Optional[Path]:
    cur = start
    for _ in range(5):  # search up to 5 levels
        for name in ("requirements.txt", "requirements-dev.txt", "req.txt"):
            p = cur / name
            if p.exists():
                return p
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


class SafetyPlugin:
    plugin_id = "python_safety"
    name = "Safety Dependency Checker"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("safety") is not None

    def build_command(self, reqs: Path) -> List[str]:
        # Prefer JSON output. Some Safety versions require auth for full DB; treat any output best-effort.
        cmd = ["safety", "check", "--json", "--file", str(reqs)]
        db_path = os.getenv("SAFETY_DB")
        if db_path:
            cmd += ["--db", db_path]
        return cmd

    def execute(self, file_path: Path) -> PluginResult:
        reqs = _find_requirements(file_path.parent)
        if not reqs:
            # Gracefully succeed with no issues when no requirements file nearby
            return PluginResult(plugin_id=self.plugin_id, success=True, issues=[])

        cmd = self.build_command(reqs)
        env = scrub_env()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(reqs.parent),
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
            # Safety JSON: either a list of vulns or an object with issues; handle common list form
            items = data if isinstance(data, list) else data.get("vulnerabilities", []) or []
            for v in items:
                # Flexible parsing across versions
                pkg = v.get("package_name") or v.get("dependency", {}).get("name")
                spec = v.get("affected_versions") or v.get("dependency", {}).get("version")
                cve = v.get("cve") or v.get("identifier")
                sev = (v.get("severity") or "high").lower()
                severity = "error" if sev in {"critical", "high"} else ("warning" if sev == "medium" else "info")
                msg = v.get("advisory") or v.get("description") or "Vulnerability detected"
                issues.append(
                    PluginIssue(
                        tool="safety",
                        path=str(reqs),
                        line=None,
                        column=None,
                        code=str(cve) if cve else None,
                        category="security",
                        severity=severity,
                        message=f"{pkg} {spec}: {msg}" if pkg else msg,
                    )
                )
        except Exception:
            # If parsing fails (e.g., non-JSON due to license), return success with no issues
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
    return SafetyPlugin()

