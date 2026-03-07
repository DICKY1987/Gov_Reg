"""
Result Validation Pipeline

Validates execution results to ensure tasks completed correctly and
produced expected outputs. Detects hallucinated successes and incomplete work.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import re


@dataclass
class ValidationResult:
    """Result of validating an execution"""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class ResultValidator:
    """Validates execution results"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
    
    def validate_task_result(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a single task's execution result
        
        Checks:
        1. Exit code is 0 if marked successful
        2. Expected files were created/modified
        3. No error patterns in output
        4. Output contains success indicators
        """
        issues = []
        warnings = []
        confidence = 1.0
        
        # Check 1: Exit code consistency
        if result.get("status") == "completed":
            if result.get("exit_code", 0) != 0:
                issues.append(f"Task marked completed but exit code is {result.get('exit_code')}")
                confidence *= 0.5
        
        # Check 2: Expected files
        expected_files = task.get("metadata", {}).get("expected_files", [])
        for file_path in expected_files:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                issues.append(f"Expected file not found: {file_path}")
                confidence *= 0.7
        
        # Check 3: Error patterns in output
        output = result.get("output", "")
        error_patterns = [
            r"error:",
            r"exception:",
            r"failed",
            r"traceback",
            r"cannot",
            r"permission denied"
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                warnings.append(f"Potential error pattern in output: {pattern}")
                confidence *= 0.9
        
        # Check 4: Success indicators
        if result.get("status") == "completed":
            success_patterns = [
                r"success",
                r"completed",
                r"✓",
                r"done",
                r"finished"
            ]
            
            has_success_indicator = any(
                re.search(pattern, output, re.IGNORECASE)
                for pattern in success_patterns
            )
            
            if not has_success_indicator and output:
                warnings.append("No success indicator found in output")
                confidence *= 0.95
        
        is_valid = confidence >= 0.7 and len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            metadata={
                "task_id": task.get("task_id"),
                "validation_time": datetime.now().isoformat()
            }
        )
    
    def validate_execution_plan_results(
        self,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate overall execution plan results
        
        Checks:
        1. All tasks have results
        2. Dependency order was respected
        3. No circular dependencies executed
        4. Expected completion rate
        """
        issues = []
        warnings = []
        confidence = 1.0
        
        tasks = plan.get("tasks", [])
        result_task_ids = {r.get("task_id") for r in results}
        
        # Check 1: All tasks have results
        for task in tasks:
            if task.get("task_id") not in result_task_ids:
                issues.append(f"Missing result for task: {task.get('task_id')}")
                confidence *= 0.8
        
        # Check 2: Dependency order
        task_by_id = {t.get("task_id"): t for t in tasks}
        completed_tasks = set()
        
        for result in sorted(results, key=lambda r: r.get("execution_order", 0)):
            task_id = result.get("task_id")
            if task_id in task_by_id:
                task = task_by_id[task_id]
                dependencies = task.get("depends_on", [])
                
                for dep_id in dependencies:
                    if dep_id not in completed_tasks:
                        warnings.append(
                            f"Task {task_id} executed before dependency {dep_id}"
                        )
                        confidence *= 0.95
                
                if result.get("status") == "completed":
                    completed_tasks.add(task_id)
        
        # Check 3: Expected completion rate
        total_tasks = len(tasks)
        completed = sum(1 for r in results if r.get("status") == "completed")
        completion_rate = completed / total_tasks if total_tasks > 0 else 0
        
        if completion_rate < 0.5:
            warnings.append(
                f"Low completion rate: {completion_rate:.1%} ({completed}/{total_tasks})"
            )
            confidence *= 0.9
        
        is_valid = confidence >= 0.7 and len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            metadata={
                "total_tasks": total_tasks,
                "completed": completed,
                "completion_rate": completion_rate,
                "validation_time": datetime.now().isoformat()
            }
        )
    
    def validate_file_changes(
        self,
        expected_changes: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate that expected file changes occurred
        
        Uses git to check for actual changes
        """
        issues = []
        warnings = []
        confidence = 1.0
        
        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                warnings.append("Could not get git status")
                confidence *= 0.9
            else:
                changed_files = set()
                for line in result.stdout.splitlines():
                    if line.strip():
                        # Format: "XY filename"
                        changed_files.add(line[3:].strip())
                
                # Check expected changes
                for change in expected_changes:
                    file_path = change.get("file_path")
                    action = change.get("action")  # create, modify, delete
                    
                    if file_path not in changed_files:
                        full_path = self.repo_root / file_path
                        
                        # Check if file exists
                        if action in ["create", "modify"] and not full_path.exists():
                            issues.append(f"Expected file not found: {file_path}")
                            confidence *= 0.7
                        elif action == "delete" and full_path.exists():
                            issues.append(f"File should be deleted but exists: {file_path}")
                            confidence *= 0.7
                        else:
                            warnings.append(f"No git change detected for: {file_path}")
                            confidence *= 0.95
        
        except subprocess.TimeoutExpired:
            warnings.append("Git command timed out")
            confidence *= 0.8
        except Exception as e:
            warnings.append(f"Validation error: {e}")
            confidence *= 0.8
        
        is_valid = confidence >= 0.7 and len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            metadata={
                "expected_changes": len(expected_changes),
                "validation_time": datetime.now().isoformat()
            }
        )


class HallucinationDetector:
    """Detects hallucinated successes (fake completions)"""
    
    def __init__(self):
        self.hallucination_patterns = [
            # Mock/placeholder indicators
            r"mock execution",
            r"placeholder",
            r"todo",
            r"not implemented",
            r"stub",
            
            # Suspicious success messages
            r"task .* completed successfully$",  # Too generic
            r"inferred from",
            r"assumed",
            r"simulated",
            
            # No-op indicators
            r"no changes",
            r"skipped",
            r"bypassed"
        ]
    
    def detect_hallucination(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Detect if result is a hallucinated success
        
        Returns:
            Hallucination reason if detected, None otherwise
        """
        if result.get("status") != "completed":
            return None  # Only check "completed" tasks
        
        output = result.get("output", "").lower()
        
        # Check for hallucination patterns
        for pattern in self.hallucination_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return f"Hallucination pattern detected: {pattern}"
        
        # Check for suspiciously fast execution
        execution_time = result.get("execution_time_seconds", 0)
        if execution_time < 0.01:  # Less than 10ms
            return "Execution time suspiciously fast (< 10ms)"
        
        # Check for empty output on tasks that should produce output
        task_kind = task.get("task_kind", "")
        if task_kind in ["code_generation", "refactoring", "testing"]:
            if not output or len(output) < 10:
                return "No meaningful output for task type"
        
        return None


def create_validation_pipeline(repo_root: Path) -> tuple:
    """
    Factory function to create validation components
    
    Returns:
        (ResultValidator, HallucinationDetector)
    """
    validator = ResultValidator(repo_root)
    hallucination_detector = HallucinationDetector()
    
    return validator, hallucination_detector
