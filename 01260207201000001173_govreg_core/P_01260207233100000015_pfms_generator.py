"""
PFMS Generator - Planning Mutation Set Creation

Creates mutation sets with dual identity:
- mutation_set_id: Instance tracking (allocator)
- content_hash: Semantic equality (deterministic)

Per spec Section 0.2: "Identity is for tracking instances. Equality is for comparing content."
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
from pathlib import Path

from .canonical_hash import hash_canonical_data
from .P_01260207233100000013_feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class PFMSGenerator:
    """Generate PFMS (Planning File Mutation Set) artifacts."""

    def __init__(self, id_allocator=None):
        """
        Initialize PFMS generator.

        Args:
            id_allocator: Optional ID allocator (defaults to sequential)
        """
        self.id_allocator = id_allocator or SequentialAllocator()

    def create_mutation_set(self, mutations: Dict, plan_id: str) -> Dict:
        """
        Create PFMS with dual identity: ID for tracking, hash for comparison.

        Args:
            mutations: Mutation operations (created_files, modified_files, etc.)
            plan_id: Parent plan ID

        Returns:
            PFMS dict with mutation_set_id and content_hash

        Example:
            >>> mutations = {
            ...     "created_files": [{"relative_path": "src/a.py"}]
            ... }
            >>> pfms = create_mutation_set(mutations, "PLAN-001")
            >>> pfms['mutation_set_id']  # Different each run
            '01999000042260124528'
            >>> pfms['content_hash']     # Same for same content
            'e8c7f9a3b5d1e6f2...'
        """
        # Identity (instance tracking)
        mutation_set_id = self.id_allocator.allocate_single_id(
            purpose=f"Mutation set for {plan_id}"
        )

        # Equality (content comparison)
        canonical_mutations = self._canonicalize_mutations(mutations)
        content_hash = hash_canonical_data(canonical_mutations)

        pfms = {
            "mutation_set_id": mutation_set_id,  # For registry tracking
            "content_hash": content_hash,  # For determinism
            "plan_id": plan_id,
            "mutations": mutations,
            "created_at": datetime.utcnow().isoformat(),
            "schema_version": "1.2.0",
        }

        logger.info(
            f"Created mutation set {mutation_set_id} (hash: {content_hash[:16]}...)"
        )

        return pfms

    def _canonicalize_mutations(self, mutations: Dict) -> Dict:
        """
        Canonicalize mutations for hashing.

        Ensures deterministic hash by:
        - Sorting lists by stable keys
        - Normalizing field order
        - Removing runtime-specific fields
        """
        canonical = {}

        # Canonicalize created_files
        if "created_files" in mutations:
            canonical["created_files"] = sorted(
                mutations["created_files"], key=lambda x: x.get("relative_path", "")
            )

        # Canonicalize modified_files
        if "modified_files" in mutations:
            canonical["modified_files"] = sorted(
                mutations["modified_files"], key=lambda x: x.get("relative_path", "")
            )

        # Canonicalize deleted_files
        if "deleted_files" in mutations:
            canonical["deleted_files"] = sorted(
                mutations["deleted_files"], key=lambda x: x.get("relative_path", "")
            )

        # Canonicalize moved_files
        if "moved_files" in mutations:
            canonical["moved_files"] = sorted(
                mutations["moved_files"], key=lambda x: x.get("old_path", "")
            )

        return canonical

    def are_mutation_sets_identical(self, pfms_a: Dict, pfms_b: Dict) -> bool:
        """
        Compare mutation sets by content, not ID.

        Args:
            pfms_a: First mutation set
            pfms_b: Second mutation set

        Returns:
            True if content_hash matches (semantically identical)

        Note:
            mutation_set_id will differ across runs, but content_hash
            will match if mutations are identical.
        """
        return pfms_a["content_hash"] == pfms_b["content_hash"]

    def create_mutation_set_with_reservations(
        self, mutations: Dict, plan_id: str, registry_root: str = "."
    ) -> Dict:
        """
        Create PFMS with pre-allocated file IDs (if feature flag enabled).

        Args:
            mutations: Mutation operations (created_files, modified_files, etc.)
            plan_id: Parent plan ID
            registry_root: Root directory for registry/reservations

        Returns:
            PFMS dict with mutation_set_id, file_ids, and content_hash

        Note:
            If enable_planning_reservations flag is OFF, behaves like create_mutation_set.
            If flag is ON, pre-allocates IDs and creates reservation ledger.
        """
        flags = FeatureFlags()

        # Check if reservations are enabled
        if not flags.get_flag("enable_planning_reservations"):
            # Legacy mode: just create mutation set without reservations
            return self.create_mutation_set(mutations, plan_id)

        # Reservations enabled: allocate IDs and create ledger
        try:
            from .P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator
            from .P_01999000042260124032_reservation_ledger import ReservationLedger

            created_files = mutations.get("created_files", [])

            if created_files:
                # Reserve IDs
                allocator = UnifiedIDAllocator(Path(registry_root) / "COUNTER_STORE.json")
                count = len(created_files)
                reserved_ids = allocator.reserve_id_range(
                    count=count,
                    purpose=f"Plan {plan_id}",
                    reservation_id=f"RES-{plan_id}",
                    allocated_by="pfms_generator"
                )

                # Sort by path for determinism
                sorted_files = sorted(created_files, key=lambda f: f.get("relative_path", ""))
                relative_paths = [f.get("relative_path", "") for f in sorted_files]

                # Assign IDs to files
                mutations_copy = dict(mutations)
                mutations_copy["created_files"] = []
                for file_info, file_id in zip(sorted_files, reserved_ids):
                    file_info["file_id"] = file_id
                    mutations_copy["created_files"].append(file_info)

                # Create reservation ledger
                ledger = ReservationLedger(plan_id, registry_root)
                ledger.create_reservation(
                    file_ids=reserved_ids,
                    relative_paths=relative_paths,
                    allocated_by="pfms_generator",
                    allocation_metadata={
                        "plan_id": plan_id,
                        "file_count": count
                    }
                )

                logger.info(
                    f"Reserved {count} file IDs for plan {plan_id}: {reserved_ids}"
                )
            else:
                mutations_copy = dict(mutations)

            # Create mutation set with standard logic
            return self.create_mutation_set(mutations_copy, plan_id)

        except Exception as e:
            logger.error(f"Failed to create mutation set with reservations: {e}")
            # Fallback to standard creation
            return self.create_mutation_set(mutations, plan_id)


class SequentialAllocator:
    """
    Simple sequential ID allocator for testing.

    Production should use P_01999000042260124027_id_allocator.py
    """

    def __init__(self, start_id: int = 1):
        self.next_id = start_id

    def allocate_single_id(self, purpose: str = "") -> str:
        """
        Allocate 20-digit sequential ID.

        Args:
            purpose: Description of what ID is for (logged)

        Returns:
            20-digit numeric string
        """
        # Format: 01999000042260124XXX (20 digits)
        base = 1999000042260124000
        allocated_id = base + self.next_id
        self.next_id += 1

        id_str = f"{allocated_id:020d}"
        logger.debug(f"Allocated ID {id_str} for: {purpose}")

        return id_str
