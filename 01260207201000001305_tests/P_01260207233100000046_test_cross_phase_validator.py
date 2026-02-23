"""
Tests for cross_phase_validator - Sequential Mutations
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.cross_phase_validator import CrossPhaseValidator, PhaseState


def test_modify_after_delete_conflict():
    """Test: Cannot modify file deleted in earlier phase."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "deleted_files": [{"relative_path": "src/a.py"}]
            }
        },
        {
            "phase": 2,
            "mutations": {
                "modified_files": [{"relative_path": "src/a.py"}]
            }
        }
    ]

    initial_files = {"src/a.py"}
    conflicts = validator.validate_cross_phase_mutations(phases, initial_files)

    assert len(conflicts) == 1
    assert conflicts[0].rule == "modify_deleted_file"


def test_create_after_delete_allowed():
    """Test: Can create file after deleting it (valid sequence)."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "deleted_files": [{"relative_path": "src/a.py"}]
            }
        },
        {
            "phase": 2,
            "mutations": {
                "created_files": [{"relative_path": "src/a.py"}]
            }
        }
    ]

    initial_files = {"src/a.py"}
    conflicts = validator.validate_cross_phase_mutations(phases, initial_files)

    assert len(conflicts) == 0, "Create after delete is valid"


def test_duplicate_create_conflict():
    """Test: Cannot create file that already exists."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "created_files": [{"relative_path": "src/a.py"}]
            }
        },
        {
            "phase": 2,
            "mutations": {
                "created_files": [{"relative_path": "src/a.py"}]
            }
        }
    ]

    conflicts = validator.validate_cross_phase_mutations(phases, set())

    assert len(conflicts) == 1
    assert conflicts[0].rule == "duplicate_create"


def test_modify_after_create_allowed():
    """Test: Can modify file created in earlier phase (valid sequence)."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "created_files": [{"relative_path": "src/a.py"}]
            }
        },
        {
            "phase": 2,
            "mutations": {
                "modified_files": [{"relative_path": "src/a.py"}]
            }
        }
    ]

    conflicts = validator.validate_cross_phase_mutations(phases, set())

    assert len(conflicts) == 0, "Modify after create is valid"


def test_modify_after_move_new_path():
    """Test: Can modify file at new path after move."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "moved_files": [{
                    "old_path": "src/old.py",
                    "new_path": "src/new.py"
                }]
            }
        },
        {
            "phase": 2,
            "mutations": {
                "modified_files": [{"relative_path": "src/new.py"}]
            }
        }
    ]

    initial_files = {"src/old.py"}
    conflicts = validator.validate_cross_phase_mutations(phases, initial_files)

    assert len(conflicts) == 0, "Modify after move (new path) is valid"


def test_delete_nonexistent_conflict():
    """Test: Cannot delete file that doesn't exist."""
    validator = CrossPhaseValidator()

    phases = [
        {
            "phase": 1,
            "mutations": {
                "deleted_files": [{"relative_path": "src/nonexistent.py"}]
            }
        }
    ]

    initial_files = {"src/other.py"}
    conflicts = validator.validate_cross_phase_mutations(phases, initial_files)

    assert len(conflicts) == 1
    assert conflicts[0].rule == "delete_nonexistent_file"


def test_phase_state_tracking():
    """Test: PhaseState correctly tracks file existence."""
    state = PhaseState()
    state.set_initial_files({"src/a.py", "src/b.py"})

    # Initial state
    assert state.file_exists("src/a.py") is True
    assert state.file_exists("src/c.py") is False

    # After create
    state.apply_phase({
        "created_files": [{"relative_path": "src/c.py"}]
    })
    assert state.file_exists("src/c.py") is True

    # After delete
    state.apply_phase({
        "deleted_files": [{"relative_path": "src/a.py"}]
    })
    assert state.file_exists("src/a.py") is False

    # After move
    state.apply_phase({
        "moved_files": [{
            "old_path": "src/b.py",
            "new_path": "src/d.py"
        }]
    })
    assert state.file_exists("src/b.py") is False
    assert state.file_exists("src/d.py") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
