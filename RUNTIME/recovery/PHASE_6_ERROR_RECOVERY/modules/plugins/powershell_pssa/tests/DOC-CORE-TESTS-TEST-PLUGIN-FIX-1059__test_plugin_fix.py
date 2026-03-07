# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1059

except ImportError:
    import pytest
    pytest.skip("powershell_pssa plugin module not available", allow_module_level=True)

class "Test PSScriptAnalyzer plugin fix capabilities (N/A - detection only)."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1059

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import shutil

import pytest

try:
    from phase6_error_recovery.modules.plugins.powershell_pssa.src.powershell_pssa.plugin import (
    PSScriptAnalyzerPlugin,
)


class TestPSSAFix:
    """Test PSScriptAnalyzer plugin - no auto-fix, detection only."""

    def test_no_fix_method(self):
        """Verify PSScriptAnalyzer plugin is detection-only (no auto-fix)."""
        plugin = PSScriptAnalyzerPlugin()

        # PSSA is detection-only, no fix method
        assert not hasattr(plugin, "fix")

    def test_plugin_purpose_is_detection(self):
        """Verify plugin is configured for detection, not fixing."""
        plugin = PSScriptAnalyzerPlugin()

        # Plugin should only detect issues
        assert hasattr(plugin, "execute")
        assert hasattr(plugin, "check_tool_available")
        assert hasattr(plugin, "build_command")

        # No fix capabilities
        assert not hasattr(plugin, "fix")
        assert not hasattr(plugin, "apply_fix")


def test_pssa_is_detection_only():
    """Document that PSScriptAnalyzer plugin is detection-only."""
    plugin = PSScriptAnalyzerPlugin()

    # This plugin only detects PowerShell issues
    # Fixes must be applied manually
    assert plugin.plugin_id == "powershell_pssa"
    assert plugin.name == "PSScriptAnalyzer"