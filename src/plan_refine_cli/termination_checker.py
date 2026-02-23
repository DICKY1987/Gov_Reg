"""
Termination Checker
Determines when planning refinement loop should terminate.
"""
from typing import Dict, Tuple, List


class TerminationChecker:
    """Checks termination conditions for planning loop"""
    
    def __init__(self, max_iterations: int = 5, 
                 plateau_threshold: float = 0.05,
                 plateau_window: int = 2):
        self.max_iterations = max_iterations
        self.plateau_threshold = plateau_threshold
        self.plateau_window = plateau_window
    
    def check_termination(self, iteration: int, 
                         defect_trajectory: List[Dict],
                         hard_defects_count: int,
                         staleness_status: str) -> Tuple[bool, str, Dict]:
        """Check if loop should terminate
        
        Args:
            iteration: Current iteration number
            defect_trajectory: History of defect counts
            hard_defects_count: Current hard defect count
            staleness_status: Current staleness status
            
        Returns:
            Tuple of (should_terminate, reason, details)
        """
        details = {
            "iteration": iteration,
            "hard_defects_count": hard_defects_count,
            "staleness_status": staleness_status
        }
        
        # Priority 1: Zero hard defects (SUCCESS)
        if hard_defects_count == 0:
            details["success"] = True
            return True, "ZERO_HARD_DEFECTS", details
        
        # Priority 2: Context is stale
        if staleness_status == "STALE":
            details["success"] = False
            return True, "CONTEXT_STALE", details
        
        # Priority 3: Max iterations reached
        if iteration >= self.max_iterations:
            details["success"] = False
            return True, "MAX_ITERATIONS_REACHED", details
        
        # Priority 4: Soft defects plateaued
        if self._detect_plateau(defect_trajectory):
            details["success"] = hard_defects_count == 0
            details["plateau_detected"] = True
            return True, "SOFT_DEFECTS_PLATEAUED", details
        
        # Continue iterating
        return False, "CONTINUE", details
    
    def _detect_plateau(self, trajectory: List[Dict]) -> bool:
        """Detect if soft defects have plateaued
        
        Args:
            trajectory: List of {iteration, hard_count, soft_count}
            
        Returns:
            True if plateau detected
        """
        if len(trajectory) < self.plateau_window + 1:
            return False
        
        # Check last N iterations
        recent = trajectory[-self.plateau_window:]
        
        # Calculate improvement rate
        if len(recent) < 2:
            return False
        
        improvements = []
        for i in range(1, len(recent)):
            prev_soft = recent[i-1]["soft_count"]
            curr_soft = recent[i]["soft_count"]
            
            if prev_soft == 0:
                improvement = 0
            else:
                improvement = (prev_soft - curr_soft) / prev_soft
            
            improvements.append(improvement)
        
        # If average improvement is below threshold, plateau detected
        avg_improvement = sum(improvements) / len(improvements)
        return avg_improvement < self.plateau_threshold
    
    def format_termination_message(self, reason: str, details: Dict) -> str:
        """Format human-readable termination message
        
        Args:
            reason: Termination reason code
            details: Details dictionary
            
        Returns:
            Formatted message
        """
        messages = {
            "ZERO_HARD_DEFECTS": "✅ Loop terminated: All hard defects resolved",
            "CONTEXT_STALE": "⚠️ Loop terminated: Context became stale",
            "MAX_ITERATIONS_REACHED": "⏱️ Loop terminated: Maximum iterations reached",
            "SOFT_DEFECTS_PLATEAUED": "📊 Loop terminated: Soft defects plateaued",
            "MANUAL_STOP": "🛑 Loop terminated: Manual stop requested"
        }
        
        base_msg = messages.get(reason, f"Loop terminated: {reason}")
        
        # Add details
        detail_lines = [base_msg]
        if "iteration" in details:
            detail_lines.append(f"  Iterations: {details['iteration']}")
        if "hard_defects_count" in details:
            detail_lines.append(f"  Hard defects: {details['hard_defects_count']}")
        
        return "\n".join(detail_lines)
