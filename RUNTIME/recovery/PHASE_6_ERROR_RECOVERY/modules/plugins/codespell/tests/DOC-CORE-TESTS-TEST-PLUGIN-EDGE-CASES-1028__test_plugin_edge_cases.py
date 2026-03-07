# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1028
"""Tests for codespell plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1028


import pytest

try:
    import tempfile


    from codespell.plugin import CodespellPlugin


    def test_codespell_empty_file():
        """Test codespell on empty file."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_missing_file():
        """Test codespell on non-existent file."""
        plugin = CodespellPlugin()
        test_file = Path("nonexistent_file_xyz.txt")
        result = plugin.execute(test_file)
        assert result.plugin_id == "codespell"


    def test_codespell_binary_file():
        """Test codespell on binary file."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_unicode_content():
        """Test codespell on file with unicode content."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("This is 你好世界 unicode text.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_large_file():
        """Test codespell on large file."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for i in range(1000):
                f.write(f"Line {i} of text content.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_result_fields():
        """Test all result fields are present."""
        plugin = CodespellPlugin()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert hasattr(result, "stdout")
            assert hasattr(result, "stderr")
            assert hasattr(result, "returncode")
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_mixed_case():
        """Test codespell with mixed case typos."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is THe test.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_markdown_file():
        """Test codespell on markdown file."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Header\n\nThis is a teh typo in markdown.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_python_file():
        """Test codespell on Python file."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('"""This is teh docstring."""\ndef func():\n    pass\n')
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_camelcase_words():
        """Test codespell with camelCase words."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("myVariableName is camelCase.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()


    def test_codespell_technical_terms():
        """Test codespell with technical terms."""
        plugin = CodespellPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("API endpoint configuration HTTP request.\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "codespell"
        finally:
            test_file.unlink()

except ImportError as e:
    pytest.skip(f"codespell plugin not available: {e}", allow_module_level=True)