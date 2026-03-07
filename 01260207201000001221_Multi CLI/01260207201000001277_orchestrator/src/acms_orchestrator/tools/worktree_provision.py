#!/usr/bin/env python3
"""
LangGraph adapter tool for worktree provisioning.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any


class WorktreeProvisionTool:
    """LangGraph tool adapter for worktree provisioning"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.parent / "01260207201000001276_scripts"
    
    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provision isolated worktrees.
        
        Args:
            request: ToolRunRequestV1 with parameters:
                - run_id: Unique run identifier
                - plan_path: Path to plan JSON file
                - parallel_groups_path: Path to parallel groups JSON
                - base_commit: Base commit reference (default: HEAD)
                - max_worktrees: Maximum total worktrees (default: 8)
        
        Returns:
            ToolRunResultV1 with:
                - worktree_map_path: Path to worktree map JSON
                - worktree_map: Dict mapping workstream_id to worktree_path
                - success: Boolean indicating success
        """
        try:
            # Extract parameters
            run_id = request['parameters']['run_id']
            plan_path = Path(request['parameters']['plan_path'])
            parallel_groups_path = Path(request['parameters'].get('parallel_groups_path'))
            base_commit = request['parameters'].get('base_commit', 'HEAD')
            max_worktrees = request['parameters'].get('max_worktrees', 8)
            output_dir = Path(request['parameters'].get('output_dir', plan_path.parent))
            
            # Run provision_worktrees.py
            script_path = self.script_dir / "provision_worktrees.py"
            
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--run-id", run_id,
                    "--plan", str(plan_path),
                    "--parallel-groups", str(parallel_groups_path),
                    "--base-commit", base_commit,
                    "--output-dir", str(output_dir),
                    "--max-worktrees", str(max_worktrees)
                ],
                capture_output=True,
                text=True
            )
            
            # Prepare result
            if result.returncode == 0:
                worktree_map_path = output_dir / "artifacts" / "worktrees" / "worktree_map.json"
                
                # Load worktree map
                with open(worktree_map_path, 'r', encoding='utf-8') as f:
                    worktree_data = json.load(f)
                
                return {
                    "success": True,
                    "result": {
                        "worktree_map_path": str(worktree_map_path),
                        "worktree_map": worktree_data['worktree_map'],
                        "total_worktrees": worktree_data['total_worktrees'],
                        "base_commit": worktree_data['base_commit']
                    },
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "success": False,
                    "error": f"Worktree provisioning failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during worktree provisioning: {str(e)}"
            }


def main():
    """CLI entry point for tool"""
    if len(sys.argv) < 2:
        print("Usage: worktree_provision.py <request_json>", file=sys.stderr)
        sys.exit(1)
    
    request = json.loads(sys.argv[1])
    tool = WorktreeProvisionTool()
    result = tool.run(request)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
