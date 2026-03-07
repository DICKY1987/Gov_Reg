# DOC_LINK: DOC-ERROR-ECHO-PLUGIN-123
from __future__ import annotations

from pathlib import Path
from typing import List

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.error.shared.utils.types import PluginResult, PluginIssue


class EchoPlugin:
    plugin_id = "echo"
    name = "Echo Validator"
    manifest = {}  # set by PluginManager

    def check_tool_available(self) -> bool:
        return True

    def build_command(self, file_path: Path) -> List[str]:  # not used
        return ["echo", str(file_path)]

    def execute(self, file_path: Path) -> PluginResult:
        # No-op validator: always succeeds, emits no issues
        return PluginResult(plugin_id=self.plugin_id, success=True, issues=[])


def register():
    return EchoPlugin()

