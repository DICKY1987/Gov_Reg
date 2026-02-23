"""
Critic Agent
Analyzes plans for defects using deterministic and LLM-based methods.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from uuid import uuid4

from ..hash_utils import compute_json_hash


class CriticAgent:
    """Analyzes plans and generates defect reports"""
    
    def __init__(self, schema_dir: Path, prompts_dir: Path):
        self.schema_dir = Path(schema_dir)
        self.prompts_dir = Path(prompts_dir)
        self.mode = "DETERMINISTIC"  # Default mode
    
    def lint_plan(self, plan: Dict, policy_snapshot: Dict,
                 context_bundle: Dict, mode: str = "DETERMINISTIC") -> Dict:
        """Analyze plan for defects
        
        Args:
            plan: Plan to analyze
            policy_snapshot: Policy configuration
            context_bundle: Repository context
            mode: "DETERMINISTIC", "LLM", or "HYBRID"
            
        Returns:
            Critic report dictionary
        """
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        hard_defects = []
        soft_defects = []
        
        if mode in ["DETERMINISTIC", "HYBRID"]:
            # Run deterministic linters
            det_hard, det_soft = self.detect_defects_deterministic(plan, policy_snapshot)
            hard_defects.extend(det_hard)
            soft_defects.extend(det_soft)
        
        if mode in ["LLM", "HYBRID"]:
            # Run LLM-based analysis (placeholder)
            llm_hard, llm_soft = self.detect_defects_llm(plan, policy_snapshot, context_bundle)
            hard_defects.extend(llm_hard)
            soft_defects.extend(llm_soft)
        
        # Determine recommendation
        if hard_defects:
            recommendation = "REFINE"
        elif soft_defects:
            recommendation = "PROCEED"  # Can proceed with soft defects
        else:
            recommendation = "PROCEED"
        
        report = {
            "report_id": f"CRITIC_{timestamp}_{short_uuid}",
            "plan_hash": compute_json_hash(plan),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "hard_defects": hard_defects,
            "soft_defects": soft_defects,
            "summary": {
                "total_defects": len(hard_defects) + len(soft_defects),
                "hard_count": len(hard_defects),
                "soft_count": len(soft_defects),
                "recommendation": recommendation
            }
        }
        
        return report
    
    def detect_defects_deterministic(self, plan: Dict, 
                                    policy_snapshot: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Run deterministic linters on plan
        
        Args:
            plan: Plan to analyze
            policy_snapshot: Policy configuration
            
        Returns:
            Tuple of (hard_defects, soft_defects)
        """
        from ..linters.deterministic_linters import (
            CompletenessLinter,
            SchemaComplianceLinter,
            ForbiddenPatternsLinter,
            ReferenceValidityLinter,
            AcceptanceCriteriaLinter
        )
        
        hard_defects = []
        soft_defects = []
        
        # Run each linter
        linters = [
            CompletenessLinter(policy_snapshot),
            SchemaComplianceLinter(self.schema_dir),
            ForbiddenPatternsLinter(policy_snapshot),
            ReferenceValidityLinter(),
            AcceptanceCriteriaLinter()
        ]
        
        for linter in linters:
            defects = linter.lint(plan)
            for defect in defects:
                if defect["severity"] in ["CRITICAL", "HIGH"]:
                    hard_defects.append(defect)
                else:
                    soft_defects.append(defect)
        
        return hard_defects, soft_defects
    
    def detect_defects_llm(self, plan: Dict, policy_snapshot: Dict,
                          context_bundle: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Run LLM-based analysis on plan
        
        Args:
            plan: Plan to analyze
            policy_snapshot: Policy configuration
            context_bundle: Repository context
            
        Returns:
            Tuple of (hard_defects, soft_defects)
        """
        # Placeholder for LLM integration
        # Would use prompts/critic_llm.md and call LLM API
        return [], []
