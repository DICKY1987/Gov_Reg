"""
Conflict Validator - Mutation Conflict Detection

Enforces mutual exclusion rules per spec Section 2.2:
- Path appears in at most one mutation category per phase
- Exception: Explicit composite move+modify operations

Conflict types:
- created ∩ modified
- created ∩ deleted
- modified ∩ deleted
- moved ∩ modified (unless composite)
- moved ∩ deleted
"""

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Conflict:
    """Conflict detection result."""

    severity: ConflictSeverity
    rule: str
    paths: List[str]
    description: str
    resolution: str


class ConflictValidator:
    """
    Validates PFMS mutations for conflicts.

    Enforces mutual exclusion invariant.
    """

    def validate_mutual_exclusion(self, mutations: Dict) -> List[Conflict]:
        """
        Enforce mutual exclusion: path appears in at most one mutation category.

        Args:
            mutations: PFMS mutations dict

        Returns:
            List of conflicts (empty if valid)
        """
        conflicts = []

        # Collect all paths by category
        created_paths = {f["relative_path"] for f in mutations.get("created_files", [])}
        modified_paths = {
            f["relative_path"] for f in mutations.get("modified_files", [])
        }
        deleted_paths = {f["relative_path"] for f in mutations.get("deleted_files", [])}

        moved_old_paths = {f["old_path"] for f in mutations.get("moved_files", [])}
        moved_new_paths = {f["new_path"] for f in mutations.get("moved_files", [])}

        # Exception: move+modify composite operations
        composite_paths = {
            f["old_path"]
            for f in mutations.get("moved_files", [])
            if f.get("apply_modifications")
        }

        # Check: created ∩ modified
        overlap = created_paths & modified_paths
        if overlap:
            conflicts.append(
                Conflict(
                    severity=ConflictSeverity.ERROR,
                    rule="mutual_exclusion_violation",
                    paths=list(overlap),
                    description=f"Paths in both created_files and modified_files: {overlap}",
                    resolution="Choose create with final content OR modify existing",
                )
            )

        # Check: created ∩ deleted
        overlap = created_paths & deleted_paths
        if overlap:
            conflicts.append(
                Conflict(
                    severity=ConflictSeverity.ERROR,
                    rule="mutual_exclusion_violation",
                    paths=list(overlap),
                    description=f"Paths in both created_files and deleted_files: {overlap}",
                    resolution="Remove both operations (net no-op)",
                )
            )

        # Check: modified ∩ deleted
        overlap = modified_paths & deleted_paths
        if overlap:
            conflicts.append(
                Conflict(
                    severity=ConflictSeverity.ERROR,
                    rule="mutual_exclusion_violation",
                    paths=list(overlap),
                    description=f"Paths in both modified_files and deleted_files: {overlap}",
                    resolution="Choose one operation",
                )
            )

        # Check: moved ∩ modified (unless composite)
        overlap = (moved_old_paths & modified_paths) - composite_paths
        if overlap:
            conflicts.append(
                Conflict(
                    severity=ConflictSeverity.ERROR,
                    rule="mutual_exclusion_violation",
                    paths=list(overlap),
                    description=f"Paths in both moved_files and modified_files: {overlap}",
                    resolution="Use composite move+modify operation",
                )
            )

        # Check: moved ∩ deleted
        overlap = moved_old_paths & deleted_paths
        if overlap:
            conflicts.append(
                Conflict(
                    severity=ConflictSeverity.ERROR,
                    rule="mutual_exclusion_violation",
                    paths=list(overlap),
                    description=f"Paths in both moved_files and deleted_files: {overlap}",
                    resolution="Choose move or delete, not both",
                )
            )

        logger.info(f"Mutual exclusion validation: {len(conflicts)} conflicts")

        return conflicts

    def validate_execution_methods(self, mutations: Dict) -> List[Conflict]:
        """
        Validate execution methods are present and valid.

        Enforces:
        - All modified and created files have execution_method
        - UNIFIED_DIFF_APPLY has strict mode (allow_fuzz=false, rejects_allowed=false)

        Args:
            mutations: mutations dict with modified_files, created_files

        Returns:
            List of conflicts found
        """
        conflicts = []
        modified_files = mutations.get("modified_files", [])
        created_files = mutations.get("created_files", [])

        all_files = modified_files + created_files

        for file_entry in all_files:
            rel_path = file_entry.get("relative_path", "[unknown]")

            # Check execution_method presence
            if "execution_method" not in file_entry:
                conflicts.append(
                    Conflict(
                        severity=ConflictSeverity.ERROR,
                        rule="execution_method_required",
                        paths=[rel_path],
                        description=f"File '{rel_path}' missing execution_method",
                        resolution="Add execution_method field (FULL_REWRITE, UNIFIED_DIFF_APPLY, or AST_TRANSFORM)",
                    )
                )
                continue

            method = file_entry["execution_method"]

            # Validate UNIFIED_DIFF_APPLY strict mode
            if method == "UNIFIED_DIFF_APPLY":
                payload = file_entry.get("method_payload", {})

                if payload.get("allow_fuzz") is not False:
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="unified_diff_strict_mode",
                            paths=[rel_path],
                            description=f"UNIFIED_DIFF_APPLY on '{rel_path}' requires strict mode",
                            resolution="Set allow_fuzz=false",
                        )
                    )

                if payload.get("rejects_allowed") is not False:
                    conflicts.append(
                        Conflict(
                            severity=ConflictSeverity.ERROR,
                            rule="unified_diff_no_rejects",
                            paths=[rel_path],
                            description=f"UNIFIED_DIFF_APPLY on '{rel_path}' requires no rejects",
                            resolution="Set rejects_allowed=false",
                        )
                    )

        logger.info(f"Execution method validation: {len(conflicts)} conflicts")

        return conflicts

    def validate_pfms(self, pfms: Dict) -> List[Conflict]:
        """
        Run all PFMS validations.

        Args:
            pfms: Complete PFMS dict

        Returns:
            List of all conflicts found
        """
        conflicts = []
        mutations = pfms.get("mutations", {})

        # Mutual exclusion
        conflicts.extend(self.validate_mutual_exclusion(mutations))

        # Execution methods
        conflicts.extend(self.validate_execution_methods(mutations))

        return conflicts


# Convenience function
def validate_pfms(pfms: Dict) -> List[Conflict]:
    """Validate PFMS (convenience wrapper)."""
    validator = ConflictValidator()
    return validator.validate_pfms(pfms)
