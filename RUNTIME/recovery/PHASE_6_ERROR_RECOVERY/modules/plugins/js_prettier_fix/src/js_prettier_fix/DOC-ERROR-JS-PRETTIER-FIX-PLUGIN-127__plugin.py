# DOC_LINK: DOC-ERROR-JS-PRETTIER-FIX-PLUGIN-127
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.env import scrub_env
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginResult


class PrettierFixPlugin:
    plugin_id = "js_prettier_fix"
    name = "Prettier Formatter (fix)"
    manifest = {}

    def check_tool_available(self) -> bool:
        return shutil.which("prettier") is not None

    def build_command(self, file_path: Path) -> List[str]:
        return ["prettier", "--write", str(file_path)]

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
            success = proc.returncode == 0
            return PluginResult(
                plugin_id=self.plugin_id,
                success=success,
                issues=[],
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                returncode=proc.returncode,
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


def register():
    return PrettierFixPlugin()
