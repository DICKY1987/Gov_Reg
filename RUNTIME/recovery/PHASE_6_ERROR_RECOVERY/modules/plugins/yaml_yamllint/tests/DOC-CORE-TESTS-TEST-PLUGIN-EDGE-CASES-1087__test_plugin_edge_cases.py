# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1087

except ImportError:
    import pytest
    pytest.skip("yaml_yamllint plugin module not available", allow_module_level=True)

def "Tests for yamllint edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1087

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from yaml_yamllint.plugin import YamllintPlugin


def test_yamllint_missing_file():
    plugin = YamllintPlugin()
    result = plugin.execute(Path("nonexistent.yaml"))
    assert result.plugin_id == "yaml_yamllint"


def test_yamllint_unicode():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("key: '你好世界'\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_large_file():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        for i in range(500):
            f.write(f"key{i}: value{i}\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_nested_structure():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("parent:\n  child:\n    grandchild: value\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()


def test_yamllint_lists():
    plugin = YamllintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("items:\n  - item1\n  - item2\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "yaml_yamllint"
        Path(f.name).unlink()