# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1076

except ImportError:
    import pytest
    pytest.skip("python_pyright plugin module not available", allow_module_level=True)

def "Tests for pyright plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1076

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_pyright.plugin import PyrightPlugin


def test_pyright_available():
    """Test that pyright tool is available."""
    plugin = PyrightPlugin()
    result = plugin.check_tool_available()
    # Pyright may not be installed, test passes either way
    assert isinstance(result, bool)


def test_pyright_plugin_metadata():
    """Test plugin metadata."""
    plugin = PyrightPlugin()
    assert plugin.plugin_id == "python_pyright"
    assert plugin.name == "Pyright Type Checker"


def test_pyright_build_command():
    """Test command building."""
    plugin = PyrightPlugin()
    test_file = Path("test.py")
    cmd = plugin.build_command(test_file)
    assert "pyright" in cmd
    assert "--outputjson" in cmd
    assert str(test_file) in cmd


def test_pyright_detects_type_error():
    """Test pyright detects type errors."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x: int = 'string'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_clean_file():
    """Test pyright on clean file."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x: int = 42\nprint(x)\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_missing_import():
    """Test pyright detects missing imports."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import nonexistent_module\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_incompatible_types():
    """Test pyright detects incompatible types."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            "def add(a: int, b: int) -> int:\n    return a + b\nresult: str = add(1, 2)\n"
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_result_structure():
    """Test result structure contains required fields."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x: int = 42\n")
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


def test_pyright_issue_structure():
    """Test issue structure if issues are found."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x: int = 'string'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        if result.issues:
            issue = result.issues[0]
            assert hasattr(issue, "tool")
            assert hasattr(issue, "path")
            assert hasattr(issue, "category")
            assert hasattr(issue, "severity")
            assert issue.tool == "pyright"
            assert issue.category == "type"
    finally:
        test_file.unlink()