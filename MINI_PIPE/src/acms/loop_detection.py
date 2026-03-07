"""
Loop Detection and Prevention System

Detects and prevents infinite loops in planning, execution, and other
automated workflows. Implements automatic simplification and circuit breaking.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict


@dataclass
class LoopDetection:
    """Represents a detected loop"""
    loop_type: str  # planning, execution, validation
    iterations: int
    threshold: int
    first_seen: datetime
    last_seen: datetime
    context: Dict[str, Any]
    resolved: bool = False


class LoopDetector:
    """Detects loops in automated workflows"""
    
    def __init__(
        self,
        planning_threshold: int = 3,
        execution_threshold: int = 5,
        validation_threshold: int = 10
    ):
        self.planning_threshold = planning_threshold
        self.execution_threshold = execution_threshold
        self.validation_threshold = validation_threshold
        
        # Track state for loop detection
        self.planning_attempts: List[Dict[str, Any]] = []
        self.execution_attempts: Dict[str, List[Dict]] = defaultdict(list)
        self.validation_attempts: Dict[str, int] = defaultdict(int)
        
        # Detected loops
        self.detected_loops: List[LoopDetection] = []
    
    def record_planning_attempt(
        self,
        run_id: str,
        gap_ids: List[str],
        workstream_count: int
    ) -> Optional[LoopDetection]:
        """
        Record a planning attempt and check for loops
        
        Returns:
            LoopDetection if loop detected, None otherwise
        """
        attempt = {
            "run_id": run_id,
            "gap_ids": sorted(gap_ids),
            "workstream_count": workstream_count,
            "timestamp": datetime.now()
        }
        
        self.planning_attempts.append(attempt)
        
        # Check for planning loop
        recent_attempts = self.planning_attempts[-self.planning_threshold:]
        
        if len(recent_attempts) >= self.planning_threshold:
            # Check if same gaps being planned repeatedly
            gap_sets = [set(a["gap_ids"]) for a in recent_attempts]
            
            if len(set(map(frozenset, gap_sets))) == 1:
                # Same gaps planned multiple times
                loop = LoopDetection(
                    loop_type="planning",
                    iterations=len(recent_attempts),
                    threshold=self.planning_threshold,
                    first_seen=recent_attempts[0]["timestamp"],
                    last_seen=recent_attempts[-1]["timestamp"],
                    context={
                        "gap_ids": gap_ids,
                        "workstream_count": workstream_count,
                        "attempts": recent_attempts
                    }
                )
                
                self.detected_loops.append(loop)
                return loop
        
        return None
    
    def record_execution_attempt(
        self,
        task_id: str,
        success: bool,
        error: Optional[str] = None
    ) -> Optional[LoopDetection]:
        """
        Record a task execution attempt and check for loops
        
        Returns:
            LoopDetection if loop detected, None otherwise
        """
        attempt = {
            "task_id": task_id,
            "success": success,
            "error": error,
            "timestamp": datetime.now()
        }
        
        self.execution_attempts[task_id].append(attempt)
        
        # Check for execution loop (repeated failures)
        task_attempts = self.execution_attempts[task_id]
        
        if len(task_attempts) >= self.execution_threshold:
            # Check recent attempts
            recent = task_attempts[-self.execution_threshold:]
            failed = [a for a in recent if not a["success"]]
            
            if len(failed) >= self.execution_threshold:
                # Same task failing repeatedly
                loop = LoopDetection(
                    loop_type="execution",
                    iterations=len(failed),
                    threshold=self.execution_threshold,
                    first_seen=failed[0]["timestamp"],
                    last_seen=failed[-1]["timestamp"],
                    context={
                        "task_id": task_id,
                        "errors": [f["error"] for f in failed if f["error"]],
                        "attempts": recent
                    }
                )
                
                self.detected_loops.append(loop)
                return loop
        
        return None
    
    def record_validation_attempt(
        self,
        validation_id: str
    ) -> Optional[LoopDetection]:
        """
        Record a validation attempt and check for loops
        
        Returns:
            LoopDetection if loop detected, None otherwise
        """
        self.validation_attempts[validation_id] += 1
        
        if self.validation_attempts[validation_id] >= self.validation_threshold:
            loop = LoopDetection(
                loop_type="validation",
                iterations=self.validation_attempts[validation_id],
                threshold=self.validation_threshold,
                first_seen=datetime.now() - timedelta(minutes=5),  # Estimate
                last_seen=datetime.now(),
                context={
                    "validation_id": validation_id,
                    "iterations": self.validation_attempts[validation_id]
                }
            )
            
            self.detected_loops.append(loop)
            return loop
        
        return None
    
    def reset_planning_attempts(self):
        """Reset planning attempts counter"""
        self.planning_attempts = []
    
    def reset_execution_attempts(self, task_id: str):
        """Reset execution attempts for a task"""
        if task_id in self.execution_attempts:
            del self.execution_attempts[task_id]
    
    def get_active_loops(self) -> List[LoopDetection]:
        """Get all active (unresolved) loops"""
        return [loop for loop in self.detected_loops if not loop.resolved]
    
    def resolve_loop(self, loop: LoopDetection):
        """Mark a loop as resolved"""
        loop.resolved = True


class LoopPrevention:
    """Prevents loops through automatic interventions"""
    
    def __init__(self, detector: LoopDetector):
        self.detector = detector
    
    def handle_planning_loop(
        self,
        loop: LoopDetection,
        current_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle planning loop by simplifying the plan
        
        Strategies:
        1. Reduce workstream count
        2. Remove low-priority gaps
        3. Consolidate similar tasks
        """
        print(f"\n⚠️  PLANNING LOOP DETECTED")
        print(f"   Iterations: {loop.iterations}")
        print(f"   Strategy: Simplifying plan\n")
        
        simplified_plan = current_plan.copy()
        
        # Strategy 1: Reduce workstream count by 50%
        if "workstreams" in simplified_plan:
            workstreams = simplified_plan["workstreams"]
            target_count = max(1, len(workstreams) // 2)
            
            # Keep highest priority workstreams
            sorted_ws = sorted(
                workstreams,
                key=lambda w: w.get("priority", 999),
                reverse=False
            )
            
            simplified_plan["workstreams"] = sorted_ws[:target_count]
            print(f"   → Reduced workstreams: {len(workstreams)} → {target_count}")
        
        # Strategy 2: Remove low-priority gaps
        if "gaps" in simplified_plan:
            gaps = simplified_plan["gaps"]
            high_priority = [
                g for g in gaps
                if g.get("severity") in ["critical", "high"]
            ]
            
            if len(high_priority) < len(gaps):
                simplified_plan["gaps"] = high_priority
                print(f"   → Filtered gaps: {len(gaps)} → {len(high_priority)} (critical/high only)")
        
        # Mark loop as resolved
        self.detector.resolve_loop(loop)
        
        return simplified_plan
    
    def handle_execution_loop(
        self,
        loop: LoopDetection,
        task: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle execution loop
        
        Strategies:
        1. Skip the failing task
        2. Mark dependencies as skipped
        3. Continue with other tasks
        """
        task_id = loop.context["task_id"]
        
        print(f"\n⚠️  EXECUTION LOOP DETECTED")
        print(f"   Task: {task_id}")
        print(f"   Failures: {loop.iterations}")
        print(f"   Strategy: Skipping task\n")
        
        # Mark task as skipped
        task["status"] = "skipped"
        task["skip_reason"] = f"Execution loop detected ({loop.iterations} failures)"
        
        # Mark loop as resolved
        self.detector.resolve_loop(loop)
        
        return task
    
    def handle_validation_loop(
        self,
        loop: LoopDetection
    ) -> str:
        """
        Handle validation loop
        
        Strategy: Stop validation and accept current state
        """
        validation_id = loop.context["validation_id"]
        
        print(f"\n⚠️  VALIDATION LOOP DETECTED")
        print(f"   Validation: {validation_id}")
        print(f"   Iterations: {loop.iterations}")
        print(f"   Strategy: Accepting current state\n")
        
        # Mark loop as resolved
        self.detector.resolve_loop(loop)
        
        return "accept"


def create_loop_protection(
    planning_threshold: int = 3,
    execution_threshold: int = 5,
    validation_threshold: int = 10
) -> tuple:
    """
    Factory function to create loop detector and prevention
    
    Returns:
        (LoopDetector, LoopPrevention)
    """
    detector = LoopDetector(
        planning_threshold=planning_threshold,
        execution_threshold=execution_threshold,
        validation_threshold=validation_threshold
    )
    
    prevention = LoopPrevention(detector)
    
    return detector, prevention
