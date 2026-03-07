"""
Tests for Tier 2 Symbols Extractor
BDD Spec: specs/behaviors/BDD-REGV3-SYMBOLS-003.yaml
Requirement: R-REGV3-SYMBOLS-003
"""
# DOC_ID: DOC-TEST-6-TESTS-TEST-TIER2-SYMBOLS-612

from importlib import util
from pathlib import Path

_module_path = Path(__file__).resolve().parent.parent / "common" / "DOC-SCRIPT-1010__tier2_symbols.py"
_spec = util.spec_from_file_location("tier2_symbols", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load module from {_module_path}")
_module = util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
extract_symbols = _module.extract_symbols
import tempfile
import os


def test_extract_symbols_from_python_file():
    """Test symbol extraction from Python file"""
    test_code = '''
import os

def public_func():
    pass

def _private_func():
    pass

class MyClass:
    def method(self):
        pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name

    try:
        symbols = extract_symbols(temp_py, "test-uid", 1, trace_id="test", run_id="test-run")

        # Should have: os import, public_func, _private_func, MyClass, method
        assert len(symbols) >= 4

        # Check function visibility
        func_symbols = [s for s in symbols if s['symbol_type'] == 'function']
        assert any(s['symbol_name'] == 'public_func' and s['visibility'] == 'public' for s in func_symbols)
        assert any(s['symbol_name'] == '_private_func' and s['visibility'] == 'protected' for s in func_symbols)

        # Check class extracted
        class_symbols = [s for s in symbols if s['symbol_type'] == 'class']
        assert any(s['symbol_name'] == 'MyClass' for s in class_symbols)

    finally:
        os.unlink(temp_py)


def test_symbols_sorted_by_line():
    """Test that symbols are sorted by line number"""
    test_code = '''
def func_b():
    pass

def func_a():
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name

    try:
        symbols = extract_symbols(temp_py, "test-uid", 1)
        func_symbols = [s for s in symbols if s['symbol_type'] == 'function']

        # func_b should come before func_a (by line number)
        if len(func_symbols) >= 2:
            assert func_symbols[0]['line_start'] < func_symbols[1]['line_start']

    finally:
        os.unlink(temp_py)


if __name__ == "__main__":
    test_extract_symbols_from_python_file()
    test_symbols_sorted_by_line()
    print("All symbols tests passed!")
