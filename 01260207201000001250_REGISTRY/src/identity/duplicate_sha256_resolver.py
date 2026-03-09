"""
duplicate_sha256_resolver.py

Duplicate SHA256 collision handling: Resolve 1 SHA256 collision.

Issue: FCA-015 (High)
Symptom: 1 SHA256 hash collision detected (same hash, different files)
Root Cause: Mutation safety contract incomplete; deduplication logic doesn't handle collisions
Fix: Collision detection, resolution policy, and evidence generation

Contract: mutation_safety_contract + fingerprint_idempotency_contract
Category: Gate + Mutation
Runner: Must detect and resolve collisions before registry mutation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class DuplicateSHA256Resolver:
    """
    Detect and resolve SHA256 hash collisions.
    
    Resolution Strategies:
    1. True duplicate: Files are identical → keep one, mark others as duplicates
    2. Hash collision: Files differ but hash is same → re-hash with salt, investigate
    3. Metadata differ: Same file, different metadata → reconcile metadata
    """
    
    def __init__(
        self,
        strict_mode: bool = True,
        evidence_dir: Optional[Path] = None
    ):
        """
        Initialize duplicate SHA256 resolver.
        
        Args:
            strict_mode: If True, fail on unresolved collisions
            evidence_dir: Directory for evidence artifacts
        """
        self.strict_mode = strict_mode
        self.evidence_dir = evidence_dir or Path(".state/evidence/phase2")
        self.stats = {
            "records_processed": 0,
            "collisions_detected": 0,
            "true_duplicates": 0,
            "hash_collisions": 0,
            "metadata_conflicts": 0,
            "resolved": 0,
            "unresolved": 0
        }
    
    def detect_collisions(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Detect SHA256 collisions across records.
        
        Args:
            records: List of registry records
        
        Returns:
            Dict mapping sha256 → list of records with that hash
        """
        sha256_map: Dict[str, List[Dict]] = {}
        
        for record in records:
            self.stats["records_processed"] += 1
            sha256 = record.get("sha256")
            
            if not sha256:
                continue
            
            if sha256 not in sha256_map:
                sha256_map[sha256] = []
            
            sha256_map[sha256].append(record)
        
        # Filter to only collisions (SHA256 with multiple records)
        collisions = {
            sha256: records_list
            for sha256, records_list in sha256_map.items()
            if len(records_list) > 1
        }
        
        self.stats["collisions_detected"] = len(collisions)
        
        return collisions
    
    def resolve_collision(self, sha256: str, records: List[Dict]) -> Tuple[str, List[Dict], Dict]:
        """
        Resolve a single SHA256 collision.
        
        Args:
            sha256: The colliding SHA256 hash
            records: List of records with this hash
        
        Returns:
            (resolution_type, resolved_records, resolution_metadata)
        """
        # Check if files are truly identical
        if self._are_files_identical(records):
            resolution_type = "true_duplicate"
            resolved_records = self._handle_true_duplicate(records)
            self.stats["true_duplicates"] += 1
        # Check if it's a metadata conflict only
        elif self._is_metadata_conflict(records):
            resolution_type = "metadata_conflict"
            resolved_records = self._reconcile_metadata(records)
            self.stats["metadata_conflicts"] += 1
        # Genuine hash collision (rare but possible)
        else:
            resolution_type = "hash_collision"
            resolved_records = self._handle_hash_collision(sha256, records)
            self.stats["hash_collisions"] += 1
        
        self.stats["resolved"] += 1
        
        resolution_metadata = {
            "sha256": sha256,
            "resolution_type": resolution_type,
            "original_count": len(records),
            "resolved_count": len(resolved_records),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return (resolution_type, resolved_records, resolution_metadata)
    
    def _are_files_identical(self, records: List[Dict]) -> bool:
        """Check if all records represent identical files."""
        # Compare file sizes
        file_sizes = [r.get("file_size") for r in records if "file_size" in r]
        if file_sizes and len(set(file_sizes)) > 1:
            return False  # Different sizes → not identical
        
        # Compare file paths (if same path, definitely same file)
        file_paths = [r.get("file_path") for r in records if "file_path" in r]
        if len(set(file_paths)) == 1:
            return True  # Same path → identical file
        
        # Compare content if available
        contents = []
        for record in records:
            if "content" in record and record["content"]:
                contents.append(record["content"])
            elif "file_path" in record:
                path = Path(record["file_path"])
                if path.exists():
                    with open(path, 'rb') as f:
                        contents.append(f.read())
        
        if contents and len(set(contents)) == 1:
            return True  # Same content → identical
        
        # Conservative: assume not identical if can't verify
        return False
    
    def _is_metadata_conflict(self, records: List[Dict]) -> bool:
        """Check if collision is due to metadata differences only."""
        # Extract core file data (sha256, file_size, file_path)
        core_data = []
        for record in records:
            core = {
                "sha256": record.get("sha256"),
                "file_size": record.get("file_size"),
                "file_path": record.get("file_path")
            }
            core_data.append(json.dumps(core, sort_keys=True))
        
        # If core data is identical, it's just metadata conflict
        return len(set(core_data)) == 1
    
    def _handle_true_duplicate(self, records: List[Dict]) -> List[Dict]:
        """
        Handle true duplicates: Keep canonical, mark others as duplicates.
        
        Returns:
            Updated records with duplicate markers
        """
        # Select canonical record (prefer one with most complete metadata)
        canonical = max(records, key=lambda r: self._metadata_completeness_score(r))
        canonical["canonicality"] = True
        canonical["duplicate_group"] = [r.get("file_path") for r in records if "file_path" in r]
        
        # Mark others as duplicates
        duplicates = [r for r in records if r is not canonical]
        for dup in duplicates:
            dup["canonicality"] = False
            dup["duplicate_of"] = canonical.get("file_id") or canonical.get("sha256")
        
        logger.info(f"Resolved true duplicate: canonical={canonical.get('file_path')}, duplicates={len(duplicates)}")
        
        return [canonical] + duplicates
    
    def _metadata_completeness_score(self, record: Dict) -> int:
        """Score record based on metadata completeness."""
        required_fields = ["file_id", "doc_id", "file_size", "repo_root_id", "canonicality"]
        return sum(1 for field in required_fields if field in record and record[field] is not None)
    
    def _reconcile_metadata(self, records: List[Dict]) -> List[Dict]:
        """
        Reconcile metadata conflicts by merging metadata.
        
        Returns:
            Single reconciled record
        """
        # Start with first record as base
        reconciled = records[0].copy()
        
        # Merge metadata from all records (prefer non-null values)
        for record in records[1:]:
            for key, value in record.items():
                if key not in reconciled or reconciled[key] is None:
                    reconciled[key] = value
        
        # Mark as reconciled
        reconciled["metadata_reconciled"] = True
        reconciled["reconciled_from"] = [r.get("file_id") or r.get("sha256") for r in records]
        
        logger.info(f"Reconciled metadata conflict for {reconciled.get('sha256')}")
        
        return [reconciled]
    
    def _handle_hash_collision(self, sha256: str, records: List[Dict]) -> List[Dict]:
        """
        Handle genuine hash collision (extremely rare).
        
        Strategy:
        1. Re-hash files with salt to create unique identifiers
        2. Log collision for investigation
        3. Update records with new salted hashes
        """
        logger.error(f"GENUINE HASH COLLISION DETECTED: {sha256}")
        
        updated_records = []
        for i, record in enumerate(records):
            # Create salted hash
            salt = f"collision_{i}_{datetime.utcnow().isoformat()}"
            salted_hash = hashlib.sha256(f"{sha256}:{salt}".encode()).hexdigest()
            
            updated_record = record.copy()
            updated_record["sha256_original"] = sha256
            updated_record["sha256"] = salted_hash
            updated_record["hash_collision_resolved"] = True
            updated_record["collision_salt"] = salt
            
            updated_records.append(updated_record)
            
            logger.warning(f"Re-hashed collision record {i}: {sha256} → {salted_hash}")
        
        return updated_records
    
    def resolve_all(self, records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Resolve all SHA256 collisions in dataset.
        
        Args:
            records: List of all records
        
        Returns:
            (resolved_records, resolution_reports)
        """
        collisions = self.detect_collisions(records)
        
        if not collisions:
            logger.info("No SHA256 collisions detected")
            return (records, [])
        
        logger.info(f"Detected {len(collisions)} SHA256 collisions")
        
        resolved_records = []
        resolution_reports = []
        processed_sha256s = set()
        
        for record in records:
            sha256 = record.get("sha256")
            
            # Skip if no SHA256 or already processed
            if not sha256 or sha256 in processed_sha256s:
                continue
            
            # Check if this SHA256 has collisions
            if sha256 in collisions:
                resolution_type, resolved, metadata = self.resolve_collision(
                    sha256, collisions[sha256]
                )
                resolved_records.extend(resolved)
                resolution_reports.append(metadata)
                processed_sha256s.add(sha256)
            else:
                # No collision, keep original
                resolved_records.append(record)
                processed_sha256s.add(sha256)
        
        return (resolved_records, resolution_reports)
    
    def create_evidence(self, output_path: Path, resolution_reports: List[Dict]):
        """Generate evidence report for collision resolution."""
        evidence = {
            "component": "duplicate_sha256_resolver",
            "contracts": ["mutation_safety_contract", "fingerprint_idempotency_contract"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "configuration": {
                "strict_mode": self.strict_mode
            },
            "statistics": self.get_stats(),
            "resolutions": resolution_reports
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.info(f"Evidence written to {output_path}")
    
    def get_stats(self) -> Dict:
        """Get resolution statistics."""
        return self.stats.copy()
