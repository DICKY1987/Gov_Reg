# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1038

except ImportError:
    import pytest
    pytest.skip("json_jq plugin module not available", allow_module_level=True)

def "Tests for jq JSON plugin detection."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1038

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from json_jq.plugin import JsonJqPlugin


def test_jq_available():
    plugin = JsonJqPlugin()
    assert isinstance(plugin.check_tool_available(), bool)


def test_jq_metadata():
    plugin = JsonJqPlugin()
    assert plugin.plugin_id == "json_jq"
    assert plugin.name == "jq (JSON syntax)"


def test_jq_build_command():
    plugin = JsonJqPlugin()
    cmd = plugin.build_command(Path("test.json"))
    assert "jq" in cmd
    assert "empty" in cmd


def test_jq_valid_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"key": "value"}')
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        assert result.plugin_id == "json_jq"
        Path(f.name).unlink()


def test_jq_invalid_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"key": "unclosed}')
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is False
        assert result.plugin_id == "json_jq"
        assert len(result.issues) > 0
        Path(f.name).unlink()


def test_jq_result_structure():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{}")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert hasattr(result, "success")
        assert hasattr(result, "issues")
        Path(f.name).unlink()


def test_jq_empty_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{}")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        Path(f.name).unlink()


def test_jq_issue_structure():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("invalid")
        f.flush()
        result = plugin.execute(Path(f.name))
        for issue in result.issues:
            assert issue.tool == "jq"
            assert issue.category == "syntax"
            assert issue.severity == "error"
        Path(f.name).unlink()