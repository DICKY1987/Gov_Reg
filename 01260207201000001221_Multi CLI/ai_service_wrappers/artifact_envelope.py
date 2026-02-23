#!/usr/bin/env python3
"""
Artifact Envelope Library - Universal envelope creation and lineage integrity verification.

Provides deterministic envelope creation, SHA-256 computation, and LIV (Lineage Integrity 
Verification) checks for artifact provenance tracking.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import jsonschema


class ArtifactEnvelope:
    """Create and validate artifact envelopes with lineage tracking."""
    
    SCHEMA_ID = "acms.artifact_envelope.v1"
    SCHEMA_VERSION = "1.0.0"
    
    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of file contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"
    
    @staticmethod
    def create_envelope(
        artifact_path: Path,
        run_id: str,
        produced_by_type: str,
        produced_by_id: str,
        attempt: int,
        derived_from_artifacts: List[Dict[str, str]],
        transformation_rule: str,
        process_semantic_version: str,
        process_logic_hash: str,
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Create an artifact envelope with full provenance.
        
        Args:
            artifact_path: Path to the artifact file
            run_id: Run identifier (e.g., RUN_20260215_...)
            produced_by_type: "phase", "gate", or "heal"
            produced_by_id: Tool/phase identifier
            attempt: Attempt number (1-based)
            derived_from_artifacts: List of input artifacts with path and sha256
            transformation_rule: Description of transformation applied
            process_semantic_version: Version of the process
            process_logic_hash: SHA-256 hash of process logic
            output_path: Where to write the envelope JSON
        
        Returns:
            The envelope dictionary
        """
        artifact_sha256 = ArtifactEnvelope.compute_sha256(artifact_path)
        artifact_id = artifact_sha256
        
        envelope = {
            "artifact_id": artifact_id,
            "schema_id": ArtifactEnvelope.SCHEMA_ID,
            "schema_version": ArtifactEnvelope.SCHEMA_VERSION,
            "run_id": run_id,
            "produced_at": datetime.now(timezone.utc).isoformat(),
            "artifact": {
                "path": str(artifact_path),
                "sha256": artifact_sha256
            },
            "provenance": {
                "produced_by": {
                    "type": produced_by_type,
                    "id": produced_by_id,
                    "attempt": attempt
                },
                "derived_from_artifacts": derived_from_artifacts,
                "transformation_rule": transformation_rule
            },
            "process_identity": {
                "semantic_version": process_semantic_version,
                "logic_hash": process_logic_hash
            }
        }
        
        # Write envelope
        with open(output_path, 'w') as f:
            json.dump(envelope, f, indent=2)
        
        return envelope
    
    @staticmethod
    def verify_lineage(
        input_artifacts: List[Dict[str, str]],
        evidence_output_path: Optional[Path] = None
    ) -> bool:
        """
        Verify lineage integrity by recomputing SHA-256 hashes.
        
        Args:
            input_artifacts: List of dicts with 'path' and 'sha256' keys
            evidence_output_path: Optional path to write io_validation.json
        
        Returns:
            True if all hashes match, False otherwise (fail-closed)
        """
        mismatches = []
        
        for artifact in input_artifacts:
            path = Path(artifact["path"])
            expected_sha256 = artifact["sha256"]
            
            if not path.exists():
                mismatches.append({
                    "path": str(path),
                    "error": "FILE_NOT_FOUND",
                    "expected_sha256": expected_sha256
                })
                continue
            
            actual_sha256 = ArtifactEnvelope.compute_sha256(path)
            
            if actual_sha256 != expected_sha256:
                mismatches.append({
                    "path": str(path),
                    "error": "SHA256_MISMATCH",
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256
                })
        
        # Write evidence
        if evidence_output_path:
            evidence = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "artifacts_checked": len(input_artifacts),
                "mismatches_found": len(mismatches),
                "status": "PASS" if len(mismatches) == 0 else "FAIL",
                "mismatches": mismatches
            }
            evidence_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(evidence_output_path, 'w') as f:
                json.dump(evidence, f, indent=2)
        
        return len(mismatches) == 0


def main():
    """CLI entry point for envelope operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Artifact envelope operations")
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Create envelope
    create_parser = subparsers.add_parser('create', help='Create artifact envelope')
    create_parser.add_argument('--artifact-path', required=True, help='Path to artifact')
    create_parser.add_argument('--run-id', required=True, help='Run ID')
    create_parser.add_argument('--produced-by-type', required=True, choices=['phase', 'gate', 'heal'])
    create_parser.add_argument('--produced-by-id', required=True, help='Producer ID')
    create_parser.add_argument('--attempt', type=int, default=1, help='Attempt number')
    create_parser.add_argument('--derived-from', help='JSON array of input artifacts')
    create_parser.add_argument('--transformation-rule', required=True, help='Transformation description')
    create_parser.add_argument('--process-version', required=True, help='Process version')
    create_parser.add_argument('--process-hash', required=True, help='Process logic hash')
    create_parser.add_argument('--output', required=True, help='Output envelope path')
    
    # Verify lineage
    verify_parser = subparsers.add_parser('verify', help='Verify artifact lineage')
    verify_parser.add_argument('--inputs', required=True, help='JSON array of input artifacts')
    verify_parser.add_argument('--evidence-output', help='Path to write io_validation.json')
    
    # Compute hash
    hash_parser = subparsers.add_parser('hash', help='Compute SHA-256 hash')
    hash_parser.add_argument('path', help='File path')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        derived_from = json.loads(args.derived_from) if args.derived_from else []
        envelope = ArtifactEnvelope.create_envelope(
            artifact_path=Path(args.artifact_path),
            run_id=args.run_id,
            produced_by_type=args.produced_by_type,
            produced_by_id=args.produced_by_id,
            attempt=args.attempt,
            derived_from_artifacts=derived_from,
            transformation_rule=args.transformation_rule,
            process_semantic_version=args.process_version,
            process_logic_hash=args.process_hash,
            output_path=Path(args.output)
        )
        print(f"Envelope created: {args.output}")
        print(f"Artifact ID: {envelope['artifact_id']}")
        sys.exit(0)
    
    elif args.command == 'verify':
        inputs = json.loads(args.inputs)
        evidence_path = Path(args.evidence_output) if args.evidence_output else None
        success = ArtifactEnvelope.verify_lineage(inputs, evidence_path)
        if success:
            print("✓ Lineage verification PASSED")
            sys.exit(0)
        else:
            print("✗ Lineage verification FAILED")
            sys.exit(1)
    
    elif args.command == 'hash':
        hash_value = ArtifactEnvelope.compute_sha256(Path(args.path))
        print(hash_value)
        sys.exit(0)


if __name__ == "__main__":
    main()
