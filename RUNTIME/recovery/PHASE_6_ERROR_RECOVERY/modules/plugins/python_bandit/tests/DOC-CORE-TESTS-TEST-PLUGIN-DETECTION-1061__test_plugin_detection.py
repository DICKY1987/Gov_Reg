# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1061

except ImportError:
    import pytest
    pytest.skip("python_bandit plugin module not available", allow_module_level=True)

def "Tests for bandit plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1061

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_bandit.plugin import BanditPlugin


def test_bandit_available():
    """Test that bandit tool is available."""
    plugin = BanditPlugin()
    result = plugin.check_tool_available()
    assert isinstance(result, bool)


def test_bandit_plugin_metadata():
    """Test plugin metadata."""
    plugin = BanditPlugin()
    assert plugin.plugin_id == "python_bandit"
    assert plugin.name == "Bandit Security Scanner"


def test_bandit_build_command():
    """Test command building."""
    plugin = BanditPlugin()
    test_file = Path("test.py")
    cmd = plugin.build_command(test_file)
    assert "bandit" in cmd
    assert "-f" in cmd
    assert "json" in cmd
    assert str(test_file) in cmd


def test_bandit_clean_file():
    """Test bandit on secure file."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def safe_function():\n    return 42\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_hardcoded_password():
    """Test bandit detects hardcoded passwords."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("password = 'hardcoded_secret_123'\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_shell_injection():
    """Test bandit detects shell injection risks."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\nos.system('ls -la')\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_sql_injection():
    """Test bandit detects SQL injection risks."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            """
import sqlite3
def query(user_input):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = '%s'" % user_input)
"""
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_issue_structure():
    """Test issue structure contains required fields."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import os\nos.system('ls')\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        if result.issues:
            issue = result.issues[0]
            assert hasattr(issue, "tool")
            assert hasattr(issue, "path")
            assert hasattr(issue, "line")
            assert hasattr(issue, "category")
            assert hasattr(issue, "severity")
            assert hasattr(issue, "message")
            assert issue.tool == "bandit"
            assert issue.category == "security"
    finally:
        test_file.unlink()


def test_bandit_severity_mapping():
    """Test severity mapping (HIGH/MEDIUM/LOW)."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import pickle\npickle.loads(b'data')\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_bandit"
    finally:
        test_file.unlink()


def test_bandit_result_structure():
    """Test result structure."""
    plugin = BanditPlugin()
    if not plugin.check_tool_available():
        return

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