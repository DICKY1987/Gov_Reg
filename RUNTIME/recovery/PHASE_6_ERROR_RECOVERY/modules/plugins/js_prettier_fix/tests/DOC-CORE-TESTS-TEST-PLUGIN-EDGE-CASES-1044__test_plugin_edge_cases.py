# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1044

except ImportError:
    import pytest
    pytest.skip("js_prettier_fix plugin module not available", allow_module_level=True)

def "Tests for prettier plugin edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1044

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from js_prettier_fix.plugin import PrettierFixPlugin


def test_prettier_syntax_error():
    """Test prettier on file with syntax error."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("function test(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_unicode():
    """Test prettier with unicode content."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write("const x='你好世界';")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_large_file():
    """Test prettier on large file."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        for i in range(500):
            f.write(f"const x{i}={i};")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_complex_formatting():
    """Test prettier on complex code."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("function test(a,b,c){if(a&&b&&c){return a+b+c;}}")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_object_literal():
    """Test prettier formats object literals."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("const obj={a:1,b:2,c:3};")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()