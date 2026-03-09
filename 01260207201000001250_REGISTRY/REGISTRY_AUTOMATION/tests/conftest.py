"""Pytest configuration for REGISTRY_AUTOMATION tests."""
import pytest
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

@pytest.fixture
def golden_registry():
    """Minimal valid registry for testing."""
    return {
        "files": [
            {
                "file_id": "01234567890123456789",
                "sha256": "a" * 64,
                "relative_path": "test/file.py",
                "canonicality": "CANONICAL"
            }
        ],
        "edges": []
    }

@pytest.fixture
def broken_registry():
    """Invalid registry for negative testing."""
    return {
        "files": [
            {
                "file_id": "INVALID",
                "sha256": "short",
                "relative_path": ""
            }
        ]
    }
