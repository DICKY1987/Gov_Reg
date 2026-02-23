"""
Cross-Phase Validator - Sequential Mutation Validation

Validates mutation sequences across multiple phases per spec Section 2.3.

Rules:
- Phase N+1 sees the world as Phase N left it
- Cannot modify deleted files
- Cannot create files that already exist
- Cannot delete non-existent files
"""

from typing import List, Dict, Set
from dataclasses import dataclass
import logging

from .conflict_validator import Conflict, ConflictSeverity

logger = logging.getLogger(__name__)


class PhaseState:
    """Track file state across phases."""

    def __init__(self):
        self.created_files: Set[str] = set()
        self.deleted_files: Set[str] = set()
        self.moved_files: Dict[str, str] = {}  # old_path -> new_path
        self.existing_files: Set[str] = set()  # From initial state

    def set_initial_files(self, paths: Set[str]):
        """Set initial filesystem state."""
        self.existing_files = paths.copy()

    def apply_phase(self, mutations: Dict):
        """
        Apply mutations to state.

        Args:
            mutations: Mutations dict for this phase
        """
        # Apply creates
        for file_info in mutations.get("created_files", []):
            path = file_info["relative_path"]
            self.created_files.add(path)
            # Remove from deleted if it was deleted earlier
            self.deleted_files.discard(path)

        # Apply deletes
        for file_info in mutations.get("deleted_files", []):
            path = file_info["relative_path"]
            self.deleted_files.add(path)
            # Remove from created if it was created earlier
            self.created_files.discard(path)

        # Apply moves
        for move_info in mutations.get("moved_files", []):
            old_path = move_info["old_path"]
            new_path = move_info["new_path"]
            self.moved_files[old_path] = new_path

            # Update created_files if file was created earlier
            if old_path in self.created_files:
                self.created_files.discard(old_path)
                self.created_files.add(new_path)

    def file_exists(self, path: str) -> bool:
        """
        Check if file exists in current state.

        Args:
            path: Path to check

        Returns:
            True if file exists in current state
        """
        # Check if deleted
        if path in self.deleted_files:
            return False

        # Check if created
        if path in self.created_files:
            return True

        # Check if it's a moved file (new path)
        if any(new_path == path for new_path in self.moved_files.values()):
            return True

        # Check initial state (not deleted, not moved away)
        if path in self.existing_files:
            # Not moved away
            if path not in self.moved_files:
                return True

        return False


class CrossPhaseValidator:
    """Validate mutation sequences across phases."""

    def validate_cross_phase_mutations(
        self, phases: List[Dict], initial_files: Set[str] = None
    ) -> List[Conflict]:
        """
        Validate mutation sequences across phases.

        Args:
            phases: List of phase dicts (each with 'mutations' key)
            initial_files: Initial filesystem state (optional)

        Returns:
            List of conflicts found
        """
        conflicts = []
        state = PhaseState()

        if initial_files:
            state.set_initial_files(initial_files)

        for phase_idx, phase_data in enumerate(phases):
            mutations = phase_data.get("mutations", {})

            # Check modifications on deleted files
            for file_info in mutations.get("modified_files", []):
                path = file_info["relative_path"]
                if not state.file_exists(path):
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="modify_deleted_file",
                            paths=[path],
                            description=f"Phase {phase_idx}: Cannot modify {path} (deleted in earlier phase)",
                            resolution="Remove modification or create file first",
                        )
                    )

            # Check duplicate creates
            for file_info in mutations.get("created_files", []):
                path = file_info["relative_path"]
                if state.file_exists(path):
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="duplicate_create",
                            paths=[path],
                            description=f"Phase {phase_idx}: Cannot create {path} (already exists)",
                            resolution="Remove duplicate create or use modify",
                        )
                    )

            # Check deletes on non-existent files
            for file_info in mutations.get("deleted_files", []):
                path = file_info["relative_path"]
                if not state.file_exists(path):
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="delete_nonexistent_file",
                            paths=[path],
                            description=f"Phase {phase_idx}: Cannot delete {path} (does not exist)",
                            resolution="Remove delete operation",
                        )
                    )

            # Check moves on non-existent files
            for move_info in mutations.get("moved_files", []):
                old_path = move_info["old_path"]
                if not state.file_exists(old_path):
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="move_nonexistent_file",
                            paths=[old_path],
                            description=f"Phase {phase_idx}: Cannot move {old_path} (does not exist)",
                            resolution="Remove move operation or create file first",
                        )
                    )

            # Apply this phase to state
            state.apply_phase(mutations)

        logger.info(
            f"Cross-phase validation: {len(conflicts)} conflicts across {len(phases)} phases"
        )

        return conflicts


# Convenience function
def validate_cross_phase(
    phases: List[Dict], initial_files: Set[str] = None
) -> List[Conflict]:
    """Validate cross-phase mutations (convenience wrapper)."""
    validator = CrossPhaseValidator()
    return validator.validate_cross_phase_mutations(phases, initial_files)
