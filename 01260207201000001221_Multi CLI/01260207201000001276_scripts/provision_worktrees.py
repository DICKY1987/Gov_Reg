#!/usr/bin/env python3
"""
Provision isolated git worktrees for parallel workstream execution.
Gate: GATE-PWE-005 (worktree provision)
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import shutil


class WorktreeProvisioner:
    def __init__(self, repo_root: Path, max_total_worktrees: int = 8):
        self.repo_root = repo_root
        self.max_total_worktrees = max_total_worktrees
        
    def get_base_commit(self, ref: str = "HEAD") -> str:
        """Get commit SHA for base reference"""
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "rev-parse", ref],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    def check_clean_worktree(self, commit_sha: str) -> bool:
        """Verify base commit is clean (no uncommitted changes)"""
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "diff-index", "--quiet", commit_sha],
            capture_output=True
        )
        return result.returncode == 0
    
    def create_worktree(self, workstream_id: str, run_id: str, base_commit: str, worktrees_dir: Path) -> Path:
        """Create isolated git worktree for workstream"""
        worktree_path = worktrees_dir / run_id / workstream_id
        
        # Ensure parent directory exists
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create detached worktree at base commit
        subprocess.run(
            [
                "git", "-C", str(self.repo_root),
                "worktree", "add",
                "--detach",
                str(worktree_path),
                base_commit
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        return worktree_path
    
    def cleanup_worktree(self, worktree_path: Path, max_retries: int = 3):
        """Remove worktree with retry logic for Windows file locks"""
        import time
        
        for attempt in range(max_retries):
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return
            except subprocess.CalledProcessError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise
    
    def list_worktrees(self) -> List[str]:
        """List all existing worktrees"""
        result = subprocess.run(
            ["git", "-C", str(self.repo_root), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        
        worktrees = []
        for line in result.stdout.split('\n'):
            if line.startswith('worktree '):
                worktrees.append(line.split(' ', 1)[1])
        
        return worktrees
    
    def provision_parallel_group(
        self,
        parallel_group: List[str],
        run_id: str,
        base_commit: str,
        worktrees_dir: Path
    ) -> Dict[str, str]:
        """Provision worktrees for a parallel execution group"""
        worktree_map = {}
        
        # Check worktree count limit
        existing_worktrees = self.list_worktrees()
        if len(existing_worktrees) + len(parallel_group) > self.max_total_worktrees:
            raise ValueError(
                f"Would exceed max_total_worktrees limit: "
                f"{len(existing_worktrees)} existing + {len(parallel_group)} new > {self.max_total_worktrees}"
            )
        
        # Verify base commit is clean
        if not self.check_clean_worktree(base_commit):
            raise ValueError(f"Base commit {base_commit} has uncommitted changes")
        
        # Create worktrees
        for workstream_id in parallel_group:
            worktree_path = self.create_worktree(workstream_id, run_id, base_commit, worktrees_dir)
            worktree_map[workstream_id] = str(worktree_path)
        
        return worktree_map
    
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
        description="Provision isolated worktrees for parallel workstreams"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique run identifier"
    )
    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="Path to plan JSON file"
    )
    parser.add_argument(
        "--parallel-groups",
        type=Path,
        default=None,
        help="Path to parallel_groups.json (default: auto-detect from plan dir)"
    )
    parser.add_argument(
        "--base-commit",
        default="HEAD",
        help="Base commit reference (default: HEAD)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for artifacts"
    )
    parser.add_argument(
        "--max-worktrees",
        type=int,
        default=8,
        help="Maximum total worktrees"
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
    
    # Default output directory
    if args.output_dir is None:
        args.output_dir = args.plan.parent
    
    # Auto-detect parallel groups file
    if args.parallel_groups is None:
        args.parallel_groups = args.output_dir / "artifacts" / "conflict_graph" / "parallel_groups.json"
    
    try:
        # Load parallel groups
        with open(args.parallel_groups, 'r', encoding='utf-8') as f:
            groups_data = json.load(f)
        
        parallel_groups = groups_data['parallel_groups']
        
        # Initialize provisioner
        provisioner = WorktreeProvisioner(args.repo_root, args.max_worktrees)
        
        # Get base commit SHA
        base_commit = provisioner.get_base_commit(args.base_commit)
        
        # Provision all parallel groups
        worktrees_dir = args.output_dir / "worktrees"
        all_worktree_map = {}
        
        for group_idx, parallel_group in enumerate(parallel_groups):
            group_map = provisioner.provision_parallel_group(
                parallel_group,
                args.run_id,
                base_commit,
                worktrees_dir
            )
            all_worktree_map.update(group_map)
        
        # Write worktree map artifact
        artifact_dir = args.output_dir / "artifacts" / "worktrees"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        worktree_map_file = artifact_dir / "worktree_map.json"
        with open(worktree_map_file, 'w', encoding='utf-8') as f:
            json.dump({
                "run_id": args.run_id,
                "base_commit": base_commit,
                "worktree_map": all_worktree_map,
                "total_worktrees": len(all_worktree_map),
                "created_at": datetime.utcnow().isoformat() + "Z"
            }, f, indent=2)
        
        # Write gate result
        provisioner.write_gate_result("GATE-PWE-005", True, None, args.output_dir)
        
        print(f"✓ GATE-PWE-005: Provisioned {len(all_worktree_map)} worktrees")
        print(f"  Run ID: {args.run_id}")
        print(f"  Base commit: {base_commit}")
        for ws_id, wt_path in all_worktree_map.items():
            print(f"  {ws_id} → {wt_path}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        
        # Write failure gate result
        provisioner = WorktreeProvisioner(args.repo_root, args.max_worktrees)
        provisioner.write_gate_result("GATE-PWE-005", False, str(e), args.output_dir)
        
        sys.exit(1)


if __name__ == "__main__":
    main()
