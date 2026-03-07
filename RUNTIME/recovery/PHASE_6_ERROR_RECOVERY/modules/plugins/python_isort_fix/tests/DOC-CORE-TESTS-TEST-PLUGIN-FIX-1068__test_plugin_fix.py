# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1068

except ImportError:
    import pytest
    pytest.skip("python_isort_fix plugin module not available", allow_module_level=True)

def "Tests for isort fix plugin capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1068

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_isort_fix.plugin import IsortFixPlugin


def test_isort_available():
    """Test that isort tool is available."""
    plugin = IsortFixPlugin()
    result = plugin.check_tool_available()
    assert isinstance(result, bool)


def test_isort_plugin_metadata():
    """Test plugin metadata."""
    plugin = IsortFixPlugin()
    assert plugin.plugin_id == "python_isort_fix"
    assert plugin.name == "isort Import Sorter (fix)"


def test_isort_build_command():
    """Test command building."""
    plugin = IsortFixPlugin()
    test_file = Path("test.py")
    cmd = plugin.build_command(test_file)
    assert "isort" in cmd
    assert str(test_file) in cmd


def test_isort_already_sorted():
    """Test isort on already sorted imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\nimport sys\n\ndef func():\n    pass\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_sorts_imports():
    """Test isort sorts unsorted imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import sys\nimport os\n\ndef func():\n    pass\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_multiple_import_groups():
    """Test isort organizes import groups."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            "from pathlib import Path\nimport os\nimport sys\n\ndef func():\n    pass\n"
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_result_structure():
    """Test result structure."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "success")
        assert hasattr(result, "plugin_id")
        assert hasattr(result, "issues")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
    finally:
        test_file.unlink()


def test_isort_no_issues_returned():
    """Test that isort fix plugin returns empty issues list."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.issues == []
    finally:
        test_file.unlink()


def test_isort_from_imports():
    """Test isort handles from imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            "from pathlib import Path\nfrom os import environ\n\ndef func():\n    pass\n"
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_mixed_imports():
    """Test isort with mixed import styles."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import sys\nfrom os import path\nimport os\n\ndef func():\n    pass\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()


def test_isort_multiline_imports():
    """Test isort handles multiline imports."""
    plugin = IsortFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            "from typing import (\n    List,\n    Dict,\n    Optional\n)\n\ndef func():\n    pass\n"
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_isort_fix"
    finally:
        test_file.unlink()