"""
metadata_backfiller.py

Metadata population: Backfill missing doc_id, file_size, canonicality fields.

Issue: FCA-010 (Critical)
Symptom: Registry records missing required metadata fields (doc_id, file_size, canonicality)
Root Cause: Phase postcondition enforcement missing; default injection semantics not actionable
Fix: Deterministic metadata backfill with validation

Contract: output_result_envelope_contract + pass_fail_criteria_contract
Category: Phase
Runner: Must validate metadata completeness before downstream consumption
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataBackfillError(Exception):
    """Raised when metadata backfill fails."""
    pass


class MetadataBackfiller:
    """
    Backfill missing metadata fields in registry records.
    
    Required fields:
    - doc_id: Unique document identifier (derived from file_id or sha256)
    - file_size: Size in bytes
    - canonicality: Boolean indicating if file is canonical version
    - file_id: 20-digit identifier (handled by FileIDResolver)
    - repo_root_id: Repository root identifier (handled by RepoRootResolver)
    
    Strategy:
    1. Identify records with missing metadata
    2. Compute missing fields from available data
    3. Validate completeness
    4. Generate evidence of backfill operations
    """
    
    def __init__(
        self,
        strict_mode: bool = True,
        evidence_dir: Optional[Path] = None
    ):
        """
        Initialize metadata backfiller.
        
        Args:
            strict_mode: If True, fail on uncomputable metadata
            evidence_dir: Directory for evidence artifacts
        """
        self.strict_mode = strict_mode
        self.evidence_dir = evidence_dir or Path(".state/evidence/phase2")
        self.stats = {
            "records_processed": 0,
            "doc_id_filled": 0,
            "file_size_filled": 0,
            "canonicality_filled": 0,
            "errors": 0
        }
    
    def backfill_record(self, record: Dict) -> Dict:
        """
        Backfill missing metadata for a single record.
        
        Args:
            record: Registry record (may have missing fields)
        
        Returns:
            Updated record with backfilled metadata
        
        Raises:
            MetadataBackfillError: If required metadata cannot be computed
        """
        self.stats["records_processed"] += 1
        updated_record = record.copy()
        
        # Backfill doc_id
        if "doc_id" not in updated_record or not updated_record["doc_id"]:
            doc_id = self._compute_doc_id(updated_record)
            if doc_id:
                updated_record["doc_id"] = doc_id
                self.stats["doc_id_filled"] += 1
                logger.info(f"Backfilled doc_id: {doc_id}")
            elif self.strict_mode:
                raise MetadataBackfillError("Cannot compute doc_id in strict mode")
        
        # Backfill file_size
        if "file_size" not in updated_record or updated_record["file_size"] is None:
            file_size = self._compute_file_size(updated_record)
            if file_size is not None:
                updated_record["file_size"] = file_size
                self.stats["file_size_filled"] += 1
                logger.info(f"Backfilled file_size: {file_size}")
            elif self.strict_mode:
                raise MetadataBackfillError("Cannot compute file_size in strict mode")
        
        # Backfill canonicality
        if "canonicality" not in updated_record:
            canonicality = self._compute_canonicality(updated_record)
            updated_record["canonicality"] = canonicality
            self.stats["canonicality_filled"] += 1
            logger.info(f"Backfilled canonicality: {canonicality}")
        
        return updated_record
    
    def _compute_doc_id(self, record: Dict) -> Optional[str]:
        """
        Compute doc_id from available fields.
        
        Priority:
        1. Use file_id if available (file_id = doc_id for single-file documents)
        2. Generate from sha256 hash
        3. Generate from content hash if file_path available
        """
        # Option 1: Use file_id
        if "file_id" in record and record["file_id"]:
            return f"DOC_{record['file_id']}"
        
        # Option 2: Use sha256
        if "sha256" in record and record["sha256"]:
            # Use first 20 chars of sha256 as doc_id seed
            sha256_prefix = record["sha256"][:20]
            return f"DOC_{sha256_prefix}"
        
        # Option 3: Compute from file_path
        if "file_path" in record and record["file_path"]:
            path = Path(record["file_path"])
            if path.exists():
                # Compute hash of file path + size as doc_id
                path_hash = hashlib.sha256(str(path).encode()).hexdigest()[:20]
                return f"DOC_{path_hash}"
        
        logger.warning(f"Cannot compute doc_id for record: {record.get('sha256', 'unknown')}")
        return None
    
    def _compute_file_size(self, record: Dict) -> Optional[int]:
        """
        Compute file_size from available data.
        
        Priority:
        1. Read from filesystem if file_path available
        2. Use content length if content available
        3. Return None if uncomputable
        """
        # Option 1: Read from filesystem
        if "file_path" in record and record["file_path"]:
            path = Path(record["file_path"])
            if path.exists():
                return path.stat().st_size
        
        # Option 2: Compute from content
        if "content" in record and record["content"]:
            if isinstance(record["content"], str):
                return len(record["content"].encode('utf-8'))
            elif isinstance(record["content"], bytes):
                return len(record["content"])
        
        logger.warning(f"Cannot compute file_size for record: {record.get('sha256', 'unknown')}")
        return None
    
    def _compute_canonicality(self, record: Dict) -> bool:
        """
        Compute canonicality (whether file is the canonical version).
        
        Heuristics:
        1. If duplicate_group exists and record is first in group → canonical=True
        2. If sha256 appears only once in dataset → canonical=True
        3. Default → canonical=False (conservative)
        """
        # Check if explicitly marked as canonical
        if "is_canonical" in record:
            return record["is_canonical"]
        
        # Check duplicate group
        if "duplicate_group" in record:
            group = record["duplicate_group"]
            if isinstance(group, list) and len(group) > 0:
                # First file in duplicate group is canonical
                return record.get("file_path") == group[0] if "file_path" in record else False
        
        # Default: assume not canonical (conservative)
        return False
    
    def backfill_batch(self, records: List[Dict]) -> List[Dict]:
        """
        Backfill metadata for multiple records.
        
        Args:
            records: List of registry records
        
        Returns:
            List of updated records with backfilled metadata
        """
        updated_records = []
        for record in records:
            try:
                updated_record = self.backfill_record(record)
                updated_records.append(updated_record)
            except MetadataBackfillError as e:
                logger.error(f"Failed to backfill record: {e}")
                self.stats["errors"] += 1
                if self.strict_mode:
                    raise
                else:
                    # Keep original record in lenient mode
                    updated_records.append(record)
        
        return updated_records
    
    def validate_metadata(self, record: Dict) -> Tuple[bool, List[str]]:
        """
        Validate that all required metadata fields are present and valid.
        
        Args:
            record: Registry record
        
        Returns:
            (is_valid, missing_fields)
        """
        required_fields = ["doc_id", "file_size", "canonicality"]
        missing = []
        
        for field in required_fields:
            if field not in record or record[field] is None:
                missing.append(field)
        
        return (len(missing) == 0, missing)
    
    def create_evidence(self, output_path: Path, backfilled_records: List[Dict]):
        """Generate evidence report for metadata backfill."""
        evidence = {
            "component": "metadata_backfiller",
            "contracts": ["output_result_envelope_contract", "pass_fail_criteria_contract"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "configuration": {
                "strict_mode": self.strict_mode
            },
            "statistics": self.get_stats(),
            "backfill_summary": {
                "total_records": len(backfilled_records),
                "complete_records": sum(1 for r in backfilled_records if self.validate_metadata(r)[0]),
                "incomplete_records": sum(1 for r in backfilled_records if not self.validate_metadata(r)[0])
            },
            "sample_records": backfilled_records[:5] if backfilled_records else []
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.info(f"Evidence written to {output_path}")
    
    def get_stats(self) -> Dict:
        """Get backfill statistics."""
        return self.stats.copy()
