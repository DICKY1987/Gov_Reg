"""
Unit tests for VocabularyValidator - Phase B

Tests vocabulary validation, batch validation, and suggestions.

FILE_ID: 01999000042260125147
"""

import pytest
import json
import sys
import tempfile
from pathlib import Path

# Add govreg_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))

from P_01999000042260125139_vocab_validator import VocabularyValidator


@pytest.fixture
def vocab_file():
    """Create temporary vocabulary file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        vocab = {
            "version": "1.0.0",
            "frozen_at": "2026-02-20T00:00:00Z",
            "entries": [
                {"id": "CAP-REGISTRY-VALIDATE", "component": "REGISTRY"},
                {"id": "CAP-REGISTRY-SCAN", "component": "REGISTRY"},
                {"id": "CAP-IDS-ALLOCATE", "component": "IDS"},
                {"id": "CAP-GOVERNANCE-VALIDATE", "component": "GOVERNANCE"}
            ],
            "file_id": "01999000042260125136"
        }
        json.dump(vocab, f)
        path = Path(f.name)
    
    yield path
    path.unlink()


def test_vocab_validator_accepts_valid(vocab_file):
    """Test validator accepts valid IDs."""
    validator = VocabularyValidator(vocab_file)
    
    assert validator.validate("CAP-REGISTRY-VALIDATE") == True
    assert validator.validate("CAP-IDS-ALLOCATE") == True


def test_vocab_validator_rejects_invalid(vocab_file):
    """Test validator rejects invalid IDs."""
    validator = VocabularyValidator(vocab_file)
    
    assert validator.validate("CAP-UNKNOWN-TAG") == False
    assert validator.validate("INVALID") == False


def test_vocab_validator_batch(vocab_file):
    """Test batch validation."""
    validator = VocabularyValidator(vocab_file)
    
    values = [
        "CAP-REGISTRY-VALIDATE",
        "CAP-UNKNOWN-TAG",
        "CAP-IDS-ALLOCATE",
        "INVALID"
    ]
    
    valid, invalid = validator.validate_batch(values)
    
    assert len(valid) == 2
    assert len(invalid) == 2
    assert "CAP-REGISTRY-VALIDATE" in valid
    assert "CAP-UNKNOWN-TAG" in invalid


def test_vocab_validator_suggestions(vocab_file):
    """Test near-miss suggestions."""
    validator = VocabularyValidator(vocab_file)
    
    # Typo in VALIDATE
    suggestions = validator.suggest("CAP-REGISTRY-VALIDAT")
    assert len(suggestions) > 0
    assert "CAP-REGISTRY-VALIDATE" in suggestions


def test_vocab_validator_properties(vocab_file):
    """Test validator properties."""
    validator = VocabularyValidator(vocab_file)
    
    assert validator.version == "1.0.0"
    assert validator.entry_count == 4


def test_vocab_validator_by_component(vocab_file):
    """Test filtering by component."""
    validator = VocabularyValidator(vocab_file)
    
    registry_entries = validator.get_entries_by_component("REGISTRY")
    assert len(registry_entries) == 2
    
    ids_entries = validator.get_entries_by_component("IDS")
    assert len(ids_entries) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
