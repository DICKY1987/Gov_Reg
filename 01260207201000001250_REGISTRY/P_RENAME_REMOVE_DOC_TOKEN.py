"""Remove legacy DOC-* tokens from filenames while preserving canonical IDs.

FILE_ID: TBD
VERSION: 1.0.0
SPEC: KI_APP_INSTRUCTIONS for DOC-* token removal
"""
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys

@dataclass
class RenameOperation:
    """Single rename operation."""
    file_id: str
    old_absolute_path: str
    new_absolute_path: str
    old_relative_path: str
    new_relative_path: str
    old_filename: str
    new_filename: str
    collision_resolved: bool
    collision_suffix: Optional[str] = None
    error: Optional[str] = None
    
@dataclass
class RunConfig:
    """Runtime configuration."""
    target_roots: List[str]
    dry_run: bool = False
    strict_registry_check: bool = False
    finalization_mode: str = "staging"
    run_id: str = ""
    timestamp_utc: str = ""

class DOCTokenRemover:
    """Removes legacy DOC-* tokens from filenames."""
    
    # Match: P_<20digits>_DOC-<anything>__<rest>
    MATCH_REGEX = re.compile(r'^(P_\d{20})_DOC-.*?__+(.+)$')
    FILE_ID_REGEX = re.compile(r'^P_(\d{20})_')
    
    def __init__(self, config: RunConfig):
        self.config = config
        self.operations: List[RenameOperation] = []
        self.skipped: List[Dict] = []
        self.collisions: List[Dict] = []
        
    def s00_config(self) -> Dict:
        """S00: Load and validate configuration."""
        print("\n=== S00: CONFIG ===")
        
        if not self.config.run_id:
            self.config.run_id = f"RENAME_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        if not self.config.timestamp_utc:
            self.config.timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        print(f"Run ID: {self.config.run_id}")
        print(f"Timestamp: {self.config.timestamp_utc}")
        print(f"Dry Run: {self.config.dry_run}")
        print(f"Strict Registry: {self.config.strict_registry_check}")
        
        return {"status": "SUCCESS", "run_id": self.config.run_id}
    
    def s01_inventory(self) -> Dict:
        """S01: Scan filesystem and identify candidates."""
        print("\n=== S01: INVENTORY ===")
        
        candidates = []
        
        for root_str in self.config.target_roots:
            root = Path(root_str)
            if not root.exists():
                print(f"⚠ Warning: Root does not exist: {root}")
                continue
            
            print(f"Scanning: {root}")
            
            # Find all files matching pattern
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                
                filename = file_path.name
                
                # Check if matches DOC-* pattern
                if self.MATCH_REGEX.match(filename):
                    # Extract file_id
                    file_id_match = self.FILE_ID_REGEX.match(filename)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        
                        candidates.append({
                            "file_id": file_id,
                            "absolute_path": str(file_path),
                            "relative_path": str(file_path.relative_to(root)),
                            "filename": filename,
                            "extension": file_path.suffix,
                            "directory": str(file_path.parent)
                        })
        
        print(f"✓ Found {len(candidates)} candidates")
        self.inventory = candidates
        return {"status": "SUCCESS", "candidate_count": len(candidates)}
    
    def s02_plan(self) -> Dict:
        """S02: Compute proposed new filenames."""
        print("\n=== S02: PLAN ===")
        
        planned = []
        
        for candidate in self.inventory:
            old_filename = candidate["filename"]
            
            # Apply rename rule
            match = self.MATCH_REGEX.match(old_filename)
            if not match:
                self.skipped.append({
                    "file_id": candidate["file_id"],
                    "reason": "regex_match_failed",
                    "path": candidate["absolute_path"]
                })
                continue
            
            # Extract parts: P_<id> and <real_basename>
            prefix = match.group(1)  # P_01999...
            real_basename = match.group(2)  # actual name
            
            new_filename = f"{prefix}_{real_basename}"
            
            # Validate invariants
            if not new_filename.startswith("P_"):
                self.skipped.append({
                    "file_id": candidate["file_id"],
                    "reason": "invariant_violation_prefix",
                    "path": candidate["absolute_path"]
                })
                continue
            
            if Path(new_filename).suffix != candidate["extension"]:
                self.skipped.append({
                    "file_id": candidate["file_id"],
                    "reason": "invariant_violation_extension",
                    "path": candidate["absolute_path"]
                })
                continue
            
            # Extract new file_id and verify unchanged
            new_file_id_match = self.FILE_ID_REGEX.match(new_filename)
            if not new_file_id_match or new_file_id_match.group(1) != candidate["file_id"]:
                self.skipped.append({
                    "file_id": candidate["file_id"],
                    "reason": "invariant_violation_file_id_changed",
                    "path": candidate["absolute_path"]
                })
                continue
            
            # Compute new paths
            directory = Path(candidate["directory"])
            new_absolute_path = str(directory / new_filename)
            
            # Determine relative path root
            for root_str in self.config.target_roots:
                root = Path(root_str)
                old_path = Path(candidate["absolute_path"])
                if old_path.is_relative_to(root):
                    new_relative_path = str((directory / new_filename).relative_to(root))
                    break
            else:
                new_relative_path = str(directory / new_filename)
            
            planned.append({
                "file_id": candidate["file_id"],
                "old_absolute_path": candidate["absolute_path"],
                "new_absolute_path": new_absolute_path,
                "old_relative_path": candidate["relative_path"],
                "new_relative_path": new_relative_path,
                "old_filename": old_filename,
                "new_filename": new_filename,
                "directory": candidate["directory"]
            })
        
        print(f"✓ Planned {len(planned)} renames")
        print(f"⚠ Skipped {len(self.skipped)} files")
        
        self.planned = planned
        return {"status": "SUCCESS", "planned_count": len(planned), "skipped_count": len(self.skipped)}
    
    def s03_collision_detection(self) -> Dict:
        """S03: Detect and resolve collisions."""
        print("\n=== S03: COLLISION DETECTION ===")
        
        # Group by (directory, new_filename)
        groups = defaultdict(list)
        for plan in self.planned:
            key = (plan["directory"], plan["new_filename"])
            groups[key].append(plan)
        
        collision_count = 0
        resolved_operations = []
        
        for (directory, new_filename), group in groups.items():
            # Check if destination already exists
            dest_path = Path(directory) / new_filename
            dest_exists = dest_path.exists()
            
            # If multiple sources or destination exists, resolve collision
            if len(group) > 1 or dest_exists:
                collision_count += 1
                
                # Sort by old_relative_path for deterministic ordering
                sorted_group = sorted(group, key=lambda x: x["old_relative_path"])
                
                # First one gets unsuffixed name (if dest doesn't exist)
                if not dest_exists:
                    winner = sorted_group[0]
                    resolved_operations.append(RenameOperation(
                        file_id=winner["file_id"],
                        old_absolute_path=winner["old_absolute_path"],
                        new_absolute_path=winner["new_absolute_path"],
                        old_relative_path=winner["old_relative_path"],
                        new_relative_path=winner["new_relative_path"],
                        old_filename=winner["old_filename"],
                        new_filename=winner["new_filename"],
                        collision_resolved=False
                    ))
                    losers = sorted_group[1:]
                else:
                    losers = sorted_group
                
                # Others get hash suffix
                for loser in losers:
                    suffix = self._compute_collision_suffix(loser["old_relative_path"])
                    base, ext = Path(loser["new_filename"]).stem, Path(loser["new_filename"]).suffix
                    new_filename_with_suffix = f"{base}{suffix}{ext}"
                    new_absolute_with_suffix = str(Path(directory) / new_filename_with_suffix)
                    
                    # Update relative path
                    for root_str in self.config.target_roots:
                        root = Path(root_str)
                        if Path(new_absolute_with_suffix).is_relative_to(root):
                            new_relative_with_suffix = str(Path(new_absolute_with_suffix).relative_to(root))
                            break
                    else:
                        new_relative_with_suffix = new_absolute_with_suffix
                    
                    resolved_operations.append(RenameOperation(
                        file_id=loser["file_id"],
                        old_absolute_path=loser["old_absolute_path"],
                        new_absolute_path=new_absolute_with_suffix,
                        old_relative_path=loser["old_relative_path"],
                        new_relative_path=new_relative_with_suffix,
                        old_filename=loser["old_filename"],
                        new_filename=new_filename_with_suffix,
                        collision_resolved=True,
                        collision_suffix=suffix
                    ))
                    
                    self.collisions.append({
                        "file_id": loser["file_id"],
                        "old_path": loser["old_absolute_path"],
                        "new_path": new_absolute_with_suffix,
                        "suffix_applied": suffix
                    })
            else:
                # No collision
                plan = group[0]
                resolved_operations.append(RenameOperation(
                    file_id=plan["file_id"],
                    old_absolute_path=plan["old_absolute_path"],
                    new_absolute_path=plan["new_absolute_path"],
                    old_relative_path=plan["old_relative_path"],
                    new_relative_path=plan["new_relative_path"],
                    old_filename=plan["old_filename"],
                    new_filename=plan["new_filename"],
                    collision_resolved=False
                ))
        
        self.operations = resolved_operations
        
        print(f"✓ Resolved {collision_count} collisions")
        print(f"✓ Total operations: {len(self.operations)}")
        
        return {
            "status": "SUCCESS",
            "collision_count": collision_count,
            "total_operations": len(self.operations)
        }
    
    def _compute_collision_suffix(self, old_relative_path: str) -> str:
        """Compute deterministic collision suffix."""
        hash_obj = hashlib.sha256(old_relative_path.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:8].upper()
        return f"__dup{hash_hex}"
    
    def s04_emit_artifacts(self, output_dir: Path) -> Dict:
        """S04: Write planning artifacts."""
        print("\n=== S04: EMIT ARTIFACTS ===")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # RENAME_MAP.json
        rename_map = {
            "doc_type": "RENAME_MAP",
            "version": "1.0.0",
            "run_id": self.config.run_id,
            "timestamp_utc": self.config.timestamp_utc,
            "operations": [asdict(op) for op in self.operations]
        }
        
        rename_map_path = output_dir / "RENAME_MAP.json"
        with open(rename_map_path, 'w', encoding='utf-8') as f:
            json.dump(rename_map, f, indent=2)
        print(f"✓ Written: {rename_map_path}")
        
        # PLAN_REPORT.md
        report_lines = [
            "# DOC-* Token Removal Plan",
            f"**Run ID:** {self.config.run_id}",
            f"**Generated:** {self.config.timestamp_utc}",
            "",
            "## Summary",
            f"- **Matched:** {len(self.operations)}",
            f"- **Skipped:** {len(self.skipped)}",
            f"- **Collisions:** {len(self.collisions)}",
            "",
            "## Preview (First 50 Operations)",
            "",
            "| File ID | Old Filename | New Filename | Collision |",
            "|---------|--------------|--------------|-----------|"
        ]
        
        for op in self.operations[:50]:
            collision_mark = "✓" if op.collision_resolved else ""
            report_lines.append(
                f"| {op.file_id} | `{op.old_filename}` | `{op.new_filename}` | {collision_mark} |"
            )
        
        if len(self.operations) > 50:
            report_lines.append(f"\n*...and {len(self.operations) - 50} more operations*")
        
        report_lines.extend([
            "",
            "## Proceed Gate",
            "",
            "To proceed with execution, create a file named **PROCEED.txt** containing:",
            "```",
            "PROCEED_RENAME=YES",
            "```",
            "",
            f"Then run: `python {Path(__file__).name} --execute`"
        ])
        
        plan_report_path = output_dir / "PLAN_REPORT.md"
        with open(plan_report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"✓ Written: {plan_report_path}")
        
        # before_manifest.csv
        before_manifest_path = output_dir / "EVIDENCE_BUNDLE" / "before_manifest.csv"
        before_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(before_manifest_path, 'w', encoding='utf-8') as f:
            f.write("file_id,absolute_path,size_bytes,mtime\n")
            for op in self.operations:
                path = Path(op.old_absolute_path)
                if path.exists():
                    stat = path.stat()
                    f.write(f"{op.file_id},{op.old_absolute_path},{stat.st_size},{stat.st_mtime}\n")
        print(f"✓ Written: {before_manifest_path}")
        
        return {
            "status": "SUCCESS",
            "artifacts": [
                str(rename_map_path),
                str(plan_report_path),
                str(before_manifest_path)
            ]
        }
    
    def s05_execute_renames(self, output_dir: Path) -> Dict:
        """S05: Execute rename operations."""
        print("\n=== S05: EXECUTE RENAMES ===")
        
        if self.config.dry_run:
            print("⚠ DRY RUN MODE - No actual renames")
            return {"status": "SUCCESS", "mode": "dry_run", "operations_executed": 0}
        
        # Check proceed gate
        proceed_file = output_dir / "PROCEED.txt"
        if not proceed_file.exists():
            print("✗ PROCEED.txt not found. Cannot execute.")
            print(f"   Create {proceed_file} containing: PROCEED_RENAME=YES")
            return {"status": "BLOCKED", "reason": "no_proceed_gate"}
        
        # Verify proceed gate content
        proceed_content = proceed_file.read_text().strip()
        if proceed_content != "PROCEED_RENAME=YES":
            print(f"✗ Invalid PROCEED.txt content: {proceed_content}")
            print("   Expected: PROCEED_RENAME=YES")
            return {"status": "BLOCKED", "reason": "invalid_proceed_gate"}
        
        print("✓ Proceed gate verified")
        
        # Prepare logging
        rename_log_path = output_dir / "EVIDENCE_BUNDLE" / "rename_log.jsonl"
        rollback_log_path = output_dir / "EVIDENCE_BUNDLE" / "rollback_log.jsonl"
        
        executed = []
        failed = []
        
        # Sort operations for deterministic order
        sorted_ops = sorted(self.operations, key=lambda op: op.old_relative_path)
        
        for i, op in enumerate(sorted_ops, 1):
            old_path = Path(op.old_absolute_path)
            new_path = Path(op.new_absolute_path)
            
            print(f"[{i}/{len(sorted_ops)}] {op.old_filename} -> {op.new_filename}")
            
            # Verify source exists
            if not old_path.exists():
                error = f"Source does not exist: {old_path}"
                print(f"  ✗ {error}")
                failed.append((op, error))
                op.error = error
                
                # Log failure
                with open(rename_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operation": "rename",
                        "status": "FAILED",
                        "error": error,
                        "file_id": op.file_id,
                        "old_path": str(old_path),
                        "new_path": str(new_path)
                    }) + '\n')
                
                # Initiate rollback
                print("\n⚠ INITIATING ROLLBACK")
                self._rollback_renames(executed, rollback_log_path)
                return {
                    "status": "FAILED",
                    "reason": "source_not_found",
                    "operations_executed": len(executed),
                    "operations_failed": len(failed)
                }
            
            # Verify destination doesn't exist
            if new_path.exists():
                error = f"Destination already exists: {new_path}"
                print(f"  ✗ {error}")
                failed.append((op, error))
                op.error = error
                
                # Log failure
                with open(rename_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operation": "rename",
                        "status": "FAILED",
                        "error": error,
                        "file_id": op.file_id,
                        "old_path": str(old_path),
                        "new_path": str(new_path)
                    }) + '\n')
                
                # Initiate rollback
                print("\n⚠ INITIATING ROLLBACK")
                self._rollback_renames(executed, rollback_log_path)
                return {
                    "status": "FAILED",
                    "reason": "destination_exists",
                    "operations_executed": len(executed),
                    "operations_failed": len(failed)
                }
            
            # Perform rename (atomic within same directory)
            try:
                old_path.rename(new_path)
                
                # Verify
                if not new_path.exists() or old_path.exists():
                    raise RuntimeError("Rename verification failed")
                
                executed.append((op, old_path, new_path))
                print(f"  ✓ Success")
                
                # Log success
                with open(rename_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operation": "rename",
                        "status": "SUCCESS",
                        "file_id": op.file_id,
                        "old_path": str(old_path),
                        "new_path": str(new_path)
                    }) + '\n')
                
            except Exception as e:
                error = f"Rename failed: {e}"
                print(f"  ✗ {error}")
                failed.append((op, error))
                op.error = error
                
                # Log failure
                with open(rename_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operation": "rename",
                        "status": "FAILED",
                        "error": str(e),
                        "file_id": op.file_id,
                        "old_path": str(old_path),
                        "new_path": str(new_path)
                    }) + '\n')
                
                # Initiate rollback
                print("\n⚠ INITIATING ROLLBACK")
                self._rollback_renames(executed, rollback_log_path)
                return {
                    "status": "FAILED",
                    "reason": "rename_exception",
                    "error": str(e),
                    "operations_executed": len(executed),
                    "operations_failed": len(failed)
                }
        
        print(f"\n✓ All {len(executed)} renames completed successfully")
        
        return {
            "status": "SUCCESS",
            "operations_executed": len(executed),
            "operations_failed": len(failed)
        }
    
    def _rollback_renames(self, executed: List[Tuple], rollback_log_path: Path):
        """Rollback executed renames."""
        print(f"Rolling back {len(executed)} operations...")
        
        for op, old_path, new_path in reversed(executed):
            try:
                if new_path.exists() and not old_path.exists():
                    new_path.rename(old_path)
                    print(f"  ↩ Rolled back: {op.file_id}")
                    
                    with open(rollback_log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "operation": "rollback",
                            "status": "SUCCESS",
                            "file_id": op.file_id,
                            "restored_path": str(old_path)
                        }) + '\n')
            except Exception as e:
                print(f"  ✗ Rollback failed for {op.file_id}: {e}")
                
                with open(rollback_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "operation": "rollback",
                        "status": "FAILED",
                        "error": str(e),
                        "file_id": op.file_id
                    }) + '\n')
        
        print("✓ Rollback complete")
    
    def s06_post_verify(self, output_dir: Path) -> Dict:
        """S06: Post-execution verification."""
        print("\n=== S06: POST VERIFY ===")
        
        # Write after_manifest
        after_manifest_path = output_dir / "EVIDENCE_BUNDLE" / "after_manifest.csv"
        
        with open(after_manifest_path, 'w', encoding='utf-8') as f:
            f.write("file_id,absolute_path,size_bytes,mtime\n")
            for op in self.operations:
                if not op.error:
                    path = Path(op.new_absolute_path)
                    if path.exists():
                        stat = path.stat()
                        f.write(f"{op.file_id},{op.new_absolute_path},{stat.st_size},{stat.st_mtime}\n")
        
        print(f"✓ Written: {after_manifest_path}")
        
        # Verify file_ids match filenames
        mismatches = []
        for op in self.operations:
            if not op.error:
                new_filename = op.new_filename
                file_id_match = self.FILE_ID_REGEX.match(new_filename)
                if not file_id_match or file_id_match.group(1) != op.file_id:
                    mismatches.append(op.file_id)
        
        if mismatches:
            print(f"⚠ Warning: {len(mismatches)} file_id mismatches")
            return {"status": "WARNING", "mismatches": len(mismatches)}
        
        print("✓ All file_ids match filenames")
        return {"status": "SUCCESS", "verified_count": len(self.operations)}
    
    def s08_finalize(self, output_dir: Path, results: Dict) -> Dict:
        """S08: Write run manifest."""
        print("\n=== S08: FINALIZE ===")
        
        manifest = {
            "doc_type": "RUN_MANIFEST",
            "version": "1.0.0",
            "run_id": self.config.run_id,
            "timestamp_utc": self.config.timestamp_utc,
            "tool_version": "1.0.0",
            "inputs": {
                "target_roots": self.config.target_roots,
                "dry_run": self.config.dry_run,
                "strict_registry_check": self.config.strict_registry_check
            },
            "outputs": {
                "rename_map": str(output_dir / "RENAME_MAP.json"),
                "plan_report": str(output_dir / "PLAN_REPORT.md"),
                "evidence_bundle": str(output_dir / "EVIDENCE_BUNDLE")
            },
            "results": results,
            "success": results.get("s05_execute", {}).get("status") == "SUCCESS"
        }
        
        manifest_path = output_dir / "RUN_MANIFEST.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✓ Written: {manifest_path}")
        
        return {"status": "SUCCESS", "manifest_path": str(manifest_path)}

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove DOC-* tokens from filenames")
    parser.add_argument("--execute", action="store_true", help="Execute renames (default: plan only)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--strict-registry", action="store_true", help="Require registry validation")
    args = parser.parse_args()
    
    # Configure
    config = RunConfig(
        target_roots=["C:\\Users\\richg\\Gov_Reg\\01260207201000001250_REGISTRY"],
        dry_run=args.dry_run,
        strict_registry_check=args.strict_registry
    )
    
    remover = DOCTokenRemover(config)
    output_dir = Path("C:\\Users\\richg\\Gov_Reg\\01260207201000001250_REGISTRY\\RENAME_OUTPUT")
    
    # Run pipeline stages
    try:
        results = {}
        
        results["s00_config"] = remover.s00_config()
        results["s01_inventory"] = remover.s01_inventory()
        results["s02_plan"] = remover.s02_plan()
        results["s03_collision"] = remover.s03_collision_detection()
        results["s04_artifacts"] = remover.s04_emit_artifacts(output_dir)
        
        if args.execute:
            results["s05_execute"] = remover.s05_execute_renames(output_dir)
            
            if results["s05_execute"]["status"] == "SUCCESS":
                results["s06_verify"] = remover.s06_post_verify(output_dir)
                results["s08_finalize"] = remover.s08_finalize(output_dir, results)
                
                print("\n" + "="*80)
                print("✓ RENAME COMPLETE")
                print("="*80)
                print(f"\nOperations executed: {results['s05_execute']['operations_executed']}")
                print(f"Evidence bundle: {output_dir / 'EVIDENCE_BUNDLE'}")
                
                return 0
            else:
                results["s08_finalize"] = remover.s08_finalize(output_dir, results)
                
                print("\n" + "="*80)
                print("✗ RENAME FAILED")
                print("="*80)
                print(f"\nStatus: {results['s05_execute']['status']}")
                print(f"Reason: {results['s05_execute'].get('reason', 'unknown')}")
                
                return 1
        else:
            # Planning only
            print("\n" + "="*80)
            print("✓ PLANNING COMPLETE")
            print("="*80)
            print(f"\nReview artifacts in: {output_dir}")
            print(f"Operations planned: {len(remover.operations)}")
            print(f"\nTo proceed:")
            print(f"  1. Create {output_dir / 'PROCEED.txt'} containing: PROCEED_RENAME=YES")
            print(f"  2. Run: python {Path(__file__).name} --execute")
            
            return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
