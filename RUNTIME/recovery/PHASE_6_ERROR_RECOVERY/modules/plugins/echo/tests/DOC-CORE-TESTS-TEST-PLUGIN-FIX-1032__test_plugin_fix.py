# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1032

except ImportError:
    import pytest
    pytest.skip("echo plugin module not available", allow_module_level=True)

class "Test Echo plugin fix capabilities (N/A - no-op validator)."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1032

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from phase6_error_recovery.modules.plugins.echo.src.echo.plugin import EchoPlugin


class TestEchoFix:
    """Test Echo plugin - no fix needed, always succeeds."""

    def test_no_fix_method(self):
        """Verify Echo plugin has no fix method."""
        plugin = EchoPlugin()

        # Echo is no-op, no fix method
        assert not hasattr(plugin, "fix")

    def test_no_fix_needed(self):
        """Verify Echo never produces issues to fix."""
        plugin = EchoPlugin()

        # Echo never reports issues, so no fixes needed
        assert hasattr(plugin, "execute")
        assert not hasattr(plugin, "fix")


def test_echo_no_op_validator():
    """Document that Echo is a no-op validator."""
    plugin = EchoPlugin()

    # This plugin exists for testing framework
    # Always succeeds, never fixes anything
    assert plugin.plugin_id == "echo"
    assert plugin.name == "Echo Validator"