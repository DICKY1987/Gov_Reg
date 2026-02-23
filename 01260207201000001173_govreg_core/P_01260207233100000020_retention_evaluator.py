"""
Retention Evaluator - State-Based Evidence Retention

Implements state-based retention per spec Section 3.2.

Overrides:
- Incomplete plans → retain indefinitely
- Open defects → retain until closed
- NO_OVERLAP failures → permanent retention
- Audit-flagged → permanent retention
- Diverged reconciliation → extended retention (180 days)
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class RetentionDecision(Enum):
    """Retention decision outcomes."""
    DELETE = "delete"
    RETAIN = "retain"
    ARCHIVE = "archive"
    RETAIN_INDEFINITELY = "retain_indefinitely"


class RetentionEvaluator:
    """Evaluate retention decisions with state-based overrides."""
    
    def __init__(self, evidence_dir: str = ".state/evidence/retention"):
        """
        Initialize retention evaluator.
        
        Args:
            evidence_dir: Directory for retention decision evidence
        """
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate_retention(
        self,
        artifact_path: str,
        artifact_age_days: int,
        plan_status: str,
        reconciliation_state: str,
        linked_defects: List[Dict],
        audit_flagged: bool
    ) -> RetentionDecision:
        """
        Evaluate retention decision with state-based overrides.
        
        Args:
            artifact_path: Path to artifact
            artifact_age_days: Age in days
            plan_status: Plan status (COMPLETE, INCOMPLETE, etc.)
            reconciliation_state: Reconciliation state
            linked_defects: List of linked defects
            audit_flagged: Whether artifact is flagged for audit
        
        Returns:
            RetentionDecision enum value
        """
        # Override 1: No-overlap failures (permanent retention)
        if reconciliation_state == "NO_OVERLAP":
            decision = RetentionDecision.RETAIN_INDEFINITELY
            reason = "NO_OVERLAP failure - permanent retention required"
            self._emit_evidence(artifact_path, decision, reason)
            return decision
        
        # Override 2: Audit-flagged (permanent retention)
        if audit_flagged:
            if artifact_age_days > 365:
                decision = RetentionDecision.ARCHIVE
                reason = "Audit-flagged, over 1 year old - archive"
            else:
                decision = RetentionDecision.RETAIN_INDEFINITELY
                reason = "Audit-flagged - permanent retention"
            self._emit_evidence(artifact_path, decision, reason)
            return decision
        
        # Override 3: Incomplete plans (retain until terminal state)
        if plan_status not in ["COMPLETE", "CANCELLED", "ABANDONED"]:
            decision = RetentionDecision.RETAIN_INDEFINITELY
            reason = f"Plan status {plan_status} - retain until terminal state"
            self._emit_evidence(artifact_path, decision, reason)
            return decision
        
        # Override 4: Open defects
        open_defects = [d for d in linked_defects if d.get('status') == 'OPEN']
        if open_defects:
            if artifact_age_days > 365:
                decision = RetentionDecision.ARCHIVE
                reason = f"{len(open_defects)} open defects, over 1 year old - archive"
            else:
                decision = RetentionDecision.RETAIN_INDEFINITELY
                reason = f"{len(open_defects)} open defects - retain until closed"
            self._emit_evidence(artifact_path, decision, reason)
            return decision
        
        # Override 5: Diverged reconciliation (extended retention)
        if reconciliation_state in ["SUBSET_MATCH", "PARTIAL_OVERLAP", "DIVERGED"]:
            retention_days = 180
        else:
            # Base retention
            if "planning" in artifact_path or "PFMS" in artifact_path:
                retention_days = 90
            elif "evidence" in artifact_path:
                retention_days = 90
            elif "runs" in artifact_path:
                retention_days = 30
            else:
                retention_days = 90  # Default
        
        # Apply retention decision
        if artifact_age_days > retention_days:
            decision = RetentionDecision.DELETE
            reason = f"Age {artifact_age_days} days exceeds retention {retention_days} days"
        else:
            decision = RetentionDecision.RETAIN
            reason = f"Within retention period ({artifact_age_days}/{retention_days} days)"
        
        self._emit_evidence(artifact_path, decision, reason)
        return decision
    
    def _emit_evidence(
        self,
        artifact_path: str,
        decision: RetentionDecision,
        reason: str
    ):
        """
        Emit evidence for retention decision.
        
        Args:
            artifact_path: Path to artifact
            decision: Retention decision
            reason: Human-readable reason
        """
        timestamp = datetime.utcnow()
        evidence_file = self.evidence_dir / f"decision_{int(timestamp.timestamp())}.json"
        
        evidence = {
            'artifact_path': artifact_path,
            'decision': decision.value,
            'reason': reason,
            'evaluated_at': timestamp.isoformat(),
            'evaluated_by': 'retention_evaluator_v1.0'
        }
        
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.debug(f"Retention decision: {artifact_path} → {decision.value}")


def evaluate_retention(
    artifact_path: str,
    artifact_age_days: int,
    plan_status: str = "COMPLETE",
    reconciliation_state: str = "EXACT_MATCH",
    linked_defects: List[Dict] = None,
    audit_flagged: bool = False
) -> RetentionDecision:
    """Evaluate retention (convenience wrapper)."""
    evaluator = RetentionEvaluator()
    return evaluator.evaluate_retention(
        artifact_path,
        artifact_age_days,
        plan_status,
        reconciliation_state,
        linked_defects or [],
        audit_flagged
    )
