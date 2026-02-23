#!/usr/bin/env python3
"""Validate approval status from approval record."""

import sys
import json
from pathlib import Path


def validate_approval_status(approval_record_path):
    """Validate that approval has been granted."""
    try:
        with open(approval_record_path, 'r', encoding='utf-8') as f:
            approval_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Approval record not found: {approval_record_path}")
        return 1
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in approval record: {approval_record_path}")
        return 1
    
    decision = approval_data.get('decision', 'PENDING')
    status = approval_data.get('status', 'UNKNOWN')
    
    print("Approval Status Validation")
    print("=" * 70)
    print(f"Decision: {decision}")
    print(f"Status: {status}")
    
    if decision == 'APPROVED':
        # Check committee votes if available
        committee = approval_data.get('committee_members', [])
        if committee:
            approved_count = sum(1 for m in committee if m.get('vote') == 'APPROVED')
            total_count = len(committee)
            print(f"Committee Votes: {approved_count}/{total_count} approved")
            
            if approved_count == total_count:
                print("=" * 70)
                print("✓ APPROVAL VALIDATED - Unanimous approval obtained")
                return 0
            elif approved_count >= (total_count * 0.75):
                print("=" * 70)
                print("✓ APPROVAL VALIDATED - Majority approval obtained")
                return 0
        else:
            print("=" * 70)
            print("✓ APPROVAL VALIDATED")
            return 0
    
    elif decision == 'PENDING':
        print("=" * 70)
        print("⚠ APPROVAL PENDING - Awaiting committee decision")
        return 1
    
    elif decision == 'REJECTED':
        print("=" * 70)
        print("✗ APPROVAL REJECTED - Cannot proceed")
        return 1
    
    else:
        print("=" * 70)
        print(f"? UNKNOWN STATUS - Decision: {decision}")
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_approval_status.py <approval_record.json>")
        sys.exit(1)
    
    approval_record_path = sys.argv[1]
    sys.exit(validate_approval_status(approval_record_path))
