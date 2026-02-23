"""
Control Plane
LangGraph-based orchestration of the planning refinement loop.
"""
import json
from pathlib import Path
from typing import Dict, Optional, TypedDict
from datetime import datetime

from .run_directory import RunDirectoryManager
from .hash_utils import compute_json_hash
from .patch_applicator import PatchApplicator
from .staleness_checker import StalenessChecker
from .termination_checker import TerminationChecker


class GraphState(TypedDict):
    """State object passed between LangGraph nodes"""
    run_id: str
    iteration: int
    current_plan: Dict
    current_plan_hash: str
    context_bundle: Dict
    context_bundle_hash: str
    policy_snapshot: Dict
    policy_hash: str
    critic_report: Optional[Dict]
    proposed_patch: Optional[Dict]
    defect_trajectory: list
    should_terminate: bool
    termination_reason: str
    artifacts: list


class ControlPlane:
    """Orchestrates planning refinement loop using LangGraph"""
    
    def __init__(self, state_root: Path, schema_dir: Path):
        self.state_root = Path(state_root)
        self.schema_dir = Path(schema_dir)
        self.run_manager = RunDirectoryManager(state_root)
        self.patch_applicator = PatchApplicator()
        self.staleness_checker = StalenessChecker(staleness_threshold_hours=24)
        self.termination_checker = TerminationChecker(max_iterations=5)
    
    def initialize_state(self, run_id: str, skeleton_plan: Dict,
                        context_bundle: Dict, policy_snapshot: Dict) -> GraphState:
        """Initialize graph state for new run
        
        Args:
            run_id: Planning run identifier
            skeleton_plan: Initial plan skeleton
            context_bundle: Repository context
            policy_snapshot: Policy configuration
            
        Returns:
            Initial graph state
        """
        state: GraphState = {
            "run_id": run_id,
            "iteration": 0,
            "current_plan": skeleton_plan,
            "current_plan_hash": compute_json_hash(skeleton_plan),
            "context_bundle": context_bundle,
            "context_bundle_hash": compute_json_hash(context_bundle),
            "policy_snapshot": policy_snapshot,
            "policy_hash": compute_json_hash(policy_snapshot),
            "critic_report": None,
            "proposed_patch": None,
            "defect_trajectory": [],
            "should_terminate": False,
            "termination_reason": "",
            "artifacts": []
        }
        
        return state
    
    def node_check_staleness(self, state: GraphState) -> GraphState:
        """LangGraph node: Check context staleness"""
        run_dir = self.run_manager.get_run_directory(state["run_id"])
        context_path = run_dir / "context_bundle.json"
        
        staleness_status, details = self.staleness_checker.check_context_staleness(
            state["context_bundle"], context_path
        )
        
        # Save staleness check evidence
        evidence_path = self.run_manager.get_evidence_path(
            state["run_id"], "PH-02", f"ITER-{state['iteration']:03d}"
        )
        staleness_report_path = evidence_path / "staleness_check.json"
        with open(staleness_report_path, 'w') as f:
            json.dump({
                "status": staleness_status,
                "details": details
            }, f, indent=2)
        
        # Check termination due to staleness
        if staleness_status == "STALE":
            should_terminate, reason, term_details = self.termination_checker.check_termination(
                state["iteration"],
                state["defect_trajectory"],
                len(state.get("critic_report", {}).get("hard_defects", [])),
                staleness_status
            )
            state["should_terminate"] = should_terminate
            state["termination_reason"] = reason
        
        return state
    
    def node_invoke_critic(self, state: GraphState) -> GraphState:
        """LangGraph node: Invoke critic (placeholder)"""
        # Placeholder: Will invoke CriticAgent
        state["critic_report"] = {
            "report_id": f"CRITIC_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_placeholder",
            "plan_hash": state["current_plan_hash"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hard_defects": [],
            "soft_defects": [],
            "summary": {
                "total_defects": 0,
                "hard_count": 0,
                "soft_count": 0,
                "recommendation": "PROCEED"
            }
        }
        return state
    
    def node_check_termination(self, state: GraphState) -> GraphState:
        """LangGraph node: Check termination conditions"""
        hard_count = len(state.get("critic_report", {}).get("hard_defects", []))
        soft_count = len(state.get("critic_report", {}).get("soft_defects", []))
        
        # Update trajectory
        state["defect_trajectory"].append({
            "iteration": state["iteration"],
            "hard_count": hard_count,
            "soft_count": soft_count
        })
        
        should_terminate, reason, details = self.termination_checker.check_termination(
            state["iteration"],
            state["defect_trajectory"],
            hard_count,
            "FRESH"  # Placeholder
        )
        
        state["should_terminate"] = should_terminate
        state["termination_reason"] = reason
        
        return state
    
    def node_invoke_planner(self, state: GraphState) -> GraphState:
        """LangGraph node: Invoke planner for refinement (placeholder)"""
        # Placeholder: Will invoke PlannerAgent
        state["proposed_patch"] = None
        return state
    
    def node_apply_patch(self, state: GraphState) -> GraphState:
        """LangGraph node: Apply patch to plan"""
        if state["proposed_patch"] is None:
            return state
        
        patched_plan, success, error_msg = self.patch_applicator.apply_patch(
            state["current_plan"],
            state["proposed_patch"]
        )
        
        if success:
            state["current_plan"] = patched_plan
            state["current_plan_hash"] = compute_json_hash(patched_plan)
            state["iteration"] += 1
        else:
            # Log error and continue with unpatched plan
            print(f"⚠️ Patch application failed: {error_msg}")
        
        return state
    
    def should_continue_loop(self, state: GraphState) -> bool:
        """Decision function for loop continuation"""
        return not state["should_terminate"]
