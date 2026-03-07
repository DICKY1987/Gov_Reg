#!/usr/bin/env python3
"""
Enforce declared write manifests after workstream execution.
Gate: GATE-PWE-007 (declared writes enforcement)
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any


class DeclaredWriteEnforcer:
    def __init__(self):
        pass
    
    def get_touched_files(self, worktree_path: Path, base_commit: str = "HEAD") -> Set[str]:
        """Get list of files modified in worktree"""
        result = subprocess.run(
            ["git", "-C", str(worktree_path), "diff", "--name-only", base_commit],
            capture_output=True,
            text=True,
            check=True
        )
        
        touched = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                touched.add(line)
        
        return touched
    
    def check_violations(
        self,
        touched_files: Set[str],
        declared_writes: List[str],
        declared_reads: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for write manifest violations"""
        violations = []
        declared_writes_set = set(declared_writes)
        declared_reads_set = set(declared_reads)
        
        # Check for undeclared writes
        for file_path in touched_files:
            if file_path not in declared_writes_set:
                violations.append({
                    "violation_type": "undeclared_write",
                    "file_path": file_path,
                    "severity": "error"
                })
        
        # Check if any declared writes were not actually touched (warning only)
        for declared_file in declared_writes:
            if declared_file not in touched_files:
                violations.append({
                    "violation_type": "declared_but_not_written",
                    "file_path": declared_file,
                    "severity": "warning"
                })
        
        return violations
    
    def write_gate_result(self, gate_id: str, passed: bool, error: str, violations: List[Dict], output_dir: Path):
        """Write gate result with violation details"""
        gate_dir = output_dir / "evidence" / "gates"
        gate_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            "gate_id": gate_id,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error,
            "violations": violations
        }
        
        result_file = gate_dir / f"{gate_id}.result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Enforce declared write manifests for workstream execution"
    )
    parser.add_argument(
        "--worktree",
        required=True,
        type=Path,
        help="Path to worktree"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to write manifest JSON"
    )
    parser.add_argument(
        "--base-commit",
        default="HEAD",
        help="Base commit for diff comparison"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for gate results"
    )
    
    args = parser.parse_args()
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = Path.cwd()
    
    try:
        # Load write manifest
        with open(args.manifest, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        workstream_id = manifest['workstream_id']
        declared_writes = manifest.get('declared_writes', [])
        declared_reads = manifest.get('declared_reads', [])
        
        # Get touched files
        enforcer = DeclaredWriteEnforcer()
        touched_files = enforcer.get_touched_files(args.worktree, args.base_commit)
        
        # Check violations
        violations = enforcer.check_violations(touched_files, declared_writes, declared_reads)
        
        # Filter only error-level violations
        error_violations = [v for v in violations if v['severity'] == 'error']
        
        # Write gate result
        if error_violations:
            error_msg = f"Found {len(error_violations)} undeclared writes"
            enforcer.write_gate_result("GATE-PWE-007", False, error_msg, violations, args.output_dir)
            
            print(f"✗ GATE-PWE-007 FAILED: {error_msg}", file=sys.stderr)
            for violation in error_violations:
                print(f"  {violation['violation_type']}: {violation['file_path']}", file=sys.stderr)
            
            sys.exit(1)
        else:
            enforcer.write_gate_result("GATE-PWE-007", True, None, violations, args.output_dir)
            
            print(f"✓ GATE-PWE-007: Declared writes enforcement passed")
            print(f"  Workstream: {workstream_id}")
            print(f"  Touched files: {len(touched_files)}")
            print(f"  Declared writes: {len(declared_writes)}")
            
            if violations:
                print(f"  Warnings: {len(violations)}")
            
            sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
