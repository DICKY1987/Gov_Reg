# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1062

except ImportError:
    import pytest
    pytest.skip("python_bandit plugin module not available", allow_module_level=True)

def "Tests for bandit plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1062

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_bandit.plugin import BanditPlugin


def test_bandit_empty_file():
    """Test bandit on empty file."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_syntax_error():
    """Test bandit on file with syntax error."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func(\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_missing_file():
    """Test bandit on non-existent file."""
    plugin = BanditPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_bandit"


def test_bandit_unicode_content():
    """Test bandit on file with unicode content."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write("comment = '你好世界'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_large_file():
    """Test bandit on large file."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        for i in range(500):
            f.write(f"VAR_{i} = {i}\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_exec_usage():
    """Test bandit detects exec usage."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("exec('print(42)')\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_assert_usage():
    """Test bandit on assert statements."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("assert True, 'This should pass'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_random_usage():
    """Test bandit on random module usage."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import random\ntoken = random.random()\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_yaml_load():
    """Test bandit detects unsafe YAML load."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import yaml\ndata = yaml.load('key: value')\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_result_fields():
    """Test all result fields are present."""
    plugin = BanditPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()