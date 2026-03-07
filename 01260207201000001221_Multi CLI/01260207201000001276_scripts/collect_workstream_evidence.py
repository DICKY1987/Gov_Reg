#!/usr/bin/env python3
"""
Collect workstream execution evidence and package into evidence bundle.
Gate: GATE-PWE-008 (evidence bundle validate)
"""

import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import jsonschema


class EvidenceCollector:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Any]:
        """Load required schemas"""
        schemas = {}
        schema_path = self.schema_dir / "evidence_bundle.schema.json"
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schemas['evidence_bundle'] = json.load(f)
        
        return schemas
    
    def compute_sha256(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def collect_gate_results(self, evidence_dir: Path) -> List[Dict[str, Any]]:
        """Collect all gate results for workstream"""
        gate_results = []
        gates_dir = evidence_dir / "gates"
        
        if gates_dir.exists():
            for gate_file in sorted(gates_dir.glob("GATE-PWE-*.result.json")):
                with open(gate_file, 'r', encoding='utf-8') as f:
                    gate_data = json.load(f)
                    gate_results.append({
                        "gate_id": gate_data['gate_id'],
                        "passed": gate_data['passed'],
                        "timestamp": gate_data['timestamp'],
                        "evidence_path": str(gate_file.relative_to(evidence_dir)),
                        "error": gate_data.get('error')
                    })
        
        return gate_results
    
    def collect_artifacts(self, artifacts_base: Path, workstream_id: str) -> Tuple[List[Dict], Dict[str, str]]:
        """Collect artifacts and compute hashes"""
        artifacts = []
        hash_manifest = {}
        
        # Define artifact locations
        artifact_patterns = [
            ("worktree_report", f"worktrees/{workstream_id}_report.json"),
            ("execution_log", f"logs/{workstream_id}.log"),
            ("patch", f"patches/{workstream_id}/*.patch")
        ]
        
        for artifact_type, pattern in artifact_patterns:
            if '*' in pattern:
                # Glob pattern
                base_dir = artifacts_base / Path(pattern).parent
                if base_dir.exists():
                    for artifact_file in base_dir.glob(Path(pattern).name):
                        self._add_artifact(artifact_file, artifact_type, artifacts_base, artifacts, hash_manifest)
            else:
                # Single file
                artifact_file = artifacts_base / pattern
                if artifact_file.exists():
                    self._add_artifact(artifact_file, artifact_type, artifacts_base, artifacts, hash_manifest)
        
        return artifacts, hash_manifest
    
    def _add_artifact(
        self,
        artifact_file: Path,
        artifact_type: str,
        base_path: Path,
        artifacts: List[Dict],
        hash_manifest: Dict[str, str]
    ):
        """Add artifact to collection"""
        rel_path = str(artifact_file.relative_to(base_path))
        sha256 = self.compute_sha256(artifact_file)
        size = artifact_file.stat().st_size
        
        artifacts.append({
            "artifact_type": artifact_type,
            "path": rel_path,
            "sha256": sha256,
            "size_bytes": size
        })
        
        hash_manifest[rel_path] = sha256
    
    def create_evidence_bundle(
        self,
        run_id: str,
        workstream_id: str,
        evidence_dir: Path,
        artifacts_dir: Path
    ) -> Dict[str, Any]:
        """Create complete evidence bundle"""
        # Collect gate results
        gate_results = self.collect_gate_results(evidence_dir)
        
        # Collect artifacts
        artifacts, hash_manifest = self.collect_artifacts(artifacts_dir, workstream_id)
        
        # Build evidence bundle
        bundle = {
            "run_id": run_id,
            "workstream_id": workstream_id,
            "gate_results": gate_results,
            "artifacts": artifacts,
            "hash_manifest": hash_manifest,
            "bundle_metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "bundle_version": "1.0.0",
                "total_artifacts": len(artifacts),
                "total_size_bytes": sum(a['size_bytes'] for a in artifacts)
            }
        }
        
        # Validate against schema
        jsonschema.validate(
            instance=bundle,
            schema=self.schemas['evidence_bundle']
        )
        
        return bundle
    
    def write_gate_result(self, gate_id: str, passed: bool, error: str, output_dir: Path):
        """Write gate result"""
        gate_dir = output_dir / "evidence" / "gates"
        gate_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            "gate_id": gate_id,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error
        }
        
        result_file = gate_dir / f"{gate_id}.result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Collect workstream execution evidence"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier"
    )
    parser.add_argument(
        "--workstream-id",
        required=True,
        help="Workstream identifier"
    )
    parser.add_argument(
        "--evidence-dir",
        required=True,
        type=Path,
        help="Evidence directory"
    )
    parser.add_argument(
        "--artifacts-dir",
        required=True,
        type=Path,
        help="Artifacts directory"
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Schemas directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for evidence bundle"
    )
    
    args = parser.parse_args()
    
    # Auto-detect schema directory
    if args.schema_dir is None:
        script_dir = Path(__file__).parent
        args.schema_dir = script_dir.parent / "01260207201000001275_schemas"
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = args.evidence_dir.parent
    
    try:
        # Create collector
        collector = EvidenceCollector(args.schema_dir)
        
        # Create evidence bundle
        bundle = collector.create_evidence_bundle(
            args.run_id,
            args.workstream_id,
            args.evidence_dir,
            args.artifacts_dir
        )
        
        # Write evidence bundle
        bundle_dir = args.output_dir / "evidence" / "workstreams" / args.workstream_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        
        bundle_file = bundle_dir / "evidence_bundle.json"
        with open(bundle_file, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2)
        
        # Write gate result
        collector.write_gate_result("GATE-PWE-008", True, None, args.output_dir)
        
        print(f"✓ GATE-PWE-008: Evidence bundle created successfully")
        print(f"  Workstream: {args.workstream_id}")
        print(f"  Gate results: {len(bundle['gate_results'])}")
        print(f"  Artifacts: {len(bundle['artifacts'])}")
        print(f"  Total size: {bundle['bundle_metadata']['total_size_bytes']} bytes")
        print(f"  Bundle: {bundle_file}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        
        collector = EvidenceCollector(args.schema_dir)
        collector.write_gate_result("GATE-PWE-008", False, str(e), args.output_dir)
        
        sys.exit(1)


if __name__ == "__main__":
    main()
