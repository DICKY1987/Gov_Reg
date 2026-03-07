# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1073

except ImportError:
    import pytest
    pytest.skip("python_pylint plugin module not available", allow_module_level=True)

def "Tests for pylint plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1073

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile

.parent.parent / "src"))
try:
    from python_pylint.plugin import PylintPlugin


def test_pylint_available():
    """Test that pylint tool is available."""
    plugin = PylintPlugin()
    assert plugin.check_tool_available() is True


def test_pylint_plugin_metadata():
    """Test plugin metadata."""
    plugin = PylintPlugin()
    assert plugin.plugin_id == "python_pylint"
    assert plugin.name == "Pylint"


def test_pylint_build_command():
    """Test command building."""
    plugin = PylintPlugin()
    test_file = Path("test.py")
    cmd = plugin.build_command(test_file)
    assert "pylint" in cmd
    assert "--output-format=json" in cmd
    assert str(test_file) in cmd


def test_pylint_detects_style_issues():
    """Test pylint detects style issues."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def badFunction():\n  return 1\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_clean_file():
    """Test pylint on clean file."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module docstring."""


def good_function():
    """Function docstring."""
    return 42
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_missing_docstring():
    """Test pylint detects missing docstrings."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    pass\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_unused_variable():
    """Test pylint detects unused variables."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""


def func():
    """Function."""
    unused_var = 42
    return 1
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_undefined_variable():
    """Test pylint detects undefined variables."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""


def func():
    """Function."""
    return undefined_var
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
        if result.issues:
            assert len(result.issues) > 0
    finally:
        test_file.unlink()


def test_pylint_naming_convention():
    """Test pylint checks naming conventions."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '''"""Module."""


def BadFunctionName():
    """Function."""
    return 1
'''
        )
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()


def test_pylint_issue_structure():
    """Test issue structure contains required fields."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def func():\n    pass\n")
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
            assert issue.tool == "pylint"
    finally:
        test_file.unlink()


def test_pylint_severity_mapping():
    """Test that severity levels are correctly mapped."""
    plugin = PylintPlugin()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("import sys\n")
        f.flush()
        test_file = Path(f.name)

    try:
        result = plugin.execute(test_file)
        assert result.plugin_id == "python_pylint"
    finally:
        test_file.unlink()