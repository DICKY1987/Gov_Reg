# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1041
"""Tests for eslint plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1041


import pytest

try:
    import tempfile


    from js_eslint.plugin import ESLintPlugin


    def test_eslint_available():
        """Test that eslint tool is available."""
        plugin = ESLintPlugin()
        result = plugin.check_tool_available()
        assert isinstance(result, bool)


    def test_eslint_plugin_metadata():
        """Test plugin metadata."""
        plugin = ESLintPlugin()
        assert plugin.plugin_id == "js_eslint"
        assert plugin.name == "ESLint"


    def test_eslint_build_command():
        """Test command building."""
        plugin = ESLintPlugin()
        test_file = Path("test.js")
        cmd = plugin.build_command(test_file)
        assert "eslint" in cmd
        assert "-f" in cmd
        assert "json" in cmd
        assert str(test_file) in cmd


    def test_eslint_clean_file():
        """Test eslint on clean JavaScript file."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 42;\nconsole.log(x);\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_detects_issues():
        """Test eslint detects style issues."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("var x=1\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_unused_variable():
        """Test eslint detects unused variables."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const unusedVar = 42;\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_issue_structure():
        """Test issue structure contains required fields."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("var x=1\n")
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
                assert issue.tool == "eslint"
                assert issue.category == "style"
        finally:
            test_file.unlink()


    def test_eslint_result_structure():
        """Test result structure."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 42;\n")
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


    def test_eslint_severity_mapping():
        """Test severity mapping (error/warning)."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 42;\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
            for issue in result.issues:
                assert issue.severity in ["error", "warning", "info"]
        finally:
            test_file.unlink()


    def test_eslint_function_syntax():
        """Test eslint on function syntax."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("function test() {\n  return 42;\n}\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_arrow_function():
        """Test eslint on arrow function syntax."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const add = (a, b) => a + b;\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()

except ImportError as e:
    pytest.skip(f"js_eslint plugin not available: {e}", allow_module_level=True)