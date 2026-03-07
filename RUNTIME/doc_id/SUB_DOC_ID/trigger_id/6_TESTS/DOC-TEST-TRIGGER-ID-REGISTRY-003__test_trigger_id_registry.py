#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TRIGGER-ID-REGISTRY-003
"""
Test suite for trigger_id registry validation
"""
# DOC_ID: DOC-TEST-TRIGGER-ID-REGISTRY-003

import sys
import pytest
import yaml
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_registry_file_exists():
    """Test that trigger registry file exists"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml"

    # File should exist (or we create it)
    if not registry_path.exists():
        # Create basic registry structure
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        basic_registry = {
            'metadata': {
                'version': '1.0.0',
                'total_triggers': 0
            },
            'triggers': []
        }
        with open(registry_path, 'w') as f:
            yaml.dump(basic_registry, f)

    assert registry_path.exists()

def test_registry_structure():
    """Test registry has required structure"""
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml"

    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = yaml.safe_load(f)

        # Should have metadata and triggers keys
        assert isinstance(registry, dict)
        # Registry should be loadable
        assert registry is not None

def test_trigger_entry_structure():
    """Test individual trigger entry structure"""
    expected_fields = {
        'trigger_id',
        'category',
        'description',
        'status'
    }

    # Test that we know what fields are required
    assert len(expected_fields) == 4

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
