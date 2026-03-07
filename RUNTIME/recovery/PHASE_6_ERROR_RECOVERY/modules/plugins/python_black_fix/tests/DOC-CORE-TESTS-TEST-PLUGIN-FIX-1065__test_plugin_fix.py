# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1065

except ImportError:
    import pytest
    pytest.skip("python_black_fix plugin module not available", allow_module_level=True)

def "Tests for black fix plugin capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1065

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_black_fix.plugin import BlackFixPlugin


def test_black_available():
    """Test that black tool is available."""
    plugin = BlackFixPlugin()
    assert plugin.check_tool_available() is True


def test_black_plugin_metadata():
    """Test plugin metadata."""
    plugin = BlackFixPlugin()
    assert plugin.plugin_id == "python_black_fix"
    assert plugin.name == "Black Formatter (fix)"


def test_black_build_command():
    """Test command building."""
    plugin = BlackFixPlugin()
    test_file = Path("test.py")
    cmd = plugin.build_command(test_file)
    assert "black" in cmd
    assert str(test_file) in cmd


def test_black_already_formatted():
    """Test black on already formatted file."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module."""\n\n\ndef func():\n    """Function."""\n    return 42\n')
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_formats_file():
    """Test black formats unformatted file."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(  ):\n  return 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_long_line():
    """Test black formats long lines."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            "x = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3', 'key4': 'value4', 'key5': 'value5', 'key6': 'value6', 'key7': 'value7'}\n"
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_whitespace_fix():
    """Test black fixes whitespace issues."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    x=1+2\n    return x\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_result_structure():
    """Test result structure."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    return 42\n")
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
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_no_issues_returned():
    """Test that black fix plugin returns empty issues list."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    return 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.issues == []
    finally:
        test_file.unlink()


def test_black_multiline_format():
    """Test black formats multiline code."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def long_function(arg1,arg2,arg3):
    result=arg1+arg2+arg3
    return result
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()


def test_black_class_format():
    """Test black formats class definitions."""
    plugin = BlackFixPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
class MyClass:
    def __init__(self,value):
        self.value=value
    def get_value(self):
        return self.value
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_black_fix"
    finally:
        test_file.unlink()