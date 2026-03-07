# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1074

except ImportError:
    import pytest
    pytest.skip("python_pylint plugin module not available", allow_module_level=True)

def "Tests for pylint plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1074

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_pylint.plugin import PylintPlugin


def test_pylint_empty_file():
    """Test pylint on empty file."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_syntax_error():
    """Test pylint on file with syntax error."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_missing_file():
    """Test pylint on non-existent file."""
    plugin = PylintPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_pylint"


def test_pylint_unicode_content():
    """Test pylint on file with unicode content."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            '''"""Module with unicode."""


def func():
    """Function."""
    text = '你好世界'
    return text
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_large_file():
    """Test pylint on large file."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module."""\n\n')
        for i in range(500):
            f.write(f"VAR_{i} = {i}\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_result_has_stdout():
    """Test that result contains stdout."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module."""\n')
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
    finally:
        test_file.unlink()


def test_pylint_multiline_function():
    """Test pylint on multiline function."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""


def long_function(
    arg1,
    arg2,
    arg3,
):
    """Function."""
    result = arg1 + arg2 + arg3
    return result
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_class_definition():
    """Test pylint on class definition."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""


class MyClass:
    """Class docstring."""

    def __init__(self):
        """Init."""
        self.value = 42
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_import_statement():
    """Test pylint with import statements."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""
import os

def func():
    """Function."""
    return os.path.exists('.')
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_usage_error_handling():
    """Test pylint usage error bit handling."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('"""Module."""\n')
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "success")
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()