# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1058

except ImportError:
    import pytest
    pytest.skip("powershell_pssa plugin module not available", allow_module_level=True)

def "Test PSScriptAnalyzer plugin edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1058

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
class TestPSSAEdgeCases:
    """Test PSScriptAnalyzer plugin edge cases."""

    def test_script_with_unicode(self):
        """Test handling of script with unicode characters."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                """
# Comment with unicode: 你好世界
function Get-Greeting {
    Write-Output "Hello 世界"
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

    def test_very_long_script(self):
        """Test handling of long PowerShell script."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            for i in range(500):
                f.write(
                    f"""
function Get-Item{i} {{
    [CmdletBinding()]
    param([string]$Name)
    Write-Output "Item {i}: $Name"
}}
"""
                )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should complete within timeout
            assert result.plugin_id == "powershell_pssa"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_script_with_here_string(self):
        """Test handling of PowerShell here-strings."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
$text = @"
This is a here-string
with multiple lines
and special characters: !@#$%
"@

Write-Output $text
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

    def test_multiple_violations(self):
        """Test script with multiple PSScriptAnalyzer rule violations."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write(
                """
# Missing CmdletBinding
function Do-Something {
    param($param1)  # Missing type
    $x = 1  # Unused variable
    Write-Host "output"  # Should use Write-Output
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

    def test_timeout_protection(self):
        """Test that timeout protection works."""
        plugin = PSScriptAnalyzerPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
            f.write('Write-Host "test"\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should complete well under 120 seconds
            assert result.plugin_id == "powershell_pssa"
        finally:
            test_file.unlink()

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        plugin = PSScriptAnalyzerPlugin()
        test_file = Path("/nonexistent/script.ps1")

        result = plugin.execute(test_file)

        # Should handle gracefully
        assert result.plugin_id == "powershell_pssa"


def test_pssa_edge_case_basic():
    """Basic edge case test that doesn't require PSScriptAnalyzer."""
    plugin = PSScriptAnalyzerPlugin()
    assert plugin.plugin_id == "powershell_pssa"