# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1054

except ImportError:
    import pytest
    pytest.skip("path_standardizer plugin module not available", allow_module_level=True)

class "Test Path Standardizer plugin edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1054

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from phase6_error_recovery.modules.plugins.path_standardizer.src.path_standardizer.plugin import (
    normalize_path,
    parse_violations,
)


class TestPathStandardizerEdgeCases:
    """Test Path Standardizer edge cases."""

    def test_normalize_with_double_backslashes(self):
        """Test path with double backslashes."""
        assert normalize_path("C:\\\\path\\\\to\\\\file.py") == "path/to/file.py"

    def test_normalize_mixed_separators(self):
        """Test path with mixed separators."""
        assert normalize_path("C:\\path/to\\file.py") == "path/to/file.py"

    def test_normalize_trailing_slashes(self):
        """Test path with trailing slashes."""
        result = normalize_path("path/to/dir/")
        assert result == "path/to/dir/"  # Trailing slash preserved

    def test_normalize_unicode_path(self):
        """Test path with unicode characters."""
        path = "C:\\Users\\测试\\文件.py"
        result = normalize_path(path)
        assert "测试" in result
        assert "文件.py" in result

    def test_normalize_very_long_path(self):
        """Test very long path."""
        long_path = "C:\\" + "\\".join([f"dir{i}" for i in range(100)]) + "\\file.py"
        result = normalize_path(long_path)
        assert "dir0" in result
        assert "dir99" in result
        assert "file.py" in result

    def test_parse_violations_with_windows_drive_in_message(self):
        """Test parsing when path has Windows drive letter."""
        output = "C:\\Users\\test\\file.py:10: Violation"
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["line"] == 10
        # Drive letter should be normalized
        assert "Users/test/file.py" in violations[0]["file"]

    def test_parse_violations_with_colon_in_message(self):
        """Test parsing when message contains colons."""
        output = "file.py:42: Error: Path contains: invalid characters"
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["line"] == 42
        assert "invalid characters" in violations[0]["message"]

    def test_parse_violations_malformed_line_number(self):
        """Test parsing with malformed line number."""
        output = "file.py:abc: Violation"
        violations = parse_violations(output)

        # Should fall back to plain message parsing
        assert len(violations) == 1

    def test_parse_violations_empty_lines(self):
        """Test parsing with many empty lines."""
        output = "\n\n\nfile.py:10: Error\n\n\n"
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["file"] == "file.py"

    def test_parse_violations_tabs_and_spaces(self):
        """Test parsing with tabs and extra spaces."""
        output = "\t  file.py:10:  \t Error message  "
        violations = parse_violations(output)

        assert len(violations) == 1
        assert violations[0]["message"].strip() == "Error message"


def test_normalize_path_special_cases():
    """Test special path normalization cases."""
    # Dot-dot navigation
    assert "../file.py" in normalize_path("../file.py")

    # Network path (UNC)
    # Note: normalize_path may not preserve \\ prefix
    result = normalize_path("\\\\server\\share\\file.py")
    assert "file.py" in result