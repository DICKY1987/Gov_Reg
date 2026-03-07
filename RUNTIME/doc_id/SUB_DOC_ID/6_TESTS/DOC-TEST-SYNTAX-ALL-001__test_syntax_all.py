# DOC_LINK: DOC-TEST-SYNTAX-ALL-001
# DOC_ID: DOC-TEST-SYNTAX-ALL-001
"""
Syntax Validation Tests for All Python Files
doc_id: DOC-TEST-SYNTAX-ALL-001
Ensures all Python files in the stable ID system are syntactically valid
"""

import pytest
from pathlib import Path
import py_compile
import sys

class TestPythonSyntax:
    """Test all Python files for syntax errors"""

    @pytest.fixture
    def base_path(self):
        """Base path for all stable ID files"""
        return Path(__file__).parent.parent

    def get_all_python_files(self, base_path):
        """Recursively find all Python files"""
        return list(base_path.rglob("*.py"))

    def test_all_python_files_compile(self, base_path):
        """Test that all Python files compile without syntax errors"""
        python_files = self.get_all_python_files(base_path)
        assert len(python_files) > 0, "No Python files found"

        failed_files = []
        for py_file in python_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                failed_files.append((py_file, str(e)))

        if failed_files:
            error_msg = "Syntax errors found in the following files:\n"
            for file, error in failed_files:
                error_msg += f"\n{file.relative_to(base_path)}:\n  {error}\n"
            pytest.fail(error_msg)

    def test_core_operations_syntax(self, base_path):
        """Test all core operations files specifically"""
        core_dirs = [
            base_path / "1_CORE_OPERATIONS",
            base_path / "trigger_id" / "1_CORE_OPERATIONS",
            base_path / "pattern_id" / "1_CORE_OPERATIONS",
        ]

        failed_files = []
        for core_dir in core_dirs:
            if core_dir.exists():
                for py_file in core_dir.glob("*.py"):
                    try:
                        py_compile.compile(str(py_file), doraise=True)
                    except py_compile.PyCompileError as e:
                        failed_files.append((py_file, str(e)))

        assert len(failed_files) == 0, f"Syntax errors in core operations: {failed_files}"

    def test_validation_syntax(self, base_path):
        """Test all validation files specifically"""
        validation_dirs = [
            base_path / "2_VALIDATION_FIXING",
            base_path / "trigger_id" / "2_VALIDATION_FIXING",
            base_path / "pattern_id" / "2_VALIDATION_FIXING",
        ]

        failed_files = []
        for val_dir in validation_dirs:
            if val_dir.exists():
                for py_file in val_dir.glob("*.py"):
                    try:
                        py_compile.compile(str(py_file), doraise=True)
                    except py_compile.PyCompileError as e:
                        failed_files.append((py_file, str(e)))

        assert len(failed_files) == 0, f"Syntax errors in validation: {failed_files}"

    def test_automation_syntax(self, base_path):
        """Test all automation files specifically"""
        automation_dirs = [
            base_path / "3_AUTOMATION_HOOKS",
            base_path / "trigger_id" / "3_AUTOMATION_HOOKS",
            base_path / "pattern_id" / "3_AUTOMATION_HOOKS",
        ]

        failed_files = []
        for auto_dir in automation_dirs:
            if auto_dir.exists():
                for py_file in auto_dir.glob("*.py"):
                    try:
                        py_compile.compile(str(py_file), doraise=True)
                    except py_compile.PyCompileError as e:
                        failed_files.append((py_file, str(e)))

        assert len(failed_files) == 0, f"Syntax errors in automation: {failed_files}"

    def test_common_modules_syntax(self, base_path):
        """Test all common module files"""
        common_dir = base_path / "common"
        if not common_dir.exists():
            pytest.skip("Common directory not found")

        failed_files = []
        for py_file in common_dir.glob("*.py"):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                failed_files.append((py_file, str(e)))

        assert len(failed_files) == 0, f"Syntax errors in common modules: {failed_files}"

class TestImportability:
    """Test that key modules can be imported"""

    @pytest.fixture
    def base_path(self):
        """Base path for all stable ID files"""
        return Path(__file__).parent.parent

    def test_scanners_importable(self, base_path):
        """Test that scanner modules can be imported"""
        sys.path.insert(0, str(base_path / "1_CORE_OPERATIONS"))

        try:
            import doc_id_scanner
            assert hasattr(doc_id_scanner, 'scan_doc_ids') or hasattr(doc_id_scanner, 'DocIDScanner')
        except ImportError as e:
            pytest.fail(f"Cannot import doc_id_scanner: {e}")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in doc_id_scanner: {e}")

    def test_validators_importable(self, base_path):
        """Test that validator modules can be imported"""
        sys.path.insert(0, str(base_path / "2_VALIDATION_FIXING"))

        # Test at least one validator
        validator_files = list((base_path / "2_VALIDATION_FIXING").glob("validate_*.py"))
        if validator_files:
            validator_name = validator_files[0].stem
            try:
                __import__(validator_name)
            except ImportError as e:
                pytest.fail(f"Cannot import {validator_name}: {e}")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {validator_name}: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
