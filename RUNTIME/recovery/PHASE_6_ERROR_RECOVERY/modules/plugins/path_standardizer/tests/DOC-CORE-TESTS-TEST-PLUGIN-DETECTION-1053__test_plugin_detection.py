# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1053

except ImportError:
    import pytest
    pytest.skip("path_standardizer plugin module not available", allow_module_level=True)

class "Test Path Standardizer plugin validation."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1053

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

try:
    from phase6_error_recovery.modules.plugins.path_standardizer.src.path_standardizer.plugin import (
    normalize_path,
    parse_violations,
    validate_paths,
)


class TestPathStandardizer:
    """Test Path Standardizer plugin path validation."""

    def test_normalize_windows_path(self):
        """Test normalization of Windows paths."""
        # Windows path with drive letter
        assert normalize_path("C:\\Users\\test\\file.py") == "Users/test/file.py"
        assert normalize_path("C:/Users/test/file.py") == "Users/test/file.py"

        # Path without drive letter
        assert normalize_path("Users\\test\\file.py") == "Users/test/file.py"

    def test_normalize_unix_path(self):
        """Test normalization of Unix paths."""
        assert normalize_path("/home/user/file.py") == "home/user/file.py"
        assert normalize_path("./relative/path.py") == "relative/path.py"

    def test_normalize_removes_multiple_slashes(self):
        """Test that multiple slashes are collapsed."""
        assert normalize_path("path//to///file.py") == "path/to/file.py"

    def test_parse_violations_with_file_line(self):
        """Test parsing violations with file:line format."""
        output = "src/test.py:42: Path violation message"
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["file"] == "src/test.py"
        assert violations[0]["line"] == 42
        assert "violation" in violations[0]["message"].lower()
        assert violations[0]["category"] == "path_standard"
        assert violations[0]["severity"] == "warning"

    def test_parse_violations_with_file_dash_message(self):
        """Test parsing violations with file - message format."""
        output = "src/test.py - Uses backslashes"
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["file"] == "src/test.py"
        assert "backslashes" in violations[0]["message"].lower()

    def test_parse_violations_plain_message(self):
        """Test parsing plain violation messages."""
        output = "Path standard violation detected"
        violations = parse_violations(output, default_file="test.py")

        assert len(violations) == 1
        assert violations[0]["message"] == "Path standard violation detected"
        assert violations[0]["file"] == "test.py"
        assert violations[0]["line"] == 0

    def test_parse_violations_multiple_lines(self):
        """Test parsing multiple violation lines."""
        output = """src/test.py:10: Violation 1
src/other.py:20: Violation 2
src/third.py - Violation 3"""
        violations = parse_violations(output)

        assert len(violations) == 3
        assert violations[0]["file"] == "src/test.py"
        assert violations[1]["file"] == "src/other.py"
        assert violations[2]["file"] == "src/third.py"

    def test_parse_violations_empty_output(self):
        """Test parsing empty output."""
        violations = parse_violations("")
        assert violations == []

    def test_parse_violations_whitespace_only(self):
        """Test parsing whitespace-only output."""
        violations = parse_violations("   \n   \n")
        assert violations == []

    def test_validate_paths_structure(self):
        """Test validate_paths returns correct structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = str(f.name)

        try:
            # Validate without project root scripts (will skip check)
            result = validate_paths([test_file], "/nonexistent", autofix=False)

            assert "tool" in result
            assert result["tool"] == "path_standardizer"
            assert "errors" in result
            assert isinstance(result["errors"], list)
        finally:
            Path(test_file).unlink()

    def test_validate_paths_returns_empty_when_no_check_script(self):
        """Test that missing check script returns empty errors."""
        result = validate_paths(["test.py"], "/nonexistent", autofix=False)

        assert result["tool"] == "path_standardizer"
        assert result["errors"] == []


def test_normalize_path_edge_cases():
    """Test path normalization edge cases."""
    # Empty path
    assert normalize_path("") == ""

    # Just a filename
    assert normalize_path("file.py") == "file.py"

    # Current directory
    assert normalize_path("./file.py") == "file.py"