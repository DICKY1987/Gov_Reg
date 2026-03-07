#!/usr/bin/env python3
"""
LangGraph adapter tool for dispatching parallel workstream workers.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ProcessPoolExecutor, as_completed


class DispatchWorkersTool:
    """LangGraph tool adapter for parallel workstream execution dispatch"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.parent / "01260207201000001276_scripts"
    
    def execute_workstream(
        self,
        workstream_id: str,
        worktree_path: str,
        manifest_path: Path,
        output_dir: Path
    ) -> Dict[str, Any]:
        """Execute a single workstream in its isolated worktree"""
        try:
            # Here would be the actual workstream execution logic
            # For now, just create a placeholder report
            
            report = {
                "workstream_id": workstream_id,
                "worktree_path": worktree_path,
                "exit_code": 0,
                "touched_files": [],
                "patches": [],
                "evidence_path": str(output_dir / "evidence" / "workstreams" / workstream_id),
                "execution_metadata": {
                    "start_time": "2026-03-07T00:00:00Z",
                    "end_time": "2026-03-07T00:01:00Z",
                    "duration_seconds": 60
                }
            }
            
            return {
                "success": True,
                "workstream_id": workstream_id,
                "report": report
            }
        
        except Exception as e:
            return {
                "success": False,
                "workstream_id": workstream_id,
                "error": str(e)
            }
    
    def dispatch_parallel_group(
        self,
        parallel_group: List[str],
        worktree_map: Dict[str, str],
        manifests_dir: Path,
        output_dir: Path,
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """Dispatch parallel execution of workstream group"""
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for workstream_id in parallel_group:
                worktree_path = worktree_map.get(workstream_id)
                manifest_path = manifests_dir / f"{workstream_id}.json"
                
                future = executor.submit(
                    self.execute_workstream,
                    workstream_id,
                    worktree_path,
                    manifest_path,
                    output_dir
                )
                futures[future] = workstream_id
            
            for future in as_completed(futures):
                workstream_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "workstream_id": workstream_id,
                        "error": str(e)
                    })
        
        return results
    
    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch parallel workstream workers.
        
        Args:
            request: ToolRunRequestV1 with parameters:
                - parallel_groups_path: Path to parallel groups JSON
                - worktree_map_path: Path to worktree map JSON
                - manifests_dir: Directory containing write manifests
                - output_dir: Output directory for results
                - max_workers: Maximum parallel workers (default: 4)
        
        Returns:
            ToolRunResultV1 with:
                - workstream_results: List of execution results
                - success: Boolean indicating success
        """
        try:
            # Extract parameters
            parallel_groups_path = Path(request['parameters']['parallel_groups_path'])
            worktree_map_path = Path(request['parameters']['worktree_map_path'])
            manifests_dir = Path(request['parameters']['manifests_dir'])
            output_dir = Path(request['parameters']['output_dir'])
            max_workers = request['parameters'].get('max_workers', 4)
            
            # Load parallel groups
            with open(parallel_groups_path, 'r', encoding='utf-8') as f:
                groups_data = json.load(f)
            
            # Load worktree map
            with open(worktree_map_path, 'r', encoding='utf-8') as f:
                worktree_data = json.load(f)
            
            parallel_groups = groups_data['parallel_groups']
            worktree_map = worktree_data['worktree_map']
            
            # Dispatch all parallel groups
            all_results = []
            for group_idx, parallel_group in enumerate(parallel_groups):
                group_results = self.dispatch_parallel_group(
                    parallel_group,
                    worktree_map,
                    manifests_dir,
                    output_dir,
                    max_workers
                )
                all_results.extend(group_results)
            
            # Check for failures
            failures = [r for r in all_results if not r['success']]
            
            return {
                "success": len(failures) == 0,
                "result": {
                    "workstream_results": all_results,
                    "total_workstreams": len(all_results),
                    "successful": len(all_results) - len(failures),
                    "failed": len(failures)
                },
                "error": None if len(failures) == 0 else f"{len(failures)} workstreams failed"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during worker dispatch: {str(e)}"
            }


def main():
    """CLI entry point for tool"""
    if len(sys.argv) < 2:
        print("Usage: dispatch_workers.py <request_json>", file=sys.stderr)
        sys.exit(1)
    
    request = json.loads(sys.argv[1])
    tool = DispatchWorkersTool()
    result = tool.run(request)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
