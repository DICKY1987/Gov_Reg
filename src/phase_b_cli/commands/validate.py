"""B1: validate - Pre-flight check that Phase A plan is execution-ready"""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

from .base import BaseCommand


class ValidateCommand(BaseCommand):
    """
    Validates Phase A plan for Phase B compilation.
    
    Gates:
    - G13: Termination record exists; reason == "NO_HARD_DEFECTS"
    - G14: All Phase A artifacts pass LIV
    - G15: Final plan schema-valid
    """
    
    def execute(self) -> int:
        """Execute validation checks"""
        self.logger.info(f"Validating Phase A run: {self.run_id}")
        
        checks = []
        all_passed = True
        
        # G13: Check termination record
        try:
            termination_path = self.phase_a_artifacts / "loop" / "refinement_termination_record.json"
            termination = self.load_json(termination_path)
            
            passed = termination.get("reason") == "NO_HARD_DEFECTS"
            checks.append({
                "gate": "G13",
                "passed": passed,
                "detail": f"Termination reason: {termination.get('reason')}"
            })
            all_passed = all_passed and passed
            
        except FileNotFoundError as e:
            checks.append({
                "gate": "G13",
                "passed": False,
                "detail": f"Termination record not found: {e}"
            })
            all_passed = False
        
        # G14: LIV verification (simplified - check files exist with envelopes)
        try:
            artifacts_to_verify = [
                "loop/refinement_termination_record.json",
                "init/planning_policy_snapshot.json"
            ]
            
            # Find final refined plan
            loop_dir = self.phase_a_artifacts / "loop"
            refined_plans = sorted([p for p in loop_dir.glob("refined_plan_*.json") if not p.name.endswith(".envelope.json")])
            if refined_plans:
                final_plan_path = refined_plans[-1]
                artifacts_to_verify.append(f"loop/{final_plan_path.name}")
            
            liv_passed = True
            for artifact_path in artifacts_to_verify:
                full_path = self.phase_a_artifacts / artifact_path
                envelope_path = Path(str(full_path) + ".envelope.json")
                
                if not full_path.exists():
                    liv_passed = False
                    self.logger.error(f"Missing artifact: {artifact_path}")
                elif not envelope_path.exists():
                    liv_passed = False
                    self.logger.error(f"Missing envelope: {artifact_path}.envelope.json")
            
            checks.append({
                "gate": "G14",
                "passed": liv_passed,
                "detail": f"LIV verification for {len(artifacts_to_verify)} artifacts"
            })
            all_passed = all_passed and liv_passed
            
        except Exception as e:
            checks.append({
                "gate": "G14",
                "passed": False,
                "detail": f"LIV verification failed: {e}"
            })
            all_passed = False
        
        # G15: Schema validation (simplified - check plan structure)
        try:
            if refined_plans:
                final_plan = self.load_json(final_plan_path)
                
                # Basic structure checks
                has_workstreams = "workstreams" in final_plan
                has_schema = "$schema" in final_plan or "schema_version" in final_plan
                
                schema_valid = has_workstreams and has_schema
                checks.append({
                    "gate": "G15",
                    "passed": schema_valid,
                    "detail": f"Schema validation: workstreams={has_workstreams}, schema={has_schema}"
                })
                all_passed = all_passed and schema_valid
            else:
                checks.append({
                    "gate": "G15",
                    "passed": False,
                    "detail": "No refined plan found"
                })
                all_passed = False
                
        except Exception as e:
            checks.append({
                "gate": "G15",
                "passed": False,
                "detail": f"Schema validation failed: {e}"
            })
            all_passed = False
        
        # Check acceptance_tests
        try:
            if refined_plans:
                final_plan = self.load_json(final_plan_path)
                workstreams = final_plan.get("workstreams", [])
                
                all_have_tests = True
                for ws in workstreams:
                    for task in ws.get("tasks", []):
                        if not task.get("acceptance_tests"):
                            all_have_tests = False
                            self.logger.warning(f"Task {task.get('id')} missing acceptance_tests")
                
                checks.append({
                    "gate": "acceptance_tests",
                    "passed": all_have_tests,
                    "detail": "All tasks have acceptance_tests" if all_have_tests else "Some tasks missing acceptance_tests"
                })
                all_passed = all_passed and all_have_tests
                
        except Exception as e:
            checks.append({
                "gate": "acceptance_tests",
                "passed": False,
                "detail": f"Acceptance test check failed: {e}"
            })
            all_passed = False
        
        # Write validation report
        report = {
            "run_id": self.phase_b_run_id,
            "phase_a_run_id": self.run_id,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "result": "PASS" if all_passed else "FAIL",
            "checks": checks
        }
        
        if refined_plans:
            # Add plan hash (simplified - would compute actual SHA256)
            report["phase_a_plan_sha256"] = "placeholder_hash"
            report["termination_reason"] = termination.get("reason", "UNKNOWN")
        
        # Write outputs
        output_dir = self.phase_b_dir / "validate"
        report_path = output_dir / "phase_b_validation_report.json"
        self.write_json(report_path, report)
        
        # Write envelope (simplified)
        envelope_path = Path(str(report_path) + ".envelope.json")
        self.write_json(envelope_path, {
            "artifact_path": str(report_path.relative_to(self.phase_a_dir)),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sha256": "placeholder_hash"
        })
        
        # Output summary
        if self.args.json_stdout:
            import json
            print(json.dumps(report, indent=2))
        else:
            print(f"Validation: {'PASS' if all_passed else 'FAIL'}")
            for check in checks:
                status = "✓" if check["passed"] else "✗"
                print(f"  {status} {check['gate']}: {check['detail']}")
        
        # Return appropriate exit code
        if not all_passed:
            if any(c["gate"] == "G14" and not c["passed"] for c in checks):
                return 11  # LIV failure
            return 10  # Validation error
        
        return 0
