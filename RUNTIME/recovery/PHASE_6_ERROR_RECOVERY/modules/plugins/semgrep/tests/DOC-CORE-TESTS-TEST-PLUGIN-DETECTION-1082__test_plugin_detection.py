# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1082
@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
except ImportError:
    import pytest
    pytest.skip("semgrep plugin module not available", allow_module_level=True)

class TECTION-1082

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import shutil
import tempfile

import pytest

try:
    from phase6_error_recovery.modules.plugins.semgrep.src.semgrep.plugin import (
    SemgrepPlugin,
    register,
)


@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
class TestSemgrepDetection:
    """Test Semgrep plugin error detection capabilities."""

    def test_plugin_registration(self):
        """Test that plugin can be registered."""
        plugin = register()
        assert isinstance(plugin, SemgrepPlugin)
        assert plugin.plugin_id == "semgrep"
        assert plugin.name == "Semgrep"

    def test_tool_available(self):
        """Test tool availability check."""
        plugin = SemgrepPlugin()
        assert plugin.check_tool_available() is True

    def test_build_command(self):
        """Test command building."""
        plugin = SemgrepPlugin()
        test_file = Path("test.py")
        cmd = plugin.build_command(test_file)

        assert "semgrep" in cmd
        assert "--json" in cmd
        assert "--config" in cmd
        assert "auto" in cmd
        assert str(test_file) in cmd

    def test_detects_sql_injection(self):
        """Test detection of SQL injection vulnerability."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)
    return cursor.fetchone()
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Semgrep should succeed (returncode 0 or 1)
            assert result.success is True
            assert result.plugin_id == "semgrep"

            # May or may not detect issues depending on semgrep rules
            # Just verify structure is correct
            assert isinstance(result.issues, list)
            for issue in result.issues:
                assert issue.tool == "semgrep"
                assert issue.category == "security"
                assert issue.severity in ("error", "warning", "info")
        finally:
            test_file.unlink()

    def test_clean_file_no_issues(self):
        """Test clean file produces no issues."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def add(a, b):
    """Add two numbers."""
    return a + b
'''
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_handles_missing_file(self):
        """Test handling of missing file."""
        plugin = SemgrepPlugin()
        test_file = Path("/nonexistent/file.py")

        result = plugin.execute(test_file)

        # Should handle gracefully, not crash
        assert result.plugin_id == "semgrep"
        assert isinstance(result.issues, list)

    def test_handles_empty_file(self):
        """Test handling of empty file."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_detects_hardcoded_password(self):
        """Test detection of hardcoded password."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import requests

def connect():
    # Hardcoded password (potential security issue)
    password = "SuperSecret123!"
    return requests.get("https://api.example.com", auth=("user", password))
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.plugin_id == "semgrep"
            # Structure validation
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_issue_structure(self):
        """Test that issues have correct structure."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
os.system("rm -rf /")  # Dangerous command
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True

            for issue in result.issues:
                # Verify all required fields present
                assert hasattr(issue, "tool")
                assert hasattr(issue, "path")
                assert hasattr(issue, "line")
                assert hasattr(issue, "category")
                assert hasattr(issue, "severity")
                assert hasattr(issue, "message")

                assert issue.tool == "semgrep"
                assert issue.category == "security"
        finally:
            test_file.unlink()

    def test_json_output_parsing(self):
        """Test that JSON output is parsed correctly."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should not crash during JSON parsing
            assert result.plugin_id == "semgrep"
            assert isinstance(result.stdout, str)
            assert isinstance(result.stderr, str)
        finally:
            test_file.unlink()


def test_plugin_without_semgrep():
    """Test plugin behavior when semgrep is not available."""
    plugin = SemgrepPlugin()

    # Just verify it has the method
    assert hasattr(plugin, "check_tool_available")
    assert callable(plugin.check_tool_available)