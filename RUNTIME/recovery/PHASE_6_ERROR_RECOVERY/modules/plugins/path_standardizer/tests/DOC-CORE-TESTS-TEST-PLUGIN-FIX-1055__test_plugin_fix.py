# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1055

except ImportError:
    import pytest
    pytest.skip("path_standardizer plugin module not available", allow_module_level=True)

class "Test Path Standardizer plugin fix capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1055

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

try:
    from phase6_error_recovery.modules.plugins.path_standardizer.src.path_standardizer.plugin import (
    validate_paths,
)


class TestPathStandardizerFix:
    """Test Path Standardizer auto-fix capabilities."""

    def test_validate_with_autofix_flag(self):
        """Test that autofix flag is accepted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = str(f.name)

        try:
            # Test with autofix=True (will skip if fix script doesn't exist)
            result = validate_paths([test_file], "/nonexistent", autofix=True)

            assert result["tool"] == "path_standardizer"
            assert isinstance(result["errors"], list)
        finally:
            Path(test_file).unlink()

    def test_validate_without_autofix(self):
        """Test validation without autofix."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x = 1\n")
            f.flush()
            test_file = str(f.name)

        try:
            result = validate_paths([test_file], "/nonexistent", autofix=False)

            assert result["tool"] == "path_standardizer"
            assert isinstance(result["errors"], list)
        finally:
            Path(test_file).unlink()

    def test_fix_requires_fix_script(self):
        """Test that fix requires fix script to exist."""
        # Without fix script, validation continues but no fixes applied
        result = validate_paths(["test.py"], "/nonexistent", autofix=True)

        # Should return gracefully
        assert result["tool"] == "path_standardizer"


def test_path_standardizer_has_autofix_capability():
    """Document that Path Standardizer has autofix capability."""
    # When fix-path-standards.sh script exists, can auto-fix
    # This is tested via the autofix parameter

    result = validate_paths([], "/nonexistent", autofix=False)
    assert result["tool"] == "path_standardizer"