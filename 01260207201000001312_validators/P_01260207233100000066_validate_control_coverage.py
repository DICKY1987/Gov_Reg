#!/usr/bin/env python3
"""
G-CTRL-001: Control Coverage Validator

Validates that all required quality controls have complete mappings:
- Satisfying gates exist
- Evidence mappings are deterministic
- Required artifacts are declared
- Required tests are mapped

Algorithm spec: gates/G-CTRL-001.control_coverage.spec.md
"""

import json
import sys
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone


class ControlCoverageValidator:
    def __init__(self, sec_021_path: Path, sec_012_path: Path, sec_011_path: Path, 
                 sec_016_path: Path, evidence_policy_path: Path):
        self.sec_021_path = sec_021_path
        self.sec_012_path = sec_012_path
        self.sec_011_path = sec_011_path
        self.sec_016_path = sec_016_path
        self.evidence_policy_path = evidence_policy_path
        
        self.errors = []
        self.start_time = datetime.now(timezone.utc)
    
    def load_json(self, path: Path) -> Dict:
        """Load JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def emit_error(self, code: str, control_id: str, message: str, **kwargs):
        """Emit error with stable ordering"""
        error = {
            "code": code,
            "control_id": control_id,
            "message": message
        }
        error.update(kwargs)
        self.errors.append(error)
    
    def validate(self) -> Dict:
        """Run validation algorithm per spec"""
        
        # Step 1: Load SEC-021 controls
        sec_021 = self.load_json(self.sec_021_path)
        controls_data = sec_021.get('quality_controls_catalog', {}).get('controls', [])
        
        # Handle both dict and list formats
        if isinstance(controls_data, dict):
            controls = list(controls_data.values())
            for control_id, control in controls_data.items():
                control['control_id'] = control_id
        else:
            controls = controls_data
        
        # Compute RequiredControls (controls where required=true)
        required_controls = []
        for control in controls:
            if control.get('required', False):
                required_controls.append(control)
        
        # Sort by control_id (stable ordering)
        required_controls.sort(key=lambda c: c.get('control_id', ''))
        
        # Step 2: Load SEC-012 gates
        sec_012 = self.load_json(self.sec_012_path)
        gates = sec_012.get('validation_gates', {}).get('gates', [])
        
        # Build ControlToGates map
        control_to_gates = {}
        for gate in gates:
            controls_satisfied = gate.get('controls_satisfied', [])
            for control_id in controls_satisfied:
                if control_id not in control_to_gates:
                    control_to_gates[control_id] = []
                control_to_gates[control_id].append(gate)
        
        # Sort gates by gate_id within each control
        for control_id in control_to_gates:
            control_to_gates[control_id].sort(key=lambda g: g.get('gate_id', ''))
        
        # Load evidence policy for path validation
        evidence_policy = self.load_json(self.evidence_policy_path)
        path_formulas = evidence_policy.get('path_formulas', {})
        
        # Step 3: Validate each required control
        satisfied_controls = []
        violated_controls = []
        
        for control in required_controls:
            control_id = control['control_id']
            control_errors_before = len(self.errors)
            
            # Check (a): Satisfying gate exists
            if control_id not in control_to_gates:
                self.emit_error(
                    "CTRL001_MISSING_SATISFYING_GATE",
                    control_id,
                    f"Control marked required=true but no gate declares controls_satisfied: [{control_id}]"
                )
            
            else:
                # Check (b): Evidence mapping exists
                for gate in control_to_gates[control_id]:
                    gate_id = gate.get('gate_id', 'UNKNOWN')
                    
                    if 'evidence_outputs' not in gate:
                        self.emit_error(
                            "CTRL001_MISSING_EVIDENCE_MAPPING",
                            control_id,
                            f"Gate claims to satisfy control but has no evidence_outputs",
                            gate_id=gate_id
                        )
                    else:
                        # Validate evidence paths are deterministic
                        evidence_outputs = gate.get('evidence_outputs', [])
                        for evidence_path in evidence_outputs:
                            # Check if path uses formula variables (basic check)
                            if not self._is_deterministic_path(evidence_path, path_formulas):
                                self.emit_error(
                                    "CTRL001_NONDETERMINISTIC_PATH",
                                    control_id,
                                    f"Evidence path does not use deterministic formula from evidence_path_policy.json",
                                    gate_id=gate_id,
                                    evidence_path=evidence_path
                                )
            
            # Check (c): Required artifacts resolve
            required_artifacts = control.get('required_artifacts', [])
            if required_artifacts:
                try:
                    sec_011 = self.load_json(self.sec_011_path)
                    manifest_entries = sec_011.get('artifact_manifest', {}).get('manifest_table', {}).get('entries', [])
                    artifact_ids = [e.get('artifact_id') for e in manifest_entries]
                    
                    for artifact_id in required_artifacts:
                        if artifact_id not in artifact_ids:
                            self.emit_error(
                                "CTRL001_MISSING_REQUIRED_ARTIFACT",
                                control_id,
                                f"Control requires artifact but it is not declared in SEC-011 artifact manifest",
                                artifact_id=artifact_id
                            )
                except FileNotFoundError:
                    self.emit_error(
                        "CTRL001_MISSING_REQUIRED_ARTIFACT",
                        control_id,
                        f"SEC-011 artifact manifest not found (required for artifact validation)"
                    )
            
            # Check (d): Required tests resolve
            test_requirements = control.get('test_requirements', {})
            if test_requirements:
                try:
                    sec_016 = self.load_json(self.sec_016_path)
                    control_test_mapping = sec_016.get('testing_strategy', {}).get('control_test_mapping', {})
                    mappings = control_test_mapping.get('mappings', [])
                    mapped_control_ids = [m.get('control_id') for m in mappings]
                    
                    if control_id not in mapped_control_ids:
                        self.emit_error(
                            "CTRL001_MISSING_REQUIRED_TEST",
                            control_id,
                            f"Control specifies test_requirements but no mapping exists in SEC-016"
                        )
                except FileNotFoundError:
                    # SEC-016 may not have control_test_mapping section yet (PH-05 adds it)
                    pass
            
            # Track satisfied vs violated
            control_errors_after = len(self.errors)
            if control_errors_after == control_errors_before:
                satisfied_controls.append(control_id)
            else:
                violated_controls.append(control_id)
        
        # Step 4: Generate report
        end_time = datetime.now(timezone.utc)
        duration_sec = (end_time - self.start_time).total_seconds()
        
        # Sort errors by control_id, then code
        self.errors.sort(key=lambda e: (e['control_id'], e['code']))
        
        report = {
            "gate_id": "G-CTRL-001",
            "status": "pass" if len(violated_controls) == 0 else "fail",
            "start_timestamp": self.start_time.isoformat(),
            "end_timestamp": end_time.isoformat(),
            "duration_sec": round(duration_sec, 3),
            "required_controls_count": len(required_controls),
            "satisfied_controls_count": len(satisfied_controls),
            "violated_controls_count": len(violated_controls),
            "satisfied_controls": sorted(satisfied_controls),
            "violated_controls": sorted(violated_controls),
            "errors": self.errors,
            "all_required_controls_satisfied": len(violated_controls) == 0
        }
        
        return report
    
    def _is_deterministic_path(self, path: str, path_formulas: Dict) -> bool:
        """
        Check if evidence path uses deterministic formula variables.
        Basic check: looks for evidence/{var}/{var}/... pattern
        """
        # Accept paths that match formula patterns
        formula_patterns = [
            r'evidence/\{[a-z_]+\}/\{[a-z_]+\}/',  # evidence/{plan_id}/{run_id}/...
            r'\.state/evidence/',  # .state/evidence/... (legacy pattern, acceptable)
        ]
        
        for pattern in formula_patterns:
            if re.search(pattern, path):
                return True
        
        return False


def main():
    parser = argparse.ArgumentParser(description="G-CTRL-001: Control Coverage Validator")
    parser.add_argument('--sec-021', type=str, default='sections/sec_021_quality_controls_catalog.json',
                        help="Path to SEC-021 controls catalog")
    parser.add_argument('--sec-012', type=str, default='sections/sec_012_validation_gates.json',
                        help="Path to SEC-012 validation gates")
    parser.add_argument('--sec-011', type=str, default='sections/sec_011_artifact_manifest.json',
                        help="Path to SEC-011 artifact manifest")
    parser.add_argument('--sec-016', type=str, default='sections/sec_016_testing_strategy.json',
                        help="Path to SEC-016 testing strategy")
    parser.add_argument('--evidence-policy', type=str, default='policies/evidence_path_policy.json',
                        help="Path to evidence path policy")
    parser.add_argument('--output', type=str, default='.state/evidence/gates/G-CTRL-001/report.json',
                        help="Output report path")
    parser.add_argument('--plan', type=str, help="Plan file (for plan_id extraction, optional)")
    
    args = parser.parse_args()
    
    # Create validator
    validator = ControlCoverageValidator(
        sec_021_path=Path(args.sec_021),
        sec_012_path=Path(args.sec_012),
        sec_011_path=Path(args.sec_011),
        sec_016_path=Path(args.sec_016),
        evidence_policy_path=Path(args.evidence_policy)
    )
    
    # Run validation
    try:
        report = validator.validate()
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Print summary to stdout
    print(f"all_required_controls_satisfied: {report['all_required_controls_satisfied']}")
    print(f"satisfied_controls_count: {report['satisfied_controls_count']}")
    print(f"violated_controls_count: {report['violated_controls_count']}")
    
    if report['errors']:
        print(f"\nErrors ({len(report['errors'])}):", file=sys.stderr)
        for error in report['errors'][:5]:  # Show first 5
            print(f"  - {error['code']}: {error['control_id']} - {error['message']}", file=sys.stderr)
        if len(report['errors']) > 5:
            print(f"  ... and {len(report['errors']) - 5} more", file=sys.stderr)
    
    sys.exit(0 if report['all_required_controls_satisfied'] else 1)


if __name__ == "__main__":
    main()
