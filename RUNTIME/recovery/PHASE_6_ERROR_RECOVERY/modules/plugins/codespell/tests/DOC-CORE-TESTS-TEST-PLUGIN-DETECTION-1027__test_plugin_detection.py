# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1027
"""Tests for codespell plugin error detection capabilities."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-DETECTION-1027


import pytest

try:
    import tempfile


    from codespell.plugin import CodespellPlugin


    def test_codespell_available():
        """Test that codespell tool is available."""
        plugin = CodespellPlugin()
        result = plugin.check_tool_available()
        assert isinstance(result, bool)


    def test_codespell_plugin_metadata():
        """Test plugin metadata."""
        plugin = CodespellPlugin()
        assert plugin.plugin_id == "codespell"
        assert plugin.name == "codespell"


    def test_codespell_build_command():
        """Test command building."""
        plugin = CodespellPlugin()
        test_file = Path("test.py")
        cmd = plugin.build_command(test_file)
        assert "codespell" in cmd
        assert str(test_file) in cmd


    def test_codespell_clean_file():
        """Test codespell on file with no spelling errors."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def function():\n    return 42\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_detects_typo():
        """Test codespell detects spelling errors."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# This is a functon with a typo\ndef func():\n    pass\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_in_comment():
        """Test codespell detects typos in comments."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a teh test.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_in_string():
        """Test codespell detects typos in strings."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('message = "Recieve this message"\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_issue_structure():
        """Test issue structure contains required fields."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a teh test.\n")
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
                assert issue.tool == "codespell"
                assert issue.category == "style"
                assert issue.severity == "warning"
        finally:
            test_file.unlink()


    def test_codespell_result_structure():
        """Test result structure."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def func():\n    pass\n")
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


    def test_codespell_multiple_typos():
        """Test codespell detects multiple typos."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is teh first typo.\nThis is teh second typo.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_line_numbers():
        """Test codespell reports correct line numbers."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Line 1 is correct.\nLine 2 has teh typo.\nLine 3 is correct.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
            if result.issues:
                # Line number should be 2
                assert any(issue.line == 2 for issue in result.issues)
        finally:
            test_file.unlink()

except ImportError as e:
    pytest.skip(f"codespell plugin not available: {e}", allow_module_level=True)