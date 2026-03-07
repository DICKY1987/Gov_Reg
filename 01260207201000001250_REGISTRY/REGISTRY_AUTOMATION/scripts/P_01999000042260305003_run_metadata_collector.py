#!/usr/bin/env python3
"""
Run Metadata Collector (Week 1 Step 1.5)

Purpose:
  - Collect metadata about analysis runs
  - Track which scripts were executed
  - Record execution times, status codes
  - Generate RUN_METADATA.json for audit trail

Usage:
  python P_01999000042260305003_run_metadata_collector.py --run-id RUN_ID --action ACTION
  
Actions:
  start   - Start a new run
  script  - Record script execution
  finish  - Finish run and write metadata
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import platform
import os


class RunMetadataCollector:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.runs_file = state_dir / "ANALYSIS_RUNS.json"
        
    def load_runs(self) -> Dict[str, Any]:
        """Load existing runs data."""
        if self.runs_file.exists():
            with open(self.runs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"runs": [], "last_run_id": None}
    
    def save_runs(self, runs_data: Dict[str, Any]) -> None:
        """Save runs data."""
        with open(self.runs_file, 'w', encoding='utf-8') as f:
            json.dump(runs_data, f, indent=2, ensure_ascii=False)
    
    def start_run(self, run_id: str) -> Dict[str, Any]:
        """Start a new analysis run."""
        run_data = {
            "run_id": run_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "finished_at": None,
            "status": "running",
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "hostname": platform.node(),
                "cwd": os.getcwd(),
            },
            "scripts_executed": [],
            "files_analyzed": 0,
            "errors": [],
            "warnings": []
        }
        
        runs_data = self.load_runs()
        runs_data["runs"].append(run_data)
        runs_data["last_run_id"] = run_id
        self.save_runs(runs_data)
        
        print(f"✅ Started run: {run_id}")
        return run_data
    
    def record_script(self, run_id: str, script_name: str, file_path: str, 
                     status: str, exit_code: int, duration_ms: Optional[int] = None,
                     output_path: Optional[str] = None) -> None:
        """Record execution of a script."""
        runs_data = self.load_runs()
        
        # Find the run
        run = None
        for r in runs_data["runs"]:
            if r["run_id"] == run_id:
                run = r
                break
        
        if not run:
            print(f"❌ Error: Run {run_id} not found", file=sys.stderr)
            return
        
        script_record = {
            "script": script_name,
            "file_path": file_path,
            "executed_at": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output_path": output_path
        }
        
        run["scripts_executed"].append(script_record)
        run["files_analyzed"] += 1
        
        if status == "error":
            run["errors"].append(f"{script_name} failed on {file_path}")
        
        self.save_runs(runs_data)
        
        print(f"  ✓ Recorded: {script_name} → {file_path} [{status}]")
    
    def finish_run(self, run_id: str, final_status: str = "completed") -> Dict[str, Any]:
        """Finish an analysis run."""
        runs_data = self.load_runs()
        
        # Find the run
        run = None
        for r in runs_data["runs"]:
            if r["run_id"] == run_id:
                run = r
                break
        
        if not run:
            print(f"❌ Error: Run {run_id} not found", file=sys.stderr)
            return {}
        
        run["finished_at"] = datetime.utcnow().isoformat() + "Z"
        run["status"] = final_status
        
        # Calculate duration
        if run["started_at"] and run["finished_at"]:
            start = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(run["finished_at"].replace("Z", "+00:00"))
            duration = (end - start).total_seconds()
            run["duration_seconds"] = duration
        
        # Summary stats
        run["summary"] = {
            "total_files": run["files_analyzed"],
            "scripts_executed": len(run["scripts_executed"]),
            "errors": len(run["errors"]),
            "warnings": len(run["warnings"])
        }
        
        self.save_runs(runs_data)
        
        # Write individual run file
        run_file = self.state_dir / f"RUN_{run_id}.json"
        with open(run_file, 'w', encoding='utf-8') as f:
            json.dump(run, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Run {run_id} finished: {final_status}")
        print(f"   Files analyzed: {run['files_analyzed']}")
        print(f"   Scripts executed: {len(run['scripts_executed'])}")
        print(f"   Errors: {len(run['errors'])}")
        print(f"   Run file: {run_file}")
        
        return run
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run data."""
        runs_data = self.load_runs()
        for run in runs_data["runs"]:
            if run["run_id"] == run_id:
                return run
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Metadata Collector')
    parser.add_argument('--run-id', required=True, help='Run ID')
    parser.add_argument('--action', required=True, 
                       choices=['start', 'script', 'finish'],
                       help='Action to perform')
    parser.add_argument('--state-dir', 
                       default='.state/analysis_runs',
                       help='State directory')
    
    # For 'script' action
    parser.add_argument('--script-name', help='Script name')
    parser.add_argument('--file-path', help='File analyzed')
    parser.add_argument('--status', help='Status (success/error)')
    parser.add_argument('--exit-code', type=int, default=0, help='Exit code')
    parser.add_argument('--duration-ms', type=int, help='Duration in ms')
    parser.add_argument('--output-path', help='Output file path')
    
    # For 'finish' action
    parser.add_argument('--final-status', default='completed', help='Final status')
    
    args = parser.parse_args()
    
    # Resolve state dir relative to script location
    script_dir = Path(__file__).parent
    state_dir = (script_dir / args.state_dir).resolve()
    
    collector = RunMetadataCollector(state_dir)
    
    if args.action == 'start':
        collector.start_run(args.run_id)
    
    elif args.action == 'script':
        if not all([args.script_name, args.file_path, args.status]):
            print("❌ Error: --script-name, --file-path, and --status required for 'script' action",
                  file=sys.stderr)
            sys.exit(1)
        
        collector.record_script(
            args.run_id,
            args.script_name,
            args.file_path,
            args.status,
            args.exit_code,
            args.duration_ms,
            args.output_path
        )
    
    elif args.action == 'finish':
        collector.finish_run(args.run_id, args.final_status)


if __name__ == "__main__":
    main()
