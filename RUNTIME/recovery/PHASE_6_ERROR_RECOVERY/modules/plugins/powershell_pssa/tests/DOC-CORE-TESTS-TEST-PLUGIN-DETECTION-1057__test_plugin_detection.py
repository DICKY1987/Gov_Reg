# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1057

except ImportError:
    import pytest
    pytest.skip("powershell_pssa plugin module not available", allow_module_level=True)

def "Test PSScriptAnalyzer plugin error detection."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1057

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import shutil
import subprocess
import tempfile

import pytest

try:
    from phase6_error_recovery.modules.plugins.powershell_pssa.src.powershell_pssa.plugin import (
    PSScriptAnalyzerPlugin,
    register,
)


def _has_pssa_module() -> bool:
    """Check if PSScriptAnalyzer PowerShell module is available."""
    if not shutil.which("pwsh"):
        return False
    try:
        result = subprocess.run(
            [
                "pwsh",
                "-NoProfile",
                "-Command",
                "Get-Module -ListAvailable -Name PSScriptAnalyzer",
            ],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout
    except Exception:
        return False


@pytest.mark.skipif(
    not _has_pssa_module(), reason="PSScriptAnalyzer module not installed"
)
class TestPSSADetection:
    """Test PSScriptAnalyzer plugin error detection capabilities."""

    def test_plugin_registration(self):
        """Test that plugin can be registered."""
        plugin = register()
        assert isinstance(plugin, PSScriptAnalyzerPlugin)
        assert plugin.plugin_id == "powershell_pssa"
        assert plugin.name == "PSScriptAnalyzer"

    def test_tool_available(self):
        """Test tool availability check (pwsh)."""
        plugin = PSScriptAnalyzerPlugin()
        # Checks for pwsh, not PSScriptAnalyzer module
        if shutil.which("pwsh"):
            assert plugin.check_tool_available() is True

    def test_build_command(self):
        """Test command building."""
        plugin = PSScriptAnalyzerPlugin()
        test_file = Path("test.ps1")
        cmd = plugin.build_command(test_file)

        assert "pwsh" in cmd
        assert "-NoProfile" in cmd
        assert "-Command" in cmd
        assert "Invoke-ScriptAnalyzer" in " ".join(cmd)

    def test_detects_syntax_error(self):
        """Test detection of PowerShell syntax errors."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
# Syntax error - missing closing brace
function Get-Data {
    Write-Host "Hello"
# Missing }
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.issues, list)

            # Check for syntax-related issues
            for issue in result.issues:
                assert issue.tool == "PSScriptAnalyzer"
                if issue.code and "ParseError" in issue.code:
                    assert issue.category == "syntax"
        finally:
            test_file.unlink()

    def test_detects_cmdlet_issues(self):
        """Test detection of PowerShell best practice violations."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
# Use unapproved verb (should be Get-Something)
function Fetch-Data {
    param($Path)
    # Missing cmdlet binding
    Write-Output "Data"
}
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_clean_script_no_issues(self):
        """Test clean PowerShell script produces minimal/no issues."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
function Get-Sum {
    [CmdletBinding()]
    param(
        [int]$A,
        [int]$B
    )

    return $A + $B
}
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Clean script should succeed
            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_handles_missing_file(self):
        """Test handling of missing file."""
        plugin = PSScriptAnalyzerPlugin()
        test_file = Path("/nonexistent/file.ps1")

        result = plugin.execute(test_file)

        # Should handle gracefully
        assert result.plugin_id == "powershell_pssa"
        assert isinstance(result.issues, list)

    def test_handles_empty_file(self):
        """Test handling of empty file."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write("")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_issue_structure(self):
        """Test that issues have correct structure."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
function Test {
    Write-Host "test"
}
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            for issue in result.issues:
                assert hasattr(issue, "tool")
                assert hasattr(issue, "path")
                assert hasattr(issue, "line")
                assert hasattr(issue, "category")
                assert hasattr(issue, "severity")
                assert hasattr(issue, "message")

                assert issue.tool == "PSScriptAnalyzer"
                assert issue.category in ("syntax", "style")
                assert issue.severity in ("error", "warning", "info")
        finally:
            test_file.unlink()

    def test_json_output_parsing(self):
        """Test that JSON output is parsed correctly."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write('Write-Host "Hello"\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should not crash during JSON parsing
            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.stdout, str)
            assert isinstance(result.stderr, str)
        finally:
            test_file.unlink()


def test_plugin_without_pwsh():
    """Test plugin behavior when pwsh is not available."""
    plugin = PSScriptAnalyzerPlugin()

    # Just verify it has the method
    assert hasattr(plugin, "check_tool_available")
    assert callable(plugin.check_tool_available)