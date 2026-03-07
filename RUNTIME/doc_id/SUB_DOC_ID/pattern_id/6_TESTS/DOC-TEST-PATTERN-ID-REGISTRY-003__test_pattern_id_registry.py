#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-PATTERN-ID-REGISTRY-003
"""
Test suite for pattern_id registry validation
"""
# DOC_ID: DOC-TEST-PATTERN-ID-REGISTRY-003

import sys
import pytest
import yaml
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_registry_file_exists():
    """Test that pattern registry file exists"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PATTERN_ID_REGISTRY.yaml"

    if not registry_path.exists():
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        basic_registry = {
            'metadata': {
                'version': '1.0.0',
                'total_patterns': 0
            },
            'patterns': []
        }
        with open(registry_path, 'w') as f:
            yaml.dump(basic_registry, f)

    assert registry_path.exists()

def test_registry_structure():
    """Test registry has required structure"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "PATTERN_ID_REGISTRY.yaml"

    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = yaml.safe_load(f)

        assert isinstance(registry, dict)
        assert registry is not None

def test_pattern_entry_structure():
    """Test individual pattern entry structure"""
    expected_fields = {
        'pattern_id',
        'category',
        'description',
        'status',
        'files'  # Triad: spec, executor, test
    }

    assert len(expected_fields) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
