# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1086

except ImportError:
    import pytest
    pytest.skip("yaml_yamllint plugin module not available", allow_module_level=True)

def "Tests for yamllint plugin detection."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1086

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from yaml_yamllint.plugin import YamllintPlugin


def test_yamllint_available():
    plugin = YamllintPlugin()
    assert isinstance(plugin.check_tool_available(), bool)


def test_yamllint_metadata():
    plugin = YamllintPlugin()
    assert plugin.plugin_id == "yaml_yamllint"
    assert plugin.name == "yamllint"


def test_yamllint_build_command():
    plugin = YamllintPlugin()
    cmd = plugin.build_command(Path("test.yaml"))
    assert "yamllint" in cmd
    assert "-f" in cmd
    assert "parsable" in cmd


def test_yamllint_clean_file():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: value\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_syntax_error():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: [unclosed\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_result_structure():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: value\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert hasattr(result, "success")
        assert hasattr(result, "issues")
        Path(f.name).unlink()


def test_yamllint_empty_file():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_issue_structure():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key:value\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        for issue in result.issues:
            assert issue.tool == "yamllint"
        Path(f.name).unlink()