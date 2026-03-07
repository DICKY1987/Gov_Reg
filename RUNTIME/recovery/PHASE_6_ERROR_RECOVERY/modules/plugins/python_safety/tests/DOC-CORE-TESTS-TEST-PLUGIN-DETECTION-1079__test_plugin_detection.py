# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1079

except ImportError:
    import pytest
    pytest.skip("python_safety plugin module not available", allow_module_level=True)

def "Tests for safety plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1079

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_safety.plugin import SafetyPlugin


def test_safety_available():
    """Test that safety tool is available."""
    plugin = SafetyPlugin()
    result = plugin.check_tool_available()
    assert isinstance(result, bool)


def test_safety_plugin_metadata():
    """Test plugin metadata."""
    plugin = SafetyPlugin()
    assert plugin.plugin_id == "python_safety"
    assert plugin.name == "Safety Dependency Checker"


def test_safety_build_command():
    """Test command building."""
    plugin = SafetyPlugin()
    test_file = Path("requirements.txt")
    cmd = plugin.build_command(test_file)
    assert "safety" in cmd
    assert "check" in cmd
    assert "--json" in cmd


def test_safety_no_requirements_file():
    """Test safety when no requirements file exists."""
    plugin = SafetyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.success is True
        assert result.plugin_id == "python_safety"
        assert result.issues == []
    finally:
        test_file.unlink()


def test_safety_empty_requirements():
    """Test safety with empty requirements file."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("x = 42\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_safe_dependencies():
    """Test safety with safe dependencies."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("import requests\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_result_structure():
    """Test result structure."""
    plugin = SafetyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "success")
        assert hasattr(result, "plugin_id")
        assert hasattr(result, "issues")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
    finally:
        test_file.unlink()


def test_safety_issue_structure():
    """Test issue structure if vulnerabilities are found."""
    plugin = SafetyPlugin()
    # This test just verifies the structure, not actual vulnerabilities
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        for issue in result.issues:
            assert hasattr(issue, "tool")
            assert hasattr(issue, "path")
            assert hasattr(issue, "category")
            assert hasattr(issue, "severity")
            assert hasattr(issue, "message")
            assert issue.tool == "safety"
            assert issue.category == "security"
    finally:
        test_file.unlink()


def test_safety_finds_requirements_txt():
    """Test safety finds requirements.txt in parent directory."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("flask==1.0.0\n")

        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.py"
        test_file.write_text("import flask\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_requirements_dev_txt():
    """Test safety finds requirements-dev.txt."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements-dev.txt"
        req_file.write_text("pytest==6.0.0\n")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("import pytest\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"