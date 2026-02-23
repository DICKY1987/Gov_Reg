"""
Tests for conflict_validator - Mutual Exclusion
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.conflict_validator import ConflictValidator, ConflictSeverity


def test_mutual_exclusion_created_modified():
    """Test: created + modified conflict detected."""
    validator = ConflictValidator()

    mutations = {
        "created_files": [{"relative_path": "src/a.py"}],
        "modified_files": [{"relative_path": "src/a.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 1
    assert conflicts[0].rule == "mutual_exclusion_violation"
    assert conflicts[0].severity == ConflictSeverity.ERROR
    assert "src/a.py" in conflicts[0].paths


def test_mutual_exclusion_created_deleted():
    """Test: created + deleted conflict detected."""
    validator = ConflictValidator()

    mutations = {
        "created_files": [{"relative_path": "src/a.py"}],
        "deleted_files": [{"relative_path": "src/a.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 1
    assert "created_files and deleted_files" in conflicts[0].description


def test_mutual_exclusion_modified_deleted():
    """Test: modified + deleted conflict detected."""
    validator = ConflictValidator()

    mutations = {
        "modified_files": [{"relative_path": "src/a.py"}],
        "deleted_files": [{"relative_path": "src/a.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 1
    assert "modified_files and deleted_files" in conflicts[0].description


def test_composite_move_modify_allowed():
    """Test: Composite move+modify operations allowed (exception)."""
    validator = ConflictValidator()

    mutations = {
        "moved_files": [{
            "old_path": "src/old.py",
            "new_path": "src/new.py",
            "apply_modifications": {"change_type": "replace_lines"}
        }]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 0, "Composite operations should be allowed"


def test_moved_modified_without_composite():
    """Test: moved + modified without composite flag is conflict."""
    validator = ConflictValidator()

    mutations = {
        "moved_files": [{"old_path": "src/a.py", "new_path": "src/b.py"}],
        "modified_files": [{"relative_path": "src/a.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 1
    assert "moved_files and modified_files" in conflicts[0].description


def test_moved_deleted_conflict():
    """Test: moved + deleted conflict detected."""
    validator = ConflictValidator()

    mutations = {
        "moved_files": [{"old_path": "src/a.py", "new_path": "src/b.py"}],
        "deleted_files": [{"relative_path": "src/a.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 1
    assert "moved_files and deleted_files" in conflicts[0].description


def test_no_conflicts_valid_mutations():
    """Test: Valid mutations produce no conflicts."""
    validator = ConflictValidator()

    mutations = {
        "created_files": [{"relative_path": "src/a.py"}],
        "modified_files": [{"relative_path": "src/b.py"}],
        "deleted_files": [{"relative_path": "src/c.py"}]
    }

    conflicts = validator.validate_mutual_exclusion(mutations)

    assert len(conflicts) == 0, "No conflicts expected for disjoint paths"


def test_validate_pfms():
    """Test: validate_pfms wrapper works."""
    validator = ConflictValidator()

    pfms = {
        "mutation_set_id": "01999000042260124001",
        "mutations": {
            "created_files": [{"relative_path": "src/a.py"}],
            "modified_files": [{"relative_path": "src/a.py"}]
        }
    }

    conflicts = validator.validate_pfms(pfms)

    assert len(conflicts) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
