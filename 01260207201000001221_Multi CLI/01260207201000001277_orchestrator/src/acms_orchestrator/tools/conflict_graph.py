#!/usr/bin/env python3
"""
LangGraph adapter tool for conflict graph computation.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any


class ConflictGraphTool:
    """LangGraph tool adapter for conflict graph computation"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.parent / "01260207201000001276_scripts"
    
    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run conflict graph computation.
        
        Args:
            request: ToolRunRequestV1 with parameters:
                - plan_path: Path to plan JSON file
                - output_dir: Output directory for artifacts
                - max_parallel: Maximum parallel workstreams (default: 4)
        
        Returns:
            ToolRunResultV1 with:
                - conflict_graph_path: Path to conflict graph JSON
                - parallel_groups_path: Path to parallel groups JSON
                - success: Boolean indicating success
        """
        try:
            # Extract parameters
            plan_path = Path(request['parameters']['plan_path'])
            output_dir = Path(request['parameters'].get('output_dir', plan_path.parent))
            max_parallel = request['parameters'].get('max_parallel', 4)
            
            # Run compute_conflict_graph.py
            script_path = self.script_dir / "compute_conflict_graph.py"
            
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--plan", str(plan_path),
                    "--output-dir", str(output_dir),
                    "--max-parallel", str(max_parallel)
                ],
                capture_output=True,
                text=True
            )
            
            # Prepare result
            if result.returncode == 0:
                conflict_graph_path = output_dir / "artifacts" / "conflict_graph" / "conflict_graph.json"
                parallel_groups_path = output_dir / "artifacts" / "conflict_graph" / "parallel_groups.json"
                
                # Load conflict graph for metadata
                with open(conflict_graph_path, 'r', encoding='utf-8') as f:
                    conflict_graph = json.load(f)
                
                return {
                    "success": True,
                    "result": {
                        "conflict_graph_path": str(conflict_graph_path),
                        "parallel_groups_path": str(parallel_groups_path),
                        "total_workstreams": conflict_graph['analysis_metadata']['total_workstreams'],
                        "total_conflicts": conflict_graph['analysis_metadata']['total_conflicts'],
                        "max_parallelism": conflict_graph['analysis_metadata']['max_parallelism']
                    },
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "success": False,
                    "error": f"Conflict graph computation failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during conflict graph computation: {str(e)}"
            }


def main():
    """CLI entry point for tool"""
    if len(sys.argv) < 2:
        print("Usage: conflict_graph.py <request_json>", file=sys.stderr)
        sys.exit(1)
    
    request = json.loads(sys.argv[1])
    tool = ConflictGraphTool()
    result = tool.run(request)
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
