"""
Unit tests for FactsExtractor - Phase E

Tests AST extraction, capability inference, and batch processing.

FILE_ID: 01999000042260125150
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path

# Add govreg_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))

from P_01999000042260125145_facts_extractor import FactsExtractor


@pytest.fixture
def sample_python_file():
    """Create sample Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import json
import sys
from pathlib import Path

FILE_ID = "01999000042260125150"

class TestClass:
    def __init__(self):
        pass
    
    def test_method(self):
        return "test"

def test_function(arg1, arg2):
    return arg1 + arg2

CONST_VALUE = 42

if __name__ == "__main__":
    print("Running")
""")
        path = Path(f.name)
    
    yield path
    path.unlink()


def test_facts_extractor_python_imports(sample_python_file):
    """Test extraction of Python imports."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    imports = facts["facts"]["imports"]
    assert len(imports) > 0
    
    # Check for json import
    json_import = [i for i in imports if i["module"] == "json"]
    assert len(json_import) == 1


def test_facts_extractor_python_classes(sample_python_file):
    """Test extraction of Python classes."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    classes = facts["facts"]["classes"]
    assert len(classes) == 1
    assert classes[0]["name"] == "TestClass"
    assert len(classes[0]["methods"]) == 2


def test_facts_extractor_python_functions(sample_python_file):
    """Test extraction of Python functions."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    functions = facts["facts"]["functions"]
    assert len(functions) == 1
    assert functions[0]["name"] == "test_function"
    assert len(functions[0]["args"]) == 2


def test_facts_extractor_python_constants(sample_python_file):
    """Test extraction of Python constants."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    constants = facts["facts"]["constants"]
    const = [c for c in constants if c["name"] == "CONST_VALUE"]
    assert len(const) == 1
    assert const[0]["value"] == 42


def test_facts_extractor_entry_points(sample_python_file):
    """Test detection of entry points."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    entry_points = facts["facts"]["entry_points"]
    assert len(entry_points) > 0
    
    # Should detect __main__ entry point
    main_entry = [e for e in entry_points if e["type"] == "main"]
    assert len(main_entry) > 0


def test_facts_extractor_capabilities(sample_python_file):
    """Test capability inference."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    capabilities = facts["facts"]["capabilities"]
    
    # Should detect IDS capability (FILE_ID present)
    assert "CAP-IDS-SCAN" in capabilities


def test_facts_extractor_content_hash(sample_python_file):
    """Test content hash is included."""
    extractor = FactsExtractor()
    facts = extractor.extract(sample_python_file, "01999000042260125150")
    
    assert "content_hash" in facts
    assert len(facts["content_hash"]) == 64  # SHA256 hex


def test_facts_extractor_save(sample_python_file):
    """Test saving facts to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        extractor = FactsExtractor()
        
        facts_path = extractor.extract_and_save(
            sample_python_file,
            "01999000042260125150",
            Path(tmpdir)
        )
        
        assert facts_path.exists()
        assert facts_path.name == "01999000042260125150.facts.json"
        
        # Verify JSON is valid
        facts = json.loads(facts_path.read_text())
        assert facts["file_id"] == "01999000042260125150"


def test_facts_extractor_batch():
    """Test batch extraction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test files
        file1 = Path(tmpdir) / "test1.py"
        file1.write_text("import json\nprint('test')")
        
        file2 = Path(tmpdir) / "test2.py"
        file2.write_text("import sys\nprint('test')")
        
        file_list = [
            (file1, "01999000042260125151"),
            (file2, "01999000042260125152")
        ]
        
        output_dir = Path(tmpdir) / "facts"
        extractor = FactsExtractor()
        summary = extractor.batch_extract(file_list, output_dir)
        
        assert summary["total"] == 2
        assert summary["succeeded"] == 2
        assert summary["failed"] == 0


def test_facts_extractor_json_file():
    """Test extraction from JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"key": "value", "$schema": "http://example.com/schema.json"}')
        path = Path(f.name)
    
    try:
        extractor = FactsExtractor()
        facts = extractor.extract(path, "01999000042260125153")
        
        assert facts["language"] == "json"
        assert "top_level_keys" in facts["facts"]
        assert "key" in facts["facts"]["top_level_keys"]
    finally:
        path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
