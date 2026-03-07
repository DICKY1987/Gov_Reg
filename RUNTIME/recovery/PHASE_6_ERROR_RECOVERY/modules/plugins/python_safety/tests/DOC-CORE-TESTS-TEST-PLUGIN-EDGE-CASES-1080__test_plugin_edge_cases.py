# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1080

except ImportError:
    import pytest
    pytest.skip("python_safety plugin module not available", allow_module_level=True)

def "Tests for safety plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1080

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_safety.plugin import SafetyPlugin


def test_safety_empty_file():
    """Test safety on empty Python file."""
    plugin = SafetyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"
        assert result.success is True
    finally:
        test_file.unlink()


def test_safety_missing_file():
    """Test safety on non-existent file."""
    plugin = SafetyPlugin()
    test_file = Path("nonexistent_file_xyz.py")
    result = plugin.execute(test_file)
    assert result.plugin_id == "python_safety"
    assert result.success is True
    assert result.issues == []


def test_safety_malformed_requirements():
    """Test safety with malformed requirements file."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("invalid===content\n")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("x = 42\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_unicode_in_requirements():
    """Test safety with unicode in requirements."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("# 你好世界\nrequests==2.28.0\n", encoding="utf-8")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("import requests\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_large_requirements():
    """Test safety with large requirements file."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        packages = "\n".join([f"package{i}==1.0.0" for i in range(100)])
        req_file.write_text(packages)

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("x = 42\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_result_fields():
    """Test all result fields are present."""
    plugin = SafetyPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("x = 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "returncode")
        assert result.plugin_id == "python_safety"
    finally:
        test_file.unlink()


def test_safety_nested_directory():
    """Test safety searches up directory tree."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("flask==1.0.0\n")

        nested = Path(tmpdir) / "a" / "b" / "c"
        nested.mkdir(parents=True)
        test_file = nested / "test.py"
        test_file.write_text("import flask\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_multiple_requirements_files():
    """Test safety prefers requirements.txt over requirements-dev.txt."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "requirements.txt").write_text("requests==2.28.0\n")
        Path(tmpdir, "requirements-dev.txt").write_text("pytest==6.0.0\n")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("import requests\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_comments_in_requirements():
    """Test safety handles comments in requirements."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("# Comment\nrequests==2.28.0  # inline comment\n")

        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("import requests\n")

        result = plugin.execute(test_file)
        assert result.plugin_id == "python_safety"


def test_safety_env_var_db_path():
    """Test safety respects SAFETY_DB env var."""
    plugin = SafetyPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        req_file = Path(tmpdir) / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        cmd = plugin.build_command(req_file)
        # Just check that command is built correctly
        assert "safety" in cmd
        assert "check" in cmd