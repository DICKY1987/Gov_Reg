#!/usr/bin/env python3
"""GATE-012: Failure Mode Audit - Comprehensive failure mode audit"""
import argparse, json, sys, subprocess
from pathlib import Path
from datetime import datetime

# FM script mapping
FM_SCRIPTS = {
    "FM-01": "P_01260207233100000277_check_orphans.py",
    "FM-02": "P_01260207233100000279_detect_write_conflicts.py",
    "FM-03": "P_01260207233100000285_validate_handoffs.py",
    "FM-04": "P_01260207233100000274_check_dead_artifacts.py",
    "FM-05": "P_01260207233100000276_check_missing_producers.py",
    "FM-06": "P_01260207233100000278_detect_cycles.py",
    "FM-07": "P_01260207233100000275_check_dormant_flows.py",
    "FM-08": "P_01260207233100000284_validate_evidence_bundles.py",
    "FM-09": "P_01260207233100000286_validate_recovery_policies.py",
    "FM-10": "P_01260207233100000281_test_idempotency_all.py",
    "FM-11": "P_01260207233100000282_validate_detection_gates.py",
    "FM-12": "P_01260207233100000283_validate_e2e_proof_linkage.py",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-file", dest="plan_file", required=False)
    parser.add_argument("plan_file_positional", nargs="?")  # Accept positional too
    parser.add_argument("--evidence-dir", default=".state/evidence/GATE-012")
    args = parser.parse_args()

    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:
        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    wiring_dir = Path(__file__).parent

    # Run all FM checks
    fm_results = {}
    all_passed = True

    for fm_id, script_name in FM_SCRIPTS.items():
        script_path = wiring_dir / script_name
        if not script_path.exists():
            fm_results[fm_id] = {"status": "missing", "checked": False}
            all_passed = False
            continue

        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--plan-file", args.plan_file],
                capture_output=True,
                timeout=30,
            )
            passed = result.returncode == 0
            fm_results[fm_id] = {
                "status": "pass" if passed else "fail",
                "checked": True,
                "exit_code": result.returncode,
            }
            if not passed:
                all_passed = False
        except Exception as e:
            fm_results[fm_id] = {"status": "error", "checked": True, "error": str(e)}
            all_passed = False

    evidence = {
        "gate_id": "GATE-012",
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "fm_results": fm_results,
        "all_passed": all_passed,
        "passed_count": sum(1 for r in fm_results.values() if r["status"] == "pass"),
        "total_count": len(FM_SCRIPTS),
    }

    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / "failure_mode_audit.json", "w") as f:
        json.dump(evidence, f, indent=2)

    print(
        f"{'✅ PASSED' if all_passed else '❌ FAILED'}: {evidence['passed_count']}/{evidence['total_count']} FM checks passed"
    )
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
