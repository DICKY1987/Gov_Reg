"""
Tests for retention_evaluator - State-Based Retention
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from govreg_core.retention_evaluator import RetentionEvaluator, RetentionDecision


def test_no_overlap_permanent_retention():
    """Test: NO_OVERLAP failures → permanent retention."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_001.json",
        artifact_age_days=100,
        plan_status="COMPLETE",
        reconciliation_state="NO_OVERLAP",
        linked_defects=[],
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.RETAIN_INDEFINITELY


def test_audit_flagged_permanent_retention():
    """Test: Audit-flagged → permanent retention."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_002.json",
        artifact_age_days=100,
        plan_status="COMPLETE",
        reconciliation_state="EXACT_MATCH",
        linked_defects=[],
        audit_flagged=True
    )
    
    assert decision == RetentionDecision.RETAIN_INDEFINITELY


def test_audit_flagged_archive_after_year():
    """Test: Audit-flagged over 1 year → archive."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_003.json",
        artifact_age_days=400,  # Over 1 year
        plan_status="COMPLETE",
        reconciliation_state="EXACT_MATCH",
        linked_defects=[],
        audit_flagged=True
    )
    
    assert decision == RetentionDecision.ARCHIVE


def test_incomplete_plan_retention():
    """Test: Incomplete plans → retain indefinitely."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="planning/plan_004.json",
        artifact_age_days=100,
        plan_status="IN_PROGRESS",
        reconciliation_state="EXACT_MATCH",
        linked_defects=[],
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.RETAIN_INDEFINITELY


def test_open_defects_retention():
    """Test: Open defects → retain until closed."""
    evaluator = RetentionEvaluator()
    
    defects = [
        {'defect_id': 'DEF-001', 'status': 'OPEN'},
        {'defect_id': 'DEF-002', 'status': 'CLOSED'}
    ]
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_005.json",
        artifact_age_days=100,
        plan_status="COMPLETE",
        reconciliation_state="EXACT_MATCH",
        linked_defects=defects,
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.RETAIN_INDEFINITELY


def test_base_retention_delete():
    """Test: Past retention period → delete."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_006.json",
        artifact_age_days=100,  # Past 90 days
        plan_status="COMPLETE",
        reconciliation_state="EXACT_MATCH",
        linked_defects=[],
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.DELETE


def test_base_retention_retain():
    """Test: Within retention period → retain."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_007.json",
        artifact_age_days=50,  # Within 90 days
        plan_status="COMPLETE",
        reconciliation_state="EXACT_MATCH",
        linked_defects=[],
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.RETAIN


def test_diverged_extended_retention():
    """Test: Diverged reconciliation → extended 180 days."""
    evaluator = RetentionEvaluator()
    
    decision = evaluator.evaluate_retention(
        artifact_path="evidence/plan_008.json",
        artifact_age_days=100,  # Past 90 but within 180
        plan_status="COMPLETE",
        reconciliation_state="DIVERGED",
        linked_defects=[],
        audit_flagged=False
    )
    
    assert decision == RetentionDecision.RETAIN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
