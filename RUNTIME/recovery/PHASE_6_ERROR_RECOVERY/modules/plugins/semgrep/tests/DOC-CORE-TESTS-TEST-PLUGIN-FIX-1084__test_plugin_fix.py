# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1084
@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
except ImportError:
    import pytest
    pytest.skip("semgrep plugin module not available", allow_module_level=True)

class ORE-TESTS-TEST-PLUGIN-FIX-1084

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import shutil

import pytest

try:
    from phase6_error_recovery.modules.plugins.semgrep.src.semgrep.plugin import (
    SemgrepPlugin,
)


@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
class TestSemgrepFix:
    """Test Semgrep plugin - no auto-fix, detection only."""

    def test_no_fix_method(self):
        """Verify Semgrep plugin is detection-only (no auto-fix)."""
        plugin = SemgrepPlugin()

        # Semgrep is detection-only, no fix method
        assert not hasattr(plugin, "fix")

    def test_plugin_purpose_is_detection(self):
        """Verify plugin is configured for detection, not fixing."""
        plugin = SemgrepPlugin()

        # Plugin should only detect issues
        assert hasattr(plugin, "execute")
        assert hasattr(plugin, "check_tool_available")
        assert hasattr(plugin, "build_command")

        # No fix capabilities
        assert not hasattr(plugin, "fix")
        assert not hasattr(plugin, "apply_fix")


def test_semgrep_is_detection_only():
    """Document that Semgrep plugin is detection-only."""
    plugin = SemgrepPlugin()

    # This plugin only detects security issues
    # Fixes must be applied manually by developer
    assert plugin.plugin_id == "semgrep"
    assert plugin.name == "Semgrep"