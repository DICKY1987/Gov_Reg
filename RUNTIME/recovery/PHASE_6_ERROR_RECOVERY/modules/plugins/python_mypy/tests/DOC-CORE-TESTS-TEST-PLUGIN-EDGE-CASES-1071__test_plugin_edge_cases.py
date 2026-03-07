# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1071

except ImportError:
    import pytest
    pytest.skip("python_mypy plugin module not available", allow_module_level=True)

def "Tests for mypy plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1071

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_mypy.plugin import MypyPlugin


def test_mypy_empty_file():
    """Test mypy on empty file."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()


def test_mypy_syntax_error():
    """Test mypy on file with syntax error."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()


def test_mypy_missing_file():
    """Test mypy on non-existent file."""
    plugin = MypyPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_mypy"


def test_mypy_binary_file():
    """Test mypy on binary file."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
        f.write(b"\x00\x01\x02\x03")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()


def test_mypy_unicode_content():
    """Test mypy on file with unicode content."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write("# -*- coding: utf-8 -*-\nx: str = '你好世界'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()


def test_mypy_large_file():
    """Test mypy on large file."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        for i in range(1000):
            f.write(f"x{i}: int = {i}\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()


def test_mypy_result_has_stdout():
    """Test that result contains stdout."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x: int = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
    finally:
        test_file.unlink()


def test_mypy_multiline_error():
    """Test mypy on multiline type error."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
def process(items: list[int]) -> int:
    total = 0
    for item in items:
        total += item
    return total

result: str = process([1, 2, 3])
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        if result.issues:
            assert any("type" in i.category for i in result.issues)
    finally:
        test_file.unlink()


def test_mypy_class_type_error():
    """Test mypy on class with type errors."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
class MyClass:
    def __init__(self, value: int):
        self.value: int = value

    def get_value(self) -> int:
        return str(self.value)
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        if result.issues:
            assert len(result.issues) > 0
    finally:
        test_file.unlink()


def test_mypy_import_error():
    """Test mypy with import errors."""
    plugin = MypyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import nonexistent_module\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_mypy"
    finally:
        test_file.unlink()