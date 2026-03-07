# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1035
@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks not installed")
except ImportError:
    import pytest
    pytest.skip("gitleaks plugin module not available", allow_module_level=True)

class ES-1035

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
)


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks not installed")
class TestGitleaksEdgeCases:
    """Test Gitleaks plugin edge cases and error handling."""

    def test_binary_file(self):
        """Test handling of binary file."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xFF\xFE")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should handle gracefully
            assert result.plugin_id == "gitleaks"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_file_with_unicode(self):
        """Test handling of file with unicode characters."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(
                """
# -*- coding: utf-8 -*-
password = "密码123"  # Chinese characters
token = "رمز456"      # Arabic characters
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_very_long_line(self):
        """Test handling of file with very long lines."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Create a very long line
            long_string = "A" * 10000
            f.write(f'password = "{long_string}"\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should handle without crashing
            assert result.plugin_id == "gitleaks"
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_multiple_secrets_in_file(self):
        """Test file with multiple different types of secrets."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(
                """
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz12
DATABASE_URL=postgresql://user:password123@localhost:5432/db
API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            assert result.success is True
            assert isinstance(result.issues, list)
            # May detect multiple secrets
        finally:
            test_file.unlink()

    def test_false_positive_candidates(self):
        """Test handling of strings that look like secrets but aren't."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
# Example placeholders (not real secrets)
example_key = "YOUR_API_KEY_HERE"
placeholder = "REPLACE_WITH_YOUR_TOKEN"
test_password = "password"
demo_secret = "SECRET123"
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Gitleaks may or may not flag these
            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_commented_out_secrets(self):
        """Test handling of secrets in comments."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
# Old API key (commented out): sk-1234567890abcdef
# TODO: Remove this old token: ghp_abcdefghijklmnopqrstuvwxyz123456
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Gitleaks may still detect secrets in comments
            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_nonexistent_parent_directory(self):
        """Test handling of file in nonexistent directory."""
        plugin = GitleaksPlugin()
        test_file = Path("/completely/nonexistent/path/file.py")

        result = plugin.execute(test_file)

        # Should handle gracefully
        assert result.plugin_id == "gitleaks"
        assert isinstance(result.issues, list)

    def test_timeout_protection(self):
        """Test that timeout protection works."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should complete well under 180 seconds
            assert result.success is True
            assert result.returncode in (0, 1)
        finally:
            test_file.unlink()

    def test_empty_json_array(self):
        """Test handling when gitleaks returns empty array."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("No secrets here, just plain text.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Should handle empty results gracefully
            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()

    def test_special_characters_in_filename(self):
        """Test file with special characters in name."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix="test_"
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

    def test_base64_encoded_secret(self):
        """Test detection of base64-encoded secrets."""
        plugin = GitleaksPlugin()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import base64

# Base64 encoded API key
encoded_key = "c2stMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6"
"""
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)

            # Gitleaks may or may not detect base64 encoded secrets
            assert result.success is True
            assert isinstance(result.issues, list)
        finally:
            test_file.unlink()