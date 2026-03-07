# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1077

except ImportError:
    import pytest
    pytest.skip("python_pyright plugin module not available", allow_module_level=True)

def "Tests for pyright plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1077

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_pyright.plugin import PyrightPlugin


def test_pyright_empty_file():
    """Test pyright on empty file."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_syntax_error():
    """Test pyright on file with syntax error."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_missing_file():
    """Test pyright on non-existent file."""
    plugin = PyrightPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_pyright"


def test_pyright_unicode_content():
    """Test pyright on file with unicode content."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write("x: str = '你好世界'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_large_file():
    """Test pyright on large file."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        for i in range(500):
            f.write(f"x{i}: int = {i}\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_complex_types():
    """Test pyright with complex type hints."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
from typing import List, Dict, Optional

def func(data: Dict[str, List[int]]) -> Optional[int]:
    if data:
        return data.get('key', [0])[0]
    return None
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_class_types():
    """Test pyright with class type checking."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
class MyClass:
    def __init__(self, value: int):
        self.value: int = value

    def get_value(self) -> int:
        return self.value
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_generic_types():
    """Test pyright with generic types."""
    plugin = PyrightPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()


def test_pyright_result_fields():
    """Test all result fields are present."""
    plugin = PyrightPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
        assert result.plugin_id == "python_pyright"
    finally:
        test_file.unlink()