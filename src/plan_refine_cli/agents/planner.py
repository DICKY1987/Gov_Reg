"""
Planner Agent
Generates and refines structural plans using LLM or templates.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from ..hash_utils import compute_json_hash


class PlannerAgent:
    """Generates plan skeletons and refinement patches"""
    
    def __init__(self, schema_dir: Path, prompts_dir: Path):
        self.schema_dir = Path(schema_dir)
        self.prompts_dir = Path(prompts_dir)
        self.mode = "DETERMINISTIC"  # Default to deterministic mode
    
    def generate_skeleton(self, context_bundle: Dict, 
                         policy_snapshot: Dict) -> Dict:
        """Generate initial plan skeleton from context
        
        Args:
            context_bundle: Repository context
            policy_snapshot: Policy configuration
            
        Returns:
            Plan skeleton dictionary
        """
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        skeleton = {
            "plan_id": f"PLAN_{timestamp}_{short_uuid}",
            "version": "2.0",
            "objective": "Generated plan skeleton - placeholder",
            "scope": {
                "in_scope": ["Schema definitions", "CLI framework"],
                "out_of_scope": ["Production deployment"]
            },
            "assumptions": [],
            "constraints": [],
            "workstreams": [
                {
                    "workstream_id": "WS_FOUNDATION",
                    "name": "Foundation Setup",
                    "owner": "SYSTEM",
                    "inputs": [],
                    "outputs": [],
                    "steps": [],
                    "evidence_requirements": []
                }
            ],
            "deliverables": [
                {
                    "deliverable_id": "DEL-001",
                    "description": "Placeholder deliverable",
                    "acceptance_test": "pytest tests/"
                }
            ],
            "acceptance_criteria": [
                {
                    "criteria_id": "AC-001",
                    "description": "All tests pass",
                    "measurement_method": "pytest --cov",
                    "target_value": "95%"
                }
            ],
            "risks": [],
            "dependencies": [],
            "gates": [],
            "declared_new_artifacts": [],
            "metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "created_by": "PLANNER_AGENT",
                "template_version": "3.0.0",
                "planning_run_id": context_bundle.get("bundle_id", "unknown"),
                "iteration": 0
            }
        }
        
        return skeleton
    
    def refine_plan(self, in_plan: Dict, lint_report: Dict,
                   context_bundle: Dict, policy_snapshot: Dict) -> Tuple[Dict, Dict]:
        """Refine plan based on critic feedback
        
        Args:
            in_plan: Current plan version
            lint_report: Critic report with defects
            context_bundle: Repository context
            policy_snapshot: Policy configuration
            
        Returns:
            Tuple of (patch, proposed_plan)
        """
        # Extract defects to fix
        hard_defects = lint_report.get("hard_defects", [])
        
        if not hard_defects:
            # No refinement needed
            return None, in_plan
        
        # Generate patch to fix defects (deterministic mode - placeholder)
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        patch = {
            "patch_id": f"PATCH_{timestamp}_{short_uuid}",
            "created_by": "PLANNER_AGENT",
            "target_plan_hash": compute_json_hash(in_plan),
            "justification": [d["defect_id"] for d in hard_defects],
            "operations": [],
            "metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "iteration": in_plan.get("metadata", {}).get("iteration", 0) + 1,
                "defects_targeted": [d["defect_id"] for d in hard_defects]
            }
        }
        
        # Placeholder: Would generate actual patch operations
        # For now, return empty patch
        
        return patch, in_plan
    
    def validate_planner_constraints(self, plan: Dict, 
                                    context_bundle: Dict) -> Tuple[bool, Dict]:
        """Validate planner-specific constraints
        
        Args:
            plan: Plan to validate
            context_bundle: Repository context
            
        Returns:
            Tuple of (valid, validation_report)
        """
        report = {
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "errors": []
        }
        
        # Check required fields
        required = ["plan_id", "version", "objective", "workstreams"]
        for field in required:
            if field not in plan:
                report["errors"].append(f"Missing required field: {field}")
        
        # Check version
        if plan.get("version") != "2.0":
            report["errors"].append(f"Invalid version: {plan.get('version')}, expected 2.0")
        
        # Check declared_new_artifacts references
        declared = {art["artifact_id"] for art in plan.get("declared_new_artifacts", [])}
        
        # All outputs should either exist in context or be declared
        for ws in plan.get("workstreams", []):
            for output in ws.get("outputs", []):
                artifact_id = output.get("artifact_id")
                # Placeholder: Would check if artifact exists in context
                # For now, just validate structure
                if not artifact_id:
                    report["errors"].append("Output missing artifact_id")
        
        valid = len(report["errors"]) == 0
        report["valid"] = valid
        return valid, report
