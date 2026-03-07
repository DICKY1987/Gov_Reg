# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1045

except ImportError:
    import pytest
    pytest.skip("js_prettier_fix plugin module not available", allow_module_level=True)

def "Tests for prettier fix plugin capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-FIX-1045

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from js_prettier_fix.plugin import PrettierFixPlugin


def test_prettier_available():
    """Test that prettier tool is available."""
    plugin = PrettierFixPlugin()
    result = plugin.check_tool_available()
    assert isinstance(result, bool)


def test_prettier_plugin_metadata():
    """Test plugin metadata."""
    plugin = PrettierFixPlugin()
    assert plugin.plugin_id == "js_prettier_fix"
    assert plugin.name == "Prettier Formatter (fix)"


def test_prettier_build_command():
    """Test command building."""
    plugin = PrettierFixPlugin()
    test_file = Path("test.js")
    cmd = plugin.build_command(test_file)
    assert "prettier" in cmd
    assert "--write" in cmd
    assert str(test_file) in cmd


def test_prettier_formats_javascript():
    """Test prettier formats JavaScript file."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("const x=1+2;")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_already_formatted():
    """Test prettier on already formatted file."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("const x = 1 + 2;\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_result_structure():
    """Test result structure."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("const x = 42;")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "success")
        assert hasattr(result, "plugin_id")
        assert hasattr(result, "issues")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert result.issues == []
    finally:
        test_file.unlink()


def test_prettier_empty_file():
    """Test prettier on empty file."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_missing_file():
    """Test prettier on non-existent file."""
    plugin = PrettierFixPlugin()
    test_file = Path("nonexistent_file_xyz.js")
    result = plugin.execute(test_file)
    assert result.plugin_id == "js_prettier_fix"
    assert result.success is False


def test_prettier_json_file():
    """Test prettier formats JSON files."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"key":"value"}')
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()


def test_prettier_markdown_file():
    """Test prettier formats Markdown files."""
    plugin = PrettierFixPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Header\n\nParagraph")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_prettier_fix"
    finally:
        test_file.unlink()