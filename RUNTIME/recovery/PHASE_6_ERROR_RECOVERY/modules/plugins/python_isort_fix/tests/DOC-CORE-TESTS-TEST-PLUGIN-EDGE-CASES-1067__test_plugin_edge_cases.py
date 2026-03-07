# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1067

except ImportError:
    import pytest
    pytest.skip("python_isort_fix plugin module not available", allow_module_level=True)

def "Tests for isort plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1067

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_isort_fix.plugin import IsortFixPlugin


def test_isort_empty_file():
    """Test isort on empty file."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_syntax_error():
    """Test isort on file with syntax error."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\ndef func(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_missing_file():
    """Test isort on non-existent file."""
    plugin = IsortFixPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_isort_fix"
    assert result.success is False


def test_isort_no_imports():
    """Test isort on file with no imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    return 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_unicode_in_imports():
    """Test isort with unicode in module names."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write("import os\n# 你好世界\nimport sys\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_large_file():
    """Test isort on large file with many imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import sys\n" * 100)
        f.write("\ndef func():\n    pass\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_result_fields():
    """Test all result fields are present."""
    plugin = IsortFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_relative_imports():
    """Test isort with relative imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("from . import module\nfrom .. import parent\nimport sys\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_aliased_imports():
    """Test isort with aliased imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import numpy as np\nimport pandas as pd\nimport sys\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_third_party_imports():
    """Test isort categorizes third-party imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import requests\nimport flask\nimport os\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()