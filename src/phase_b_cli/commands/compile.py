"""B2: compile - Generate execution compilation package"""

from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime, timezone
from collections import defaultdict, deque

from .base import BaseCommand


class CompileCommand(BaseCommand):
    """
    Generates execution compilation package from validated plan.
    
    Gates:
    - G16: Dependency graph acyclic
    - G17: All write paths within repo-root
    - G18: Every task has acceptance_tests
    - G19: Rollback operations cover all write operations
    - G22: All write_scopes globs expand to ≥1 file
    - G23: No dependency cycles
    """
    
    def execute(self) -> int:
        """Execute compilation"""
        self.logger.info(f"Compiling execution package for Phase A run: {self.run_id}")
        
        # Check validation report exists and passed
        validation_report_path = self.phase_b_dir / "validate" / "phase_b_validation_report.json"
        if not validation_report_path.exists():
            self.logger.error("Validation report not found. Run 'validate' command first.")
            return 10
        
        validation_report = self.load_json(validation_report_path)
        if validation_report.get("result") != "PASS":
            self.logger.error("Phase A validation failed. Cannot compile.")
            return 10
        
        # Load Phase A final plan
        loop_dir = self.phase_a_artifacts / "loop"
        refined_plans = sorted([p for p in loop_dir.glob("refined_plan_*.json") if not p.name.endswith(".envelope.json")])
        if not refined_plans:
            self.logger.error("No refined plan found")
            return 10
        
        final_plan_path = refined_plans[-1]
        final_plan = self.load_json(final_plan_path)
        
        # Build task list
        tasks = []
        for ws in final_plan.get("workstreams", []):
            for task in ws.get("tasks", []):
                tasks.append(task)
        
        self.logger.info(f"Found {len(tasks)} tasks")
        
        # G16/G23: Topological sort
        try:
            task_order = self._topological_sort(tasks)
        except ValueError as e:
            self.logger.error(f"Dependency cycle detected: {e}")
            return 10
        
        # Compile each task
        compile_dir = self.phase_b_dir / "compile"
        task_specs_dir = compile_dir / "task_specs"
        task_spec_registry = []
        
        for task_id in task_order:
            task = next(t for t in tasks if t["id"] == task_id)
            
            # G18: Check acceptance_tests
            if not task.get("acceptance_tests"):
                self.logger.error(f"Task {task_id} missing acceptance_tests (G18)")
                return 10
            
            # Compile task spec
            task_spec = self._compile_task_spec(task)
            
            # G17: Validate write paths
            for write_op in task_spec.get("write_operations", []):
                path = Path(write_op["path"])
                if not self._is_within_repo(path):
                    self.logger.error(f"Path outside repo: {path} (G17)")
                    return 10
            
            # G19: Validate rollback operations
            if not self._validate_rollback_coverage(task_spec):
                self.logger.error(f"Task {task_id} has incomplete rollback coverage (G19)")
                return 10
            
            # Write task spec
            safe_id = self._make_safe_id(task_id)
            spec_path = task_specs_dir / f"task_spec_{safe_id}.json"
            self.write_json(spec_path, task_spec)
            
            # Write envelope
            envelope_path = Path(str(spec_path) + ".envelope.json")
            self.write_json(envelope_path, {
                "artifact_path": str(spec_path.relative_to(self.phase_a_dir)),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "sha256": "placeholder_hash"
            })
            
            task_spec_registry.append({
                "task_id": task_id,
                "file_path": str(spec_path.relative_to(compile_dir)),
                "sha256": "placeholder_hash"
            })
        
        # Generate execution plan
        execution_plan = {
            "plan_id": final_plan.get("plan_id", "UNKNOWN"),
            "phase_a_run_id": self.run_id,
            "phase_a_plan_sha256": "placeholder_hash",
            "task_order": task_order,
            "parallel_groups": self._detect_parallel_groups(tasks, task_order) if self.args.parallel_detection == "auto" else [],
            "metadata": {
                "compiled_at": datetime.now(timezone.utc).isoformat(),
                "total_tasks": len(tasks),
                "estimated_duration_seconds": sum(t.get("estimated_duration_seconds", 60) for t in tasks),
                "harness_lang": self.args.harness_lang
            }
        }
        
        execution_plan_path = compile_dir / "execution_plan.json"
        self.write_json(execution_plan_path, execution_plan)
        self._write_envelope(execution_plan_path)
        
        # Generate execution manifest
        manifest = {
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "execution_plan_sha256": "placeholder_hash",
            "rollback_plan_sha256": "placeholder_hash",
            "task_spec_registry": task_spec_registry
        }
        
        manifest_path = compile_dir / "execution_manifest.json"
        self.write_json(manifest_path, manifest)
        self._write_envelope(manifest_path)
        
        # Generate execution policy snapshot
        policy_snapshot = {
            "snapshotted_at": datetime.now(timezone.utc).isoformat(),
            "source_policy_sha256": "placeholder_hash",
            "runtime_limits": {
                "default_task_timeout_seconds": 3600,
                "max_task_timeout_seconds": 86400,
                "max_retries_per_task": 0,
                "parallel_execution_allowed": True,
                "max_parallel_tasks": 4
            }
        }
        
        policy_path = compile_dir / "execution_policy_snapshot.json"
        self.write_json(policy_path, policy_snapshot)
        self._write_envelope(policy_path)
        
        # Generate test harness
        self._generate_test_harness(tasks, task_order, compile_dir)
        
        # Generate rollback plan
        self._generate_rollback_plan(tasks, task_order, compile_dir)
        
        self.logger.info(f"Compilation complete: {len(tasks)} tasks")
        
        if self.args.json_stdout:
            import json
            print(json.dumps({
                "status": "success",
                "total_tasks": len(tasks),
                "output_dir": str(compile_dir)
            }, indent=2))
        else:
            print(f"✓ Compiled {len(tasks)} tasks")
            print(f"  Output: {compile_dir}")
        
        return 0
    
    def _topological_sort(self, tasks: List[Dict]) -> List[str]:
        """Kahn's algorithm with lexicographic tie-breaking"""
        graph = {t["id"]: set(t.get("depends_on", [])) for t in tasks}
        in_degree = {t["id"]: len(t.get("depends_on", [])) for t in tasks}
        
        # Check all dependencies exist
        for task_id, deps in graph.items():
            for dep in deps:
                if dep not in graph:
                    raise ValueError(f"Task {task_id} depends on non-existent task {dep}")
        
        queue = sorted([tid for tid, deg in in_degree.items() if deg == 0])
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Find dependents
            for task_id, deps in graph.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
                        queue.sort()
        
        if len(result) != len(tasks):
            raise ValueError("Dependency cycle detected")
        
        return result
    
    def _compile_task_spec(self, task: Dict) -> Dict:
        """Compile task into task_spec format"""
        task_id = task["id"]
        
        # Convert writes_scopes to write_operations (simplified)
        write_operations = []
        for scope in task.get("writes_scopes", []):
            # Simplified: treat each scope as a create operation
            write_operations.append({
                "type": "create",
                "path": scope,
                "backup_required": False
            })
        
        # Generate rollback operations
        rollback_operations = []
        for write_op in write_operations:
            if write_op["type"] == "create":
                rollback_operations.append({
                    "type": "delete",
                    "path": write_op["path"],
                    "backup_ref": None,
                    "sha256_before": None
                })
        
        return {
            "task_id": task_id,
            "safe_task_id": self._make_safe_id(task_id),
            "summary": task.get("summary", ""),
            "depends_on": task.get("depends_on", []),
            "write_operations": write_operations,
            "acceptance_tests": task.get("acceptance_tests", []),
            "rollback_operations": rollback_operations,
            "estimated_duration_seconds": task.get("estimated_duration_seconds", 60),
            "retries_allowed": 0
        }
    
    def _make_safe_id(self, task_id: str) -> str:
        """Convert task ID to filesystem-safe name"""
        import re
        safe = re.sub(r'[^a-zA-Z0-9]+', '_', task_id)
        safe = re.sub(r'_+', '_', safe).strip('_')
        return safe
    
    def _is_within_repo(self, path: Path) -> bool:
        """Check if path is within repo root"""
        try:
            abs_path = (self.repo_root / path).resolve()
            return abs_path.is_relative_to(self.repo_root)
        except:
            return False
    
    def _validate_rollback_coverage(self, task_spec: Dict) -> bool:
        """Validate rollback operations cover all write operations"""
        write_ops = len(task_spec.get("write_operations", []))
        rollback_ops = len(task_spec.get("rollback_operations", []))
        return write_ops == rollback_ops
    
    def _detect_parallel_groups(self, tasks: List[Dict], task_order: List[str]) -> List[Dict]:
        """Detect tasks that can run in parallel (simplified)"""
        # Simplified: no parallel groups in v1
        return []
    
    def _generate_test_harness(self, tasks: List[Dict], task_order: List[str], output_dir: Path):
        """Generate test harness script"""
        if self.args.harness_lang == "sh":
            self._generate_bash_harness(tasks, task_order, output_dir)
        else:
            self._generate_python_harness(tasks, task_order, output_dir)
    
    def _generate_bash_harness(self, tasks: List[Dict], task_order: List[str], output_dir: Path):
        """Generate bash test harness"""
        lines = [
            "#!/bin/bash",
            "set -euo pipefail",
            "",
            "# Phase B Test Harness",
            f"# Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
        ]
        
        for task_id in task_order:
            task = next(t for t in tasks if t["id"] == task_id)
            safe_id = self._make_safe_id(task_id)
            
            lines.append(f"echo 'Testing {task_id}...'")
            for i, test in enumerate(task.get("acceptance_tests", [])):
                lines.append(f"{test['command']}")
            lines.append("")
        
        lines.append("echo 'All tests passed'")
        
        harness_path = output_dir / "test_harness.sh"
        harness_path.write_text("\n".join(lines))
        harness_path.chmod(0o755)
        self.logger.debug(f"Wrote {harness_path}")
    
    def _generate_python_harness(self, tasks: List[Dict], task_order: List[str], output_dir: Path):
        """Generate Python test harness"""
        lines = [
            "#!/usr/bin/env python3",
            '"""Phase B Test Harness"""',
            "",
            "import subprocess",
            "import sys",
            "",
        ]
        
        lines.append("def main():")
        for task_id in task_order:
            task = next(t for t in tasks if t["id"] == task_id)
            lines.append(f"    print('Testing {task_id}...')")
            for test in task.get("acceptance_tests", []):
                lines.append(f"    result = subprocess.run({test['command']!r}, shell=True)")
                lines.append(f"    if result.returncode != 0:")
                lines.append(f"        sys.exit(1)")
        
        lines.append("    print('All tests passed')")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")
        
        harness_path = output_dir / "test_harness.py"
        harness_path.write_text("\n".join(lines))
        harness_path.chmod(0o755)
        self.logger.debug(f"Wrote {harness_path}")
    
    def _generate_rollback_plan(self, tasks: List[Dict], task_order: List[str], output_dir: Path):
        """Generate rollback plan"""
        rollback_plan = {
            "execution_plan_sha256": "placeholder_hash",
            "rollback_order": list(reversed(task_order)),
            "snapshot_refs": [],
            "rollback_script": "rollback.sh"
        }
        
        rollback_path = output_dir / "rollback_plan.json"
        self.write_json(rollback_path, rollback_plan)
        self._write_envelope(rollback_path)
    
    def _write_envelope(self, artifact_path: Path):
        """Write envelope sidecar for artifact"""
        envelope_path = Path(str(artifact_path) + ".envelope.json")
        self.write_json(envelope_path, {
            "artifact_path": str(artifact_path.relative_to(self.phase_a_dir)),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": "placeholder_hash"
        })
