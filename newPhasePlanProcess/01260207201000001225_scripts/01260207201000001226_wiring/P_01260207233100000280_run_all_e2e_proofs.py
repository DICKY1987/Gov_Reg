#!/usr/bin/env python3
"""GATE-013: Run All E2E Proofs - Final execution of all E2E proofs"""
import argparse, json, sys, subprocess
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--evidence-dir', default='.state/evidence/GATE-013')
    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    wiring_dir = Path(__file__).parent
    current_script = Path(__file__).name
    fm_scripts = sorted(wiring_dir.glob('*.py'))

    results = {}
    for script in fm_scripts:
        if script.name.startswith('_') or script.name == current_script:
            continue
        try:
            result = subprocess.run([sys.executable, str(script), args.plan_file],
                                  capture_output=True, timeout=30)
            results[script.name] = {
                'exit_code': result.returncode,
                'passed': result.returncode == 0
            }
        except Exception as e:
            results[script.name] = {'error': str(e), 'passed': False}

    evidence = {
        'gate_id': 'GATE-013',
        'validated_at': datetime.utcnow().isoformat() + 'Z',
        'total_proofs': len(results),
        'passed': sum(1 for r in results.values() if r.get('passed')),
        'results': results
    }

    Path(args.evidence_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.evidence_dir) / 'e2e_proof_results.json', 'w') as f:
        json.dump(evidence, f, indent=2)

    all_passed = all(r.get('passed') for r in results.values())
    print(f"{'✅ PASSED' if all_passed else '❌ FAILED'}: {evidence['passed']}/{evidence['total_proofs']} proofs passed")
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
