#!/usr/bin/env python3
"""
Validate determinism of conflict graph computation.
Gate: GATE-PWE-011 (determinism validate)
"""

import sys
import json
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class DeterminismValidator:
    def __init__(self):
        self.volatile_fields = ['analysis_timestamp', 'timestamp', 'created_at', 'run_id']
    
    def normalize_data(self, data: Any) -> Any:
        """Recursively normalize volatile fields for deterministic comparison"""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                if key in self.volatile_fields:
                    # Replace volatile timestamps with fixed value
                    normalized[key] = "2026-01-01T00:00:00Z"
                else:
                    normalized[key] = self.normalize_data(value)
            return normalized
        elif isinstance(data, list):
            return [self.normalize_data(item) for item in data]
        else:
            return data
    
    def compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute deterministic hash of normalized data"""
        # Normalize data
        normalized = self.normalize_data(data)
        
        # Convert to canonical JSON (sorted keys)
        canonical_json = json.dumps(normalized, sort_keys=True, indent=2)
        
        # Compute SHA-256
        sha256_hash = hashlib.sha256()
        sha256_hash.update(canonical_json.encode('utf-8'))
        
        return sha256_hash.hexdigest()
    
    def run_conflict_graph_computation(self, plan_file: Path, script_path: Path, output_dir: Path) -> Path:
        """Run conflict graph computation and return output file"""
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--plan", str(plan_file),
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Conflict graph computation failed: {result.stderr}")
        
        return output_dir / "artifacts" / "conflict_graph" / "conflict_graph.json"
    
    def validate_determinism(
        self,
        plan_file: Path,
        compute_script: Path,
        num_runs: int = 2
    ) -> Dict[str, Any]:
        """Run conflict graph computation multiple times and validate determinism"""
        hashes = []
        output_files = []
        
        for run_idx in range(num_runs):
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Run computation
                output_file = self.run_conflict_graph_computation(plan_file, compute_script, temp_path)
                
                # Load result
                with open(output_file, 'r', encoding='utf-8') as f:
                    conflict_graph = json.load(f)
                
                # Compute hash
                graph_hash = self.compute_hash(conflict_graph)
                hashes.append(graph_hash)
                output_files.append(str(output_file))
        
        # Check if all hashes match
        all_match = len(set(hashes)) == 1
        
        report = {
            "determinism_validated": all_match,
            "num_runs": num_runs,
            "hashes": hashes,
            "hash_match": all_match,
            "first_hash": hashes[0] if hashes else None,
            "validation_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return report
    
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
        description="Validate determinism of conflict graph computation"
    )
    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="Path to plan JSON file"
    )
    parser.add_argument(
        "--compute-script",
        type=Path,
        default=None,
        help="Path to compute_conflict_graph.py script"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for determinism report"
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=2,
        help="Number of runs for comparison"
    )
    
    args = parser.parse_args()
    
    # Auto-detect compute script
    if args.compute_script is None:
        script_dir = Path(__file__).parent
        args.compute_script = script_dir / "compute_conflict_graph.py"
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = args.plan.parent
    
    try:
        # Run validation
        validator = DeterminismValidator()
        report = validator.validate_determinism(args.plan, args.compute_script, args.num_runs)
        
        # Write determinism report
        artifact_dir = args.output_dir / "evidence" / "determinism"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = artifact_dir / "determinism_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Write gate result
        if report['determinism_validated']:
            validator.write_gate_result("GATE-PWE-011", True, None, args.output_dir)
            
            print(f"✓ GATE-PWE-011: Determinism validated")
            print(f"  Runs: {report['num_runs']}")
            print(f"  Hash: {report['first_hash']}")
            sys.exit(0)
        else:
            error_msg = "Hash mismatch across runs - computation is not deterministic"
            validator.write_gate_result("GATE-PWE-011", False, error_msg, args.output_dir)
            
            print(f"✗ GATE-PWE-011 FAILED: {error_msg}", file=sys.stderr)
            print(f"  Hashes: {report['hashes']}", file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
