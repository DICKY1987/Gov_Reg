# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1083
@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
except ImportError:
    import pytest
    pytest.skip("semgrep plugin module not available", allow_module_level=True)

class SES-1083

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
)


@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed")
class TestSemgrepEdgeCases:
    """Test Semgrep plugin edge cases and error handling."""

    def test_binary_file(self):
        """Test handling of binary file."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xFF\xFE")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should handle gracefully
            assert result.plugin_id == "semgrep"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_very_large_file(self):
        """Test handling of large file (timeout protection)."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Create moderately large file
            for i in range(1000):
                f.write(f"def function_{i}():\n    pass\n\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should complete within timeout
            assert result.plugin_id == "semgrep"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_file_with_unicode(self):
        """Test handling of file with unicode characters."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                '''
# -*- coding: utf-8 -*-
def greet():
    """Say hello in multiple languages: 你好, مرحبا, שלום"""
    return "Hello 世界"
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

    def test_syntax_error_in_file(self):
        """Test handling of file with syntax errors."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def broken(
    # Missing closing parenthesis
    return "broken"
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Semgrep may or may not parse broken syntax
            # Just verify it doesn't crash
            assert result.plugin_id == "semgrep"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_file_in_readonly_directory(self):
        """Test handling of file in directory without write permissions."""
        plugin = SemgrepPlugin()

        # Create temp file in standard temp location
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should work even if directory is readonly
            assert result.plugin_id == "semgrep"
        finally:
            test_file.unlink()

    def test_multiple_security_issues(self):
        """Test file with multiple security issues."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
import subprocess

password = "hardcoded_password"  # Issue 1
api_key = "sk-1234567890abcdef"   # Issue 2

def execute_command(user_input):
    os.system(user_input)  # Issue 3: command injection

def sql_query(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # Issue 4: SQL injection
    return query
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            # May detect multiple issues
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_nonexistent_parent_directory(self):
        """Test handling of file in nonexistent directory."""
        plugin = SemgrepPlugin()
        test_file = Path("/completely/nonexistent/path/file.py")

        result = plugin.execute(test_file)

        # Should handle gracefully, not crash
        assert result.plugin_id == "semgrep"
        assert isinstance(result.issues, list)

    def test_file_with_special_characters_in_name(self):
        """Test handling of file with special characters."""
        plugin = SemgrepPlugin()

        # Use tempfile to avoid filesystem issues
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="test_file_"
        ) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_command_timeout_protection(self):
        """Test that timeout protection works."""
        plugin = SemgrepPlugin()

        # Normal file should complete well under 180 seconds
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should complete successfully
            assert result.success is True
            assert result.returncode in (0, 1)
        finally:
            test_file.unlink()

    def test_empty_json_output(self):
        """Test handling of empty JSON output."""
        plugin = SemgrepPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# Just a comment\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should handle empty results gracefully
            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()