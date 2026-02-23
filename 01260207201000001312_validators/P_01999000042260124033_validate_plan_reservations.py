"""Planning gate validator for file ID reservations.

FILE_ID: 01999000042260124033
DOC_ID: P_01999000042260124033
PHASE: 1.4 - Foundation (Validation Gate - Planning)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "govreg_core"))
from P_01999000042260124032_reservation_ledger import ReservationLedger


def validate_plan_reservations(
    plan_data: Dict,
    plan_id: str,
    registry_root: Path | str
) -> Dict:
    """Validate that all created_files have file_id reservations.
    
    Fail-closed: Missing IDs or ledger errors block execution.
    
    Args:
        plan_data: Plan data containing created_files
        plan_id: Plan identifier
        registry_root: Root directory for REGISTRY
        
    Returns:
        Dict: Validation report with status and details
        
    Exit Codes:
        0: Validation passed
        11: Missing file IDs
        12: Ledger errors
    """
    report = {
        "validator": "validate_plan_reservations",
        "plan_id": plan_id,
        "status": "UNKNOWN",
        "passed": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Check if plan has created_files
        created_files = plan_data.get("created_files", [])
        if not created_files:
            report["status"] = "PASSED_NO_FILES"
            report["passed"] = True
            report["details"] = "No created_files to validate"
            return report
        
        # Check all created_files have file_id
        missing_ids = []
        for idx, file_info in enumerate(created_files):
            if "file_id" not in file_info:
                missing_ids.append({
                    "index": idx,
                    "relative_path": file_info.get("relative_path", "UNKNOWN")
                })
        
        if missing_ids:
            report["status"] = "FAILED_MISSING_IDS"
            report["passed"] = False
            report["errors"].append(
                f"Missing file_id in {len(missing_ids)} created_file(s)"
            )
            report["missing_ids_details"] = missing_ids
            return report
        
        # Validate against reservation ledger
        ledger = ReservationLedger(plan_id, registry_root)
        
        # Check ledger exists
        if not ledger.ledger_path.exists():
            report["status"] = "FAILED_NO_LEDGER"
            report["passed"] = False
            report["errors"].append(
                f"Reservation ledger not found: {ledger.ledger_path}"
            )
            return report
        
        # Validate each file_id against ledger
        ledger_errors = []
        for file_info in created_files:
            file_id = file_info.get("file_id")
            relative_path = file_info.get("relative_path")
            
            reservation = ledger.get_reservation(file_id)
            
            if not reservation:
                ledger_errors.append({
                    "file_id": file_id,
                    "reason": "Not in ledger"
                })
                continue
            
            # Check path matches
            if reservation.relative_path != relative_path:
                ledger_errors.append({
                    "file_id": file_id,
                    "reason": f"Path mismatch: ledger={reservation.relative_path}, plan={relative_path}"
                })
        
        if ledger_errors:
            report["status"] = "FAILED_LEDGER_MISMATCH"
            report["passed"] = False
            report["errors"].append(
                f"Ledger validation failed for {len(ledger_errors)} file(s)"
            )
            report["ledger_errors"] = ledger_errors
            return report
        
        # All validations passed
        report["status"] = "PASSED"
        report["passed"] = True
        report["details"] = f"All {len(created_files)} file_id(s) validated against ledger"
        report["validated_count"] = len(created_files)
        
        return report
        
    except Exception as e:
        report["status"] = "ERROR"
        report["passed"] = False
        report["errors"].append(f"Unexpected error: {str(e)}")
        return report


def exit_code_for_report(report: Dict) -> int:
    """Convert validation report to exit code.
    
    Exit Codes:
        0: Validation passed
        11: Missing file IDs
        12: Ledger validation failed
        13: Unexpected error
    """
    status = report.get("status", "UNKNOWN")
    
    if status in ["PASSED", "PASSED_NO_FILES"]:
        return 0
    elif status == "FAILED_MISSING_IDS":
        return 11
    elif status in ["FAILED_NO_LEDGER", "FAILED_LEDGER_MISMATCH"]:
        return 12
    else:
        return 13


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate plan reservations")
    parser.add_argument("plan_file", help="Path to plan JSON file")
    parser.add_argument("--plan-id", required=True, help="Plan identifier")
    parser.add_argument("--registry-root", default=".", help="Registry root directory")
    
    args = parser.parse_args()
    
    # Load plan
    with open(args.plan_file) as f:
        plan_data = json.load(f)
    
    # Validate
    report = validate_plan_reservations(
        plan_data,
        args.plan_id,
        args.registry_root
    )
    
    # Output
    print(json.dumps(report, indent=2))
    sys.exit(exit_code_for_report(report))
