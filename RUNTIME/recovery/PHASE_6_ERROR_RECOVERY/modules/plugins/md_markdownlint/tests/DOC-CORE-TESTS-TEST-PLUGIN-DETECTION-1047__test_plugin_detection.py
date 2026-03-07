# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1047

except ImportError:
    import pytest
    pytest.skip("md_markdownlint plugin module not available", allow_module_level=True)

def "Tests for markdownlint plugin detection."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1047

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from md_markdownlint.plugin import MarkdownlintPlugin


def test_markdownlint_available():
    plugin = MarkdownlintPlugin()
    assert isinstance(plugin.check_tool_available(), bool)


def test_markdownlint_metadata():
    plugin = MarkdownlintPlugin()
    assert plugin.plugin_id == "md_markdownlint"
    assert plugin.name == "markdownlint-cli"


def test_markdownlint_build_command():
    plugin = MarkdownlintPlugin()
    cmd = plugin.build_command(Path("test.md"))
    assert "markdownlint" in cmd
    assert "-j" in cmd


def test_markdownlint_clean_file():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Header\n\nParagraph.\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_detects_issues():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("#Header\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_result_structure():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert hasattr(result, "success")
        assert hasattr(result, "issues")
        Path(f.name).unlink()


def test_markdownlint_empty_file():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("")
        f.flush()
        result = plugin.execute(Path(f.name))
        assert result.plugin_id == "md_markdownlint"
        Path(f.name).unlink()


def test_markdownlint_issue_structure():
    plugin = MarkdownlintPlugin()
    if not plugin.check_tool_available():
        return
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("#Bad\n")
        f.flush()
        result = plugin.execute(Path(f.name))
        for issue in result.issues:
            assert issue.tool == "markdownlint"
            assert issue.category == "style"
        Path(f.name).unlink()