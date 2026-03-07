# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1048

except ImportError:
    import pytest
    pytest.skip("md_markdownlint plugin module not available", allow_module_level=True)

def "Tests for markdownlint edge cases."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1048

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from md_markdownlint.plugin import MarkdownlintPlugin


def test_markdownlint_missing_file():
    plugin = MarkdownlintPlugin()
    result = plugin.execute(Path("nonexistent.md"))
    assert result.plugin_id == "md_markdownlint"


def test_markdownlint_unicode():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# 你好\n\n世界\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_large_file():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        for i in range(500):
            f.write(f"# Heading {i}\n\nContent {i}\n\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_code_blocks():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Code\n\n```python\ndef test():\n    pass\n```\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_lists():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# List\n\n- Item 1\n- Item 2\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()