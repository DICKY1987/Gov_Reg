# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1030

except ImportError:
    import pytest
    pytest.skip("echo plugin module not available", allow_module_level=True)

class "Test Echo plugin (no-op validator)."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1030

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
try:
    from echo.plugin import EchoPlugin, register


class TestEchoDetection:
    """Test Echo plugin - always succeeds, no issues."""

    def test_plugin_registration(self):
        """Test that plugin can be registered."""
        plugin = register()
        assert isinstance(plugin, EchoPlugin)
        assert plugin.plugin_id == "echo"
        assert plugin.name == "Echo Validator"

    def test_tool_always_available(self):
        """Test tool is always available (no-op)."""
        plugin = EchoPlugin()
        assert plugin.check_tool_available() is True

    def test_build_command(self):
        """Test command building (not used)."""
        plugin = EchoPlugin()
        test_file = Path("test.txt")
        cmd = plugin.build_command(test_file)

        # Has command method but not used in execute()
        assert isinstance(cmd, list)
        assert "echo" in cmd

    def test_execute_always_succeeds(self):
        """Test that execute always succeeds."""
        plugin = EchoPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("any content")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.plugin_id == "echo"
            assert result.issues == []
        finally:
            test_file.unlink()

    def test_no_issues_produced(self):
        """Test that no issues are ever produced."""
        plugin = EchoPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("any python code with errors!")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Always returns empty issues list
            assert result.issues == []
            assert len(result.issues) == 0
        finally:
            test_file.unlink()

    def test_missing_file_still_succeeds(self):
        """Test that missing file still succeeds (no-op)."""
        plugin = EchoPlugin()
        test_file = Path("/nonexistent/file.txt")

        result = plugin.execute(test_file)

        # Still succeeds with no issues
        assert result.success is True
        assert result.issues == []

    def test_empty_file_succeeds(self):
        """Test that empty file succeeds."""
        plugin = EchoPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.issues == []
        finally:
            test_file.unlink()

    def test_binary_file_succeeds(self):
        """Test that binary file succeeds."""
        plugin = EchoPlugin()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\xFF\xFE")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.issues == []
        finally:
            test_file.unlink()

    def test_plugin_purpose(self):
        """Document that Echo is a no-op test plugin."""
        plugin = EchoPlugin()

        # Echo plugin exists for testing purposes
        # Always succeeds, never reports issues
        # Used to verify plugin loading/execution framework
        assert plugin.plugin_id == "echo"
        assert plugin.check_tool_available() is True
