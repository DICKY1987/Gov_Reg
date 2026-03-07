# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1039

except ImportError:
    import pytest
    pytest.skip("json_jq plugin module not available", allow_module_level=True)

def "Tests for jq edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1039

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from json_jq.plugin import JsonJqPlugin


def test_jq_missing_file():
    plugin = JsonJqPlugin()
    result = plugin.execute(Path("nonexistent.json"))
    assert result.plugin_id == "json_jq"


def test_jq_unicode():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write('{"message": "你好世界"}')
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        Path(f.name).unlink()


def test_jq_large_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"data": [')
        for i in range(500):
            f.write(f'{{"id": {i}}},')
        f.write('{"id": 500}]}')
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        Path(f.name).unlink()


def test_jq_nested_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"parent": {"child": {"grandchild": "value"}}}')
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        Path(f.name).unlink()


def test_jq_array_json():
    plugin = JsonJqPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("[1, 2, 3, 4, 5]")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.success is True
        Path(f.name).unlink()