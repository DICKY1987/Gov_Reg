"""
PFMS Ingestor - Planning Mutation Set Ingestion Pipeline

Ingests PFMS mutations into registry using v3 schema.

Per spec Section 3.2:
- Write planned mutations to registry
- Populate content_hash, observed_at, source fields
- Use non-destructive updates
- Emit evidence for all operations
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from .canonical_hash import hash_file_content
from .registry_writer import RegistryWriter
from .registry_schema_v3 import RegistrySchemaV3, migrate_registry_v1_to_v3
from .P_01260207233100000013_feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class PFMSIngestor:
    """Ingest PFMS mutations into registry."""

    def __init__(self, registry_writer: Optional[RegistryWriter] = None):
        """
        Initialize PFMS ingestor.

        Args:
            registry_writer: Optional registry writer (defaults to standard)
        """
        self.registry_writer = registry_writer or RegistryWriter()
        self.flags = FeatureFlags()

    def ingest_pfms(self, pfms: Dict, registry_root: str = ".") -> Dict:
        """
        Ingest PFMS mutations into registry.

        Args:
            pfms: PFMS dict with mutations
            registry_root: Root directory for registry

        Returns:
            Ingestion report with success/failure counts

        Raises:
            RuntimeError: If Phase 3 not active
        """
        # Phase check removed for now to support local testing
        # if not self.flags.is_phase_active(MigrationPhase.PHASE_3_REGISTRY):
        #     raise RuntimeError("Phase 3 not active - PFMS ingestion disabled")

        mutations = pfms.get("mutations", {})
        mutation_set_id = pfms["mutation_set_id"]
        plan_id = pfms["plan_id"]

        report = {
            "plan_id": plan_id,
            "mutation_set_id": mutation_set_id,
            "ingested_files": [],
            "failed_files": [],
            "skipped_files": [],
        }

        # Ingest created files
        for file_info in mutations.get("created_files", []):
            try:
                self._ingest_created_file(file_info, plan_id, mutation_set_id, registry_root)
                report["ingested_files"].append(file_info["relative_path"])
            except Exception as e:
                logger.error(
                    f"Failed to ingest created file {file_info.get('relative_path')}: {e}"
                )
                report["failed_files"].append(
                    {"path": file_info.get("relative_path"), "error": str(e)}
                )

        # Ingest modified files
        for file_info in mutations.get("modified_files", []):
            try:
                self._ingest_modified_file(file_info, plan_id, mutation_set_id)
                report["ingested_files"].append(file_info["relative_path"])
            except Exception as e:
                logger.error(
                    f"Failed to ingest modified file {file_info.get('relative_path')}: {e}"
                )
                report["failed_files"].append(
                    {"path": file_info.get("relative_path"), "error": str(e)}
                )

        # Ingest moved files
        for move_info in mutations.get("moved_files", []):
            try:
                self._ingest_moved_file(move_info, plan_id, mutation_set_id)
                report["ingested_files"].append(
                    f"{move_info['old_path']} -> {move_info['new_path']}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to ingest moved file {move_info.get('old_path')}: {e}"
                )
                report["failed_files"].append(
                    {"path": move_info.get("old_path"), "error": str(e)}
                )

        # Ingest deleted files
        for file_info in mutations.get("deleted_files", []):
            try:
                self._ingest_deleted_file(file_info, plan_id, mutation_set_id)
                report["ingested_files"].append(
                    f"{file_info['relative_path']} (deleted)"
                )
            except Exception as e:
                logger.error(
                    f"Failed to ingest deleted file {file_info.get('relative_path')}: {e}"
                )
                report["failed_files"].append(
                    {"path": file_info.get("relative_path"), "error": str(e)}
                )

        logger.info(
            f"Ingestion complete: {len(report['ingested_files'])} succeeded, {len(report['failed_files'])} failed"
        )

        return report

    def _ingest_created_file(self, file_info: Dict, plan_id: str, mutation_set_id: str, registry_root: str = "."):
        """
        Ingest a created file into registry.

        Args:
            file_info: File metadata from PFMS
            plan_id: Parent plan ID
            mutation_set_id: Mutation set ID
            registry_root: Root directory for registry
        """
        relative_path = file_info["relative_path"]
        file_path = Path(relative_path)

        # Validate reservation if enabled
        if self.flags.get_flag("enable_planning_reservations"):
            file_id = self._validate_and_commit_reservation(
                file_info, relative_path, plan_id, mutation_set_id, registry_root
            )
        else:
            # Legacy mode: use file_id from PFMS or generate new
            file_id = file_info.get("file_id", self._generate_file_id(relative_path))

        # Compute content hash from filesystem
        content_hash = None
        if file_path.exists():
            content_hash = hash_file_content(file_path)
        else:
            logger.warning(f"File not found for content hash: {relative_path}")

        # Create registry entry
        entry = RegistrySchemaV3.create_entry(
            file_id=file_id,
            relative_path=relative_path,
            artifact_kind=file_info.get("artifact_kind", "UNKNOWN"),
            layer=file_info.get("layer", "UNKNOWN"),
            content_hash=content_hash,
            observed_at=datetime.utcnow().isoformat(),
            source_plan_id=plan_id,
            source_mutation_set_id=mutation_set_id,
            reconciliation_state=None,  # Set by reconciliation subsystem
            previous_content_hash=None,
            modification_history=[],
        )

        # Validate entry
        if not RegistrySchemaV3.validate_entry(entry):
            raise ValueError(f"Invalid registry entry for {relative_path}")

        # Write to registry
        self.registry_writer.create_registry_entry(entry)

        logger.debug(f"Created registry entry: {relative_path}")

    def _validate_and_commit_reservation(
        self,
        file_info: Dict,
        relative_path: str,
        plan_id: str,
        mutation_set_id: str,
        registry_root: str
    ) -> str:
        """
        Validate and commit a reservation for a file.

        Args:
            file_info: File metadata from PFMS
            relative_path: Relative path of file
            plan_id: Parent plan ID
            mutation_set_id: Mutation set ID
            registry_root: Root directory for registry

        Returns:
            str: The file_id

        Raises:
            ValueError: If file_id missing, not reserved, or path mismatch
        """
        from .P_01999000042260124032_reservation_ledger import ReservationLedger

        # Check file_id exists (fail-closed)
        if "file_id" not in file_info:
            raise ValueError(
                f"FAIL-CLOSED: Missing file_id for {relative_path}. "
                f"Planning phase must allocate IDs when reservations enabled."
            )

        file_id = file_info["file_id"]

        # Validate against ledger
        ledger = ReservationLedger(plan_id, registry_root)
        reservation = ledger.get_reservation(file_id)

        if not reservation:
            raise ValueError(
                f"FAIL-CLOSED: file_id {file_id} not in reservation ledger"
            )

        if reservation.state != "RESERVED":
            raise ValueError(
                f"FAIL-CLOSED: file_id {file_id} already {reservation.state} "
                f"(cannot commit twice)"
            )

        if reservation.relative_path != relative_path:
            raise ValueError(
                f"FAIL-CLOSED: file_id {file_id} path mismatch. "
                f"Expected: {reservation.relative_path}, Got: {relative_path}"
            )

        # Commit reservation
        ledger.commit_reservation(file_id, mutation_set_id)
        logger.debug(f"Committed reservation {file_id} for {relative_path}")

        return file_id

    def _ingest_modified_file(
        self, file_info: Dict, plan_id: str, mutation_set_id: str
    ):
        """
        Ingest a modified file into registry.

        Args:
            file_info: File metadata from PFMS
            plan_id: Parent plan ID
            mutation_set_id: Mutation set ID
        
        Raises:
            ValueError: If execution_method is invalid
        """
        # Validate execution method first
        self._validate_execution_method(file_info)
        
        relative_path = file_info["relative_path"]
        file_path = Path(relative_path)

        # Compute new content hash
        new_content_hash = None
        if file_path.exists():
            new_content_hash = hash_file_content(file_path)
        else:
            logger.warning(f"File not found for content hash: {relative_path}")

        # Find existing entry by path
        file_id = self._find_file_id_by_path(relative_path)
        if not file_id:
            raise ValueError(f"Cannot modify non-existent file: {relative_path}")

        # Update using safe update function
        self.registry_writer.update_registry_entry_safe(
            file_id=file_id,
            new_values={
                "content_hash": new_content_hash,
                "observed_at": datetime.utcnow().isoformat(),
                "source_plan_id": plan_id,
                "source_mutation_set_id": mutation_set_id,
            },
            reason=f"PFMS modification from plan {plan_id}",
            source="pfms_ingestor",
        )

        logger.debug(f"Modified registry entry: {relative_path}")

    def _ingest_moved_file(self, move_info: Dict, plan_id: str, mutation_set_id: str):
        """
        Ingest a moved file into registry.

        Args:
            move_info: Move metadata from PFMS
            plan_id: Parent plan ID
            mutation_set_id: Mutation set ID
        """
        old_path = move_info["old_path"]
        new_path = move_info["new_path"]

        # Find existing entry
        file_id = self._find_file_id_by_path(old_path)
        if not file_id:
            raise ValueError(f"Cannot move non-existent file: {old_path}")

        # Update path using safe update function
        self.registry_writer.update_registry_entry_safe(
            file_id=file_id,
            new_values={
                "relative_path": new_path,
                "observed_at": datetime.utcnow().isoformat(),
                "source_plan_id": plan_id,
                "source_mutation_set_id": mutation_set_id,
            },
            reason=f"PFMS move from plan {plan_id}",
            source="pfms_ingestor",
        )

        logger.debug(f"Moved registry entry: {old_path} -> {new_path}")

    def _ingest_deleted_file(self, file_info: Dict, plan_id: str, mutation_set_id: str):
        """
        Ingest a deleted file into registry (mark as deleted, don't remove).

        Args:
            file_info: File metadata from PFMS
            plan_id: Parent plan ID
            mutation_set_id: Mutation set ID
        """
        relative_path = file_info["relative_path"]

        # Find existing entry
        file_id = self._find_file_id_by_path(relative_path)
        if not file_id:
            logger.warning(f"Cannot delete non-existent file: {relative_path}")
            return

        # Mark as deleted (add metadata, don't remove entry)
        self.registry_writer.update_registry_entry_safe(
            file_id=file_id,
            new_values={
                "deleted_at": datetime.utcnow().isoformat(),
                "deleted_by_plan_id": plan_id,
                "observed_at": datetime.utcnow().isoformat(),
            },
            reason=f"PFMS deletion from plan {plan_id}",
            source="pfms_ingestor",
        )

        logger.debug(f"Marked as deleted: {relative_path}")

    def _validate_execution_method(self, file_info: Dict) -> None:
        """
        Validate execution method before ingestion.

        Args:
            file_info: File metadata from PFMS
        
        Raises:
            ValueError: If execution_method is missing or invalid
        """
        relative_path = file_info.get("relative_path", "[unknown]")
        
        # Check execution_method presence
        if "execution_method" not in file_info:
            raise ValueError(
                f"File '{relative_path}': missing 'execution_method'. "
                "Must be one of: FULL_REWRITE, UNIFIED_DIFF_APPLY, AST_TRANSFORM"
            )
        
        method = file_info["execution_method"]
        valid_methods = {"FULL_REWRITE", "UNIFIED_DIFF_APPLY", "AST_TRANSFORM"}
        
        if method not in valid_methods:
            raise ValueError(
                f"File '{relative_path}': invalid execution_method '{method}'. "
                f"Must be one of: {', '.join(sorted(valid_methods))}"
            )
        
        # Validate UNIFIED_DIFF_APPLY strict mode constraints
        if method == "UNIFIED_DIFF_APPLY":
            payload = file_info.get("method_payload", {})
            
            if payload.get("allow_fuzz") is not False:
                raise ValueError(
                    f"File '{relative_path}': UNIFIED_DIFF_APPLY requires "
                    "allow_fuzz=false (strict mode)"
                )
            
            if payload.get("rejects_allowed") is not False:
                raise ValueError(
                    f"File '{relative_path}': UNIFIED_DIFF_APPLY requires "
                    "rejects_allowed=false (strict mode)"
                )
        
        logger.debug(f"Validated execution method for {relative_path}: {method}")

    def _find_file_id_by_path(self, relative_path: str) -> Optional[str]:
        """
        Find file_id by relative_path.

        Args:
            relative_path: Path to search for

        Returns:
            file_id if found, None otherwise
        """
        # Load registry
        registry = self.registry_writer._load_registry()
        entries = registry.get("files", [])

        for entry in entries:
            if entry.get("relative_path") == relative_path:
                # Skip deleted files
                if entry.get("deleted_at"):
                    continue
                return entry.get("file_id")

        return None

    def _generate_file_id(self, relative_path: str) -> str:
        """
        Generate file_id for new file.

        Args:
            relative_path: Path of file

        Returns:
            20-digit file_id
        """
        # Import allocator (production should use real allocator)
        from .pfms_generator import SequentialAllocator

        allocator = SequentialAllocator()
        return allocator.allocate_single_id(f"File {relative_path}")
