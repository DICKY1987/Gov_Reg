#!/usr/bin/env python3
"""Validate Phase 4 approval from approval record."""

import sys
import json
from pathlib import Path


def validate_phase4_approval(approval_file):
    """Validate Phase 4 approval has been granted."""
    print("Phase 4 Approval Validation")
    print("=" * 70)
    
    try:
        with open(approval_file, 'r', encoding='utf-8') as f:
            approval_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Approval file not found: {approval_file}")
        print("=" * 70)
        print("✗ APPROVAL NOT FOUND")
        return 1
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in approval file: {approval_file}")
        print("=" * 70)
        print("✗ INVALID APPROVAL FILE")
        return 1
    
    decision = approval_data.get('decision', 'PENDING')
    decision_type = approval_data.get('decision_type', 'UNKNOWN')
    effective_date = approval_data.get('effective_date', 'UNKNOWN')
    
    print(f"Decision: {decision}")
    print(f"Type: {decision_type}")
    print(f"Effective Date: {effective_date}")
    
    # Check committee votes
    committee = approval_data.get('approval_committee', {})
    vote_summary = committee.get('vote_summary', {})
    
    if vote_summary:
        total = vote_summary.get('total_members', 0)
        approved = vote_summary.get('approved', 0)
        rejected = vote_summary.get('rejected', 0)
        result = vote_summary.get('result', 'UNKNOWN')
        
        print(f"\nCommittee Vote:")
        print(f"  Approved: {approved}/{total}")
        print(f"  Rejected: {rejected}/{total}")
        print(f"  Result: {result}")
    
    # Check approval criteria
    criteria_met = approval_data.get('approval_criteria_met', {})
    if criteria_met:
        print(f"\nApproval Criteria:")
        all_met = all(criteria_met.values())
        for criterion, met in criteria_met.items():
            marker = "✓" if met else "✗"
            print(f"  {marker} {criterion.replace('_', ' ').title()}")
    
    print("=" * 70)
    
    # Validate decision
    if decision == 'APPROVED' and (decision_type == 'UNANIMOUS' or decision_type == 'MAJORITY'):
        print("✓ PHASE 4 APPROVAL VALIDATED")
        print("  Authorization to proceed with Phase 4+ deployment")
        print("\n⚠️  WARNING: Phase 4+ is irreversible")
        print("  This approval authorizes crossing the point of no return")
        return 0
    
    elif decision == 'APPROVED':
        print("⚠ PHASE 4 APPROVED (with conditions)")
        print("  Verify decision type and conditions before proceeding")
        return 0
    
    elif decision == 'DEFERRED':
        print("⏸ PHASE 4 DEFERRED")
        print("  Approval postponed pending additional review")
        return 1
    
    elif decision == 'REJECTED':
        print("✗ PHASE 4 REJECTED")
        print("  Cannot proceed with Phase 4+ deployment")
        return 1
    
    else:
        print(f"? PHASE 4 STATUS UNKNOWN")
        print(f"  Unexpected decision status: {decision}")
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_phase4_approval.py <approval_file.json>")
        sys.exit(1)
    
    approval_file = sys.argv[1]
    sys.exit(validate_phase4_approval(approval_file))
