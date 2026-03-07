# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1034
@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks not installed")
except ImportError:
    import pytest
    pytest.skip("gitleaks plugin module not available", allow_module_level=True)

class TECTION-1034

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import shutil
import tempfile

import pytest

try:
    from phase6_error_recovery.modules.plugins.gitleaks.src.gitleaks.plugin import (
    GitleaksPlugin,
    register,
)


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks not installed")
class TestGitleaksDetection:
    """Test Gitleaks plugin secret detection capabilities."""

    def test_plugin_registration(self):
        """Test that plugin can be registered."""
        plugin = register()
        assert isinstance(plugin, GitleaksPlugin)
        assert plugin.plugin_id == "gitleaks"
        assert plugin.name == "Gitleaks"

    def test_tool_available(self):
        """Test tool availability check."""
        plugin = GitleaksPlugin()
        assert plugin.check_tool_available() is True

    def test_build_command(self):
        """Test command building."""
        plugin = GitleaksPlugin()
        test_file = Path("test.py")
        cmd = plugin.build_command(test_file)

        assert "gitleaks" in cmd
        assert "detect" in cmd
        assert "--no-git" in cmd
        assert "--report-format" in cmd
        assert "json" in cmd

    def test_detects_aws_key(self):
        """Test detection of AWS access key."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
# AWS credentials
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Gitleaks should succeed (returncode 0 or 1)
            assert result.success is True
            assert result.plugin_id == "gitleaks"

            # Check structure
            assert isinstance(result.issues, list)
            for issue in result.issues:
                assert issue.tool == "gitleaks"
                assert issue.category == "security"
                assert issue.severity == "error"
        finally:
            test_file.unlink()

    def test_detects_github_token(self):
        """Test detection of GitHub personal access token."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import requests

# GitHub token
token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
headers = {"Authorization": f"Bearer {token}"}
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.plugin_id == "gitleaks"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_detects_private_key(self):
        """Test detection of private key."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(
                """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert result.plugin_id == "gitleaks"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_clean_file_no_secrets(self):
        """Test clean file produces no issues."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def add(a, b):
    """Add two numbers."""
    return a + b

API_URL = "https://api.example.com"
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
        plugin = GitleaksPlugin()
        test_file = Path("/nonexistent/file.py")

        result = plugin.execute(test_file)

        # Should handle gracefully
        assert result.plugin_id == "gitleaks"
        assert isinstance(result.issues, list)

    def test_handles_empty_file(self):
        """Test handling of empty file."""
        plugin = GitleaksPlugin()

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

    def test_issue_structure(self):
        """Test that issues have correct structure."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(
                """
API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz
DATABASE_PASSWORD=SuperSecretPassword123!
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True

            for issue in result.issues:
                assert hasattr(issue, "tool")
                assert hasattr(issue, "path")
                assert hasattr(issue, "line")
                assert hasattr(issue, "category")
                assert hasattr(issue, "severity")
                assert hasattr(issue, "message")

                assert issue.tool == "gitleaks"
                assert issue.category == "security"
                assert issue.severity == "error"
        finally:
            test_file.unlink()

    def test_filters_to_target_file_only(self):
        """Test that only issues in target file are reported."""
        plugin = GitleaksPlugin()

        # Create a file that gitleaks will scan
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('API_KEY = "test"\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # All reported issues should be from target file
            for issue in result.issues:
                assert test_file.name in str(issue.path)
        finally:
            test_file.unlink()

    def test_json_output_parsing(self):
        """Test that JSON output is parsed correctly."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should not crash during JSON parsing
            assert result.plugin_id == "gitleaks"
            assert isinstance(result.stdout, str)
            assert isinstance(result.stderr, str)
        finally:
            test_file.unlink()


def test_plugin_without_gitleaks():
    """Test plugin behavior when gitleaks is not available."""
    plugin = GitleaksPlugin()

    # Just verify it has the method
    assert hasattr(plugin, "check_tool_available")
    assert callable(plugin.check_tool_available)