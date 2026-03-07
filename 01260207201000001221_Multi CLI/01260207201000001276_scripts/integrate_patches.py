#!/usr/bin/env python3
"""
Integrate patches from parallel workstreams in topological order.
Gates: GATE-PWE-009 (integrate patches), GATE-PWE-010 (integration validate)
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import jsonschema


@dataclass
class MergeConflict:
    file_path: str
    conflicting_workstreams: List[str]
    conflict_markers: Optional[str] = None


@dataclass
class MergeResult:
    success: bool
    applied_patches: List[Dict[str, Any]]
    failed_patches: List[Dict[str, Any]]
    conflicts: List[MergeConflict]
    rollback_occurred: bool


class PatchIntegrator:
    def __init__(self, repo_root: Path, schema_dir: Path):
        self.repo_root = repo_root
        self.schema_dir = schema_dir
        self.schemas = self._load_schemas()
        
    def _load_schemas(self) -> Dict[str, Any]:
        """Load required schemas"""
        schemas = {}
        schema_path = self.schema_dir / "integration_report.schema.json"
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schemas['integration_report'] = json.load(f)
        
        return schemas
    
    def load_integration_order(self, parallel_groups_file: Path) -> List[str]:
        """Load topological integration order from parallel groups"""
        with open(parallel_groups_file, 'r', encoding='utf-8') as f:
            groups_data = json.load(f)
        
        # Flatten parallel groups into sequential integration order
        integration_order = []
        for group in groups_data['parallel_groups']:
            integration_order.extend(sorted(group))
        
        return integration_order
    
    def find_patches(self, patches_dir: Path, workstream_id: str) -> List[Path]:
        """Find all patch files for a workstream"""
        patches = []
        ws_patch_dir = patches_dir / workstream_id
        
        if ws_patch_dir.exists():
            patches = sorted(ws_patch_dir.glob("*.patch"))
        
        return patches
    
    def apply_patch(self, patch_file: Path) -> bool:
        """Apply a single patch with git apply"""
        # First check if patch applies cleanly
        check_result = subprocess.run(
            ["git", "-C", str(self.repo_root), "apply", "--check", str(patch_file)],
            capture_output=True,
            text=True
        )
        
        if check_result.returncode != 0:
            return False
        
        # Apply the patch
        apply_result = subprocess.run(
            ["git", "-C", str(self.repo_root), "apply", str(patch_file)],
            capture_output=True,
            text=True
        )
        
        return apply_result.returncode == 0
    
    def rollback_patches(self, applied_patches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rollback applied patches in reverse order"""
        rollback_log = []
        
        for patch_info in reversed(applied_patches):
            patch_file = Path(patch_info['file_path'])
            
            try:
                # Apply patch in reverse
                result = subprocess.run(
                    ["git", "-C", str(self.repo_root), "apply", "--reverse", str(patch_file)],
                    capture_output=True,
                    text=True
                )
                
                rollback_log.append({
                    "action": f"Reversed patch: {patch_file.name}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "success": result.returncode == 0,
                    "error": result.stderr if result.returncode != 0 else None
                })
            except Exception as e:
                rollback_log.append({
                    "action": f"Failed to reverse patch: {patch_file.name}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "success": False,
                    "error": str(e)
                })
        
        # Reset to clean state
        try:
            subprocess.run(
                ["git", "-C", str(self.repo_root), "reset", "--hard", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            rollback_log.append({
                "action": "Reset to HEAD",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "success": True,
                "error": None
            })
        except Exception as e:
            rollback_log.append({
                "action": "Failed to reset to HEAD",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "success": False,
                "error": str(e)
            })
        
        return rollback_log
    
    def integrate_workstreams(
        self,
        integration_order: List[str],
        patches_dir: Path
    ) -> MergeResult:
        """Integrate patches in topological order"""
        applied_patches = []
        failed_patches = []
        conflicts = []
        
        for workstream_id in integration_order:
            patch_files = self.find_patches(patches_dir, workstream_id)
            
            for patch_file in patch_files:
                if self.apply_patch(patch_file):
                    applied_patches.append({
                        "workstream_id": workstream_id,
                        "file_path": str(patch_file),
                        "apply_timestamp": datetime.utcnow().isoformat() + "Z",
                        "patch_sha256": self._compute_sha256(patch_file)
                    })
                else:
                    # Patch failed - record and trigger rollback
                    with open(patch_file, 'r', encoding='utf-8') as f:
                        patch_content = f.read()
                    
                    failed_patches.append({
                        "workstream_id": workstream_id,
                        "file_path": str(patch_file),
                        "error": "Failed to apply patch",
                        "patch_content": patch_content[:1000]  # Truncate for size
                    })
                    
                    # Detect conflict
                    conflicts.append(MergeConflict(
                        file_path=str(patch_file),
                        conflicting_workstreams=[workstream_id]
                    ))
                    
                    # Rollback and exit
                    rollback_log = self.rollback_patches(applied_patches)
                    
                    return MergeResult(
                        success=False,
                        applied_patches=applied_patches,
                        failed_patches=failed_patches,
                        conflicts=conflicts,
                        rollback_occurred=True
                    )
        
        return MergeResult(
            success=True,
            applied_patches=applied_patches,
            failed_patches=failed_patches,
            conflicts=conflicts,
            rollback_occurred=False
        )
    
    def _compute_sha256(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        import hashlib
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def create_integration_report(
        self,
        merge_result: MergeResult,
        integration_order: List[str],
        rollback_log: List[Dict] = None
    ) -> Dict[str, Any]:
        """Create integration report"""
        report = {
            "applied_patches": merge_result.applied_patches,
            "failed_patches": merge_result.failed_patches,
            "conflicts": [
                {
                    "file_path": c.file_path,
                    "conflicting_workstreams": c.conflicting_workstreams,
                    "conflict_markers": c.conflict_markers
                }
                for c in merge_result.conflicts
            ],
            "rollback_log": rollback_log or [],
            "integration_order": integration_order,
            "integration_metadata": {
                "start_time": datetime.utcnow().isoformat() + "Z",
                "end_time": datetime.utcnow().isoformat() + "Z",
                "total_patches_applied": len(merge_result.applied_patches),
                "rollback_occurred": merge_result.rollback_occurred,
                "final_commit_sha": self._get_current_commit()
            }
        }
        
        # Validate against schema
        jsonschema.validate(
            instance=report,
            schema=self.schemas['integration_report']
        )
        
        return report
    
    def _get_current_commit(self) -> str:
        """Get current commit SHA"""
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
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
        description="Integrate patches from parallel workstreams"
    )
    parser.add_argument(
        "--parallel-groups",
        required=True,
        type=Path,
        help="Path to parallel_groups.json"
    )
    parser.add_argument(
        "--patches-dir",
        required=True,
        type=Path,
        help="Directory containing patch files"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root"
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
        help="Output directory for integration report"
    )
    
    args = parser.parse_args()
    
    # Auto-detect repo root
    if args.repo_root is None:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        args.repo_root = Path(result.stdout.strip())
    
    # Auto-detect schema directory
    if args.schema_dir is None:
        script_dir = Path(__file__).parent
        args.schema_dir = script_dir.parent / "01260207201000001275_schemas"
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = args.parallel_groups.parent.parent.parent
    
    try:
        # Initialize integrator
        integrator = PatchIntegrator(args.repo_root, args.schema_dir)
        
        # Load integration order
        integration_order = integrator.load_integration_order(args.parallel_groups)
        
        # Integrate patches
        merge_result = integrator.integrate_workstreams(integration_order, args.patches_dir)
        
        # Create integration report
        report = integrator.create_integration_report(merge_result, integration_order)
        
        # Write integration report
        artifact_dir = args.output_dir / "artifacts" / "integration"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = artifact_dir / "integration_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        # Write rollback log if rollback occurred
        if merge_result.rollback_occurred:
            rollback_file = artifact_dir / "rollback_log.json"
            with open(rollback_file, 'w', encoding='utf-8') as f:
                json.dump({"rollback_log": report['rollback_log']}, f, indent=2)
        
        # Write gate results
        integrator.write_gate_result("GATE-PWE-009", merge_result.success, None, args.output_dir)
        integrator.write_gate_result("GATE-PWE-010", merge_result.success, None, args.output_dir)
        
        if merge_result.success:
            print(f"✓ GATE-PWE-009: Integration completed successfully")
            print(f"✓ GATE-PWE-010: Integration validated")
            print(f"  Applied patches: {len(merge_result.applied_patches)}")
            print(f"  Integration order: {', '.join(integration_order)}")
            sys.exit(0)
        else:
            print(f"✗ GATE-PWE-009 FAILED: Integration failed", file=sys.stderr)
            print(f"  Failed patches: {len(merge_result.failed_patches)}", file=sys.stderr)
            print(f"  Conflicts: {len(merge_result.conflicts)}", file=sys.stderr)
            print(f"  Rollback performed", file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
