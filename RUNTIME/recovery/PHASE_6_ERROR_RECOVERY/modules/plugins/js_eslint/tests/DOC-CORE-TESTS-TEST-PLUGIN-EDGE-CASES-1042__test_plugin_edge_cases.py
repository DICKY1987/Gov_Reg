# DOC_LINK: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1042
"""Tests for eslint plugin edge cases and error handling."""
# DOC_ID: DOC-CORE-TESTS-TEST-PLUGIN-EDGE-CASES-1042


import pytest

try:
    import tempfile


    from js_eslint.plugin import ESLintPlugin


    def test_eslint_empty_file():
        """Test eslint on empty file."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_syntax_error():
        """Test eslint on file with syntax error."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("function test(\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_missing_file():
        """Test eslint on non-existent file."""
        plugin = ESLintPlugin()
        test_file = Path("nonexistent_file_xyz.js")
        result = plugin.execute(test_file)
        assert result.plugin_id == "js_eslint"


    def test_eslint_unicode_content():
        """Test eslint on file with unicode content."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write("const message = '你好世界';\nconsole.log(message);\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_large_file():
        """Test eslint on large file."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            for i in range(500):
                f.write(f"const VAR_{i} = {i};\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_result_fields():
        """Test all result fields are present."""
        plugin = ESLintPlugin()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const x = 42;\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert hasattr(result, "stdout")
            assert hasattr(result, "stderr")
            assert hasattr(result, "returncode")
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_class_syntax():
        """Test eslint on ES6 class syntax."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("class MyClass {\n  constructor() {\n    this.value = 42;\n  }\n}\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_async_function():
        """Test eslint on async function."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(
                "async function fetchData() {\n  return await Promise.resolve(42);\n}\n"
            )
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_destructuring():
        """Test eslint on destructuring syntax."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const { a, b } = { a: 1, b: 2 };\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()


    def test_eslint_template_literals():
        """Test eslint on template literals."""
        plugin = ESLintPlugin()
        if not plugin.check_tool_available():
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const name = 'World';\nconst message = `Hello ${name}`;\n")
            f.flush()
            test_file = Path(f.name)

        try:
            result = plugin.execute(test_file)
            assert result.plugin_id == "js_eslint"
        finally:
            test_file.unlink()

except ImportError as e:
    pytest.skip(f"js_eslint plugin not available: {e}", allow_module_level=True)