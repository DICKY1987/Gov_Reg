"""
Tests for Tier 2 Edges Extractor
BDD Spec: specs/behaviors/BDD-REGV3-EDGES-004.yaml
Requirement: R-REGV3-EDGES-004
"""
# DOC_ID: DOC-TEST-6-TESTS-TEST-TIER2-EDGES-611

from importlib import util
from pathlib import Path

_module_path = Path(__file__).resolve().parent.parent / "common" / "DOC-SCRIPT-1009__tier2_edges.py"
_spec = util.spec_from_file_location("tier2_edges", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load module from {_module_path}")
_module = util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
extract_edges = _module.extract_edges
import tempfile
import os


def test_extract_import_edges():
    """Test import edge extraction"""
    test_code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name

    try:
        edges = extract_edges(temp_py, "test-uid", 1, trace_id="test", run_id="test-run")

        # Should have 4 import edges
        assert len(edges) >= 4

        # Check edge types
        assert all(e['edge_type'] == 'import' for e in edges)

        # Check specific imports
        assert any(e['target_module'] == 'os' for e in edges)
        assert any(e['target_module'] == 'sys' for e in edges)
        assert any(e['target_module'] == 'pathlib' for e in edges)
        assert any(e['target_module'] == 'typing' for e in edges)

    finally:
        os.unlink(temp_py)


def test_edges_sorted():
    """Test that edges are sorted deterministically"""
    test_code = '''
import sys
import os
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name

    try:
        edges = extract_edges(temp_py, "test-uid", 1)

        # Should be sorted by target_module
        if len(edges) >= 2:
            assert edges[0]['target_module'] <= edges[1]['target_module']

    finally:
        os.unlink(temp_py)


if __name__ == "__main__":
    test_extract_import_edges()
    test_edges_sorted()
    print("All edges tests passed!")
