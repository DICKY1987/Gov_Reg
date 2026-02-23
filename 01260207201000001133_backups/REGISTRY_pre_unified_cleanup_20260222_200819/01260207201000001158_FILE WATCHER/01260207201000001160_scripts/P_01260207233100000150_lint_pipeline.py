#!/usr/bin/env python3
"""
Pipeline Linter - Enforce Action Taxonomy Ordering Constraints
Validates step pipelines beyond what JSON Schema can enforce.

Usage:
    python lint_pipeline.py <pipeline_file.yaml>
    
Exit Codes:
    0: All checks passed
    1: Validation errors found
    2: File not found / parse error
"""

import sys
import json
import yaml
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Canonical 9-class action taxonomy"""
    ARTIFACT_RESOLUTION = "artifact_resolution"
    REGISTRY_QUERY = "registry_query"
    TEMPLATE_INJECTION = "template_injection"
    VALIDATION = "validation"
    COMPUTATION = "computation"
    EXTERNAL_EXECUTION = "external_execution"
    WRITE_COMMIT = "write_commit"
    STATE_TRANSITION = "state_transition"
    LEDGER_EMISSION = "ledger_emission"


class SideEffects(Enum):
    """Side effect classification"""
    NONE = "none"
    APPEND_ONLY = "append_only"
    MUTATING = "mutating"


@dataclass
class ValidationError:
    """Structured validation error"""
    rule: str
    message: str
    step_id: str = None
    remediation: str = None
    
    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "message": self.message,
            "step_id": self.step_id,
            "remediation": self.remediation
        }


class PipelineLinter:
    """Enforces ordering and semantic constraints on step pipelines"""
    
    # Allowed transitions (directed graph)
    ALLOWED_TRANSITIONS = {
        ActionType.ARTIFACT_RESOLUTION: {
            ActionType.REGISTRY_QUERY,
            ActionType.VALIDATION,
            ActionType.COMPUTATION
        },
        ActionType.REGISTRY_QUERY: {
            ActionType.VALIDATION,
            ActionType.COMPUTATION,
            ActionType.TEMPLATE_INJECTION
        },
        ActionType.TEMPLATE_INJECTION: {
            ActionType.VALIDATION,
            ActionType.COMPUTATION
        },
        ActionType.VALIDATION: {
            ActionType.COMPUTATION,
            ActionType.REGISTRY_QUERY,
            ActionType.LEDGER_EMISSION  # On validation failure
        },
        ActionType.COMPUTATION: {
            ActionType.WRITE_COMMIT,
            ActionType.EXTERNAL_EXECUTION,
            ActionType.STATE_TRANSITION,
            ActionType.LEDGER_EMISSION
        },
        ActionType.EXTERNAL_EXECUTION: {
            ActionType.WRITE_COMMIT,
            ActionType.STATE_TRANSITION,
            ActionType.LEDGER_EMISSION
        },
        ActionType.WRITE_COMMIT: {
            ActionType.STATE_TRANSITION,
            ActionType.LEDGER_EMISSION
        },
        ActionType.STATE_TRANSITION: {
            ActionType.LEDGER_EMISSION
        },
        ActionType.LEDGER_EMISSION: set()  # Must be terminal
    }
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def lint(self, pipeline: dict) -> bool:
        """Run all validation rules. Returns True if all pass."""
        self._validate_structure(pipeline)
        
        if "steps" not in pipeline:
            return False
        
        steps = pipeline["steps"]
        
        self._validate_step_ids(steps)
        self._validate_final_step(steps)
        self._validate_ordering(steps)
        self._validate_side_effects_ordering(steps)
        self._validate_mutating_steps(steps)
        self._validate_validation_steps(steps)
        self._validate_computation_steps(steps)
        
        return len(self.errors) == 0
    
    def _validate_structure(self, pipeline: dict):
        """Check basic structure requirements"""
        required_fields = ["version", "pipeline_id", "steps"]
        for field in required_fields:
            if field not in pipeline:
                self.errors.append(ValidationError(
                    rule="STRUCTURE",
                    message=f"Missing required field: {field}",
                    remediation="Add field to pipeline definition"
                ))
    
    def _validate_step_ids(self, steps: List[dict]):
        """Check step IDs are unique and follow naming convention"""
        seen_ids = set()
        for step in steps:
            step_id = step.get("step_id")
            if not step_id:
                self.errors.append(ValidationError(
                    rule="STEP_ID",
                    message="Step missing step_id",
                    remediation="Add step_id field matching pattern /^S[0-9]{2,3}$/"
                ))
                continue
            
            if step_id in seen_ids:
                self.errors.append(ValidationError(
                    rule="STEP_ID_UNIQUE",
                    message=f"Duplicate step_id: {step_id}",
                    step_id=step_id,
                    remediation="Use unique step IDs"
                ))
            
            seen_ids.add(step_id)
    
    def _validate_final_step(self, steps: List[dict]):
        """Ensure pipeline ends with ledger_emission"""
        if not steps:
            self.errors.append(ValidationError(
                rule="FINAL_STEP",
                message="Pipeline has no steps",
                remediation="Add at least one step"
            ))
            return
        
        last_step = steps[-1]
        last_action = last_step.get("action")
        
        if last_action != ActionType.LEDGER_EMISSION.value:
            self.errors.append(ValidationError(
                rule="FINAL_STEP",
                message=f"Pipeline must end with ledger_emission, got: {last_action}",
                step_id=last_step.get("step_id"),
                remediation="Add ledger_emission as final step"
            ))
    
    def _validate_ordering(self, steps: List[dict]):
        """Validate action ordering follows allowed transitions"""
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            current_action = current_step.get("action")
            next_action = next_step.get("action")
            
            if not current_action or not next_action:
                continue
            
            try:
                current_enum = ActionType(current_action)
                next_enum = ActionType(next_action)
            except ValueError:
                continue  # Invalid action, will be caught by JSON Schema
            
            allowed = self.ALLOWED_TRANSITIONS.get(current_enum, set())
            
            if next_enum not in allowed:
                self.errors.append(ValidationError(
                    rule="ORDERING",
                    message=f"Invalid transition: {current_action} → {next_action}",
                    step_id=current_step.get("step_id"),
                    remediation=f"Allowed transitions from {current_action}: {[a.value for a in allowed]}"
                ))
    
    def _validate_side_effects_ordering(self, steps: List[dict]):
        """Mutating steps must come after non-mutating steps"""
        seen_mutating = False
        
        for step in steps:
            side_effects = step.get("side_effects")
            step_id = step.get("step_id")
            
            if side_effects == SideEffects.MUTATING.value:
                seen_mutating = True
            elif side_effects == SideEffects.NONE.value and seen_mutating:
                self.errors.append(ValidationError(
                    rule="SIDE_EFFECTS_ORDERING",
                    message=f"Non-mutating step after mutating step: {step_id}",
                    step_id=step_id,
                    remediation="Move non-mutating steps (validation, computation) before mutating steps"
                ))
    
    def _validate_mutating_steps(self, steps: List[dict]):
        """write_commit and external_execution must have rollback + mechanics"""
        mutating_actions = {
            ActionType.WRITE_COMMIT.value,
            ActionType.EXTERNAL_EXECUTION.value
        }
        
        for step in steps:
            action = step.get("action")
            step_id = step.get("step_id")
            
            if action not in mutating_actions:
                continue
            
            # Check rollback
            if "rollback" not in step:
                self.errors.append(ValidationError(
                    rule="MUTATING_ROLLBACK",
                    message=f"Mutating action {action} missing rollback definition",
                    step_id=step_id,
                    remediation="Add rollback field with strategy (snapshot_restore or reverse_ops)"
                ))
            
            # Check mechanics (required for write_commit)
            if action == ActionType.WRITE_COMMIT.value and "mechanics" not in step:
                self.errors.append(ValidationError(
                    rule="WRITE_COMMIT_MECHANICS",
                    message="write_commit step missing mechanics (lock + stability_gate)",
                    step_id=step_id,
                    remediation="Add mechanics field with lock and stability_gate"
                ))
    
    def _validate_validation_steps(self, steps: List[dict]):
        """validation steps must support fast_feedback"""
        for step in steps:
            if step.get("action") != ActionType.VALIDATION.value:
                continue
            
            step_id = step.get("step_id")
            
            if "fast_feedback" not in step:
                self.errors.append(ValidationError(
                    rule="VALIDATION_FAST_FEEDBACK",
                    message="validation step missing fast_feedback field",
                    step_id=step_id,
                    remediation="Add fast_feedback: {required: true, mcp_tool_name: '...'}"
                ))
    
    def _validate_computation_steps(self, steps: List[dict]):
        """computation steps should expose MCP tool (warning, not error)"""
        for step in steps:
            if step.get("action") != ActionType.COMPUTATION.value:
                continue
            
            step_id = step.get("step_id")
            
            if "mcp" not in step:
                # This is a warning, not an error
                print(f"⚠️  WARNING: computation step {step_id} should expose MCP tool interface")
    
    def report(self) -> dict:
        """Generate structured error report"""
        return {
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "errors": [e.to_dict() for e in self.errors]
        }


def main():
    if len(sys.argv) != 2:
        print("Usage: python lint_pipeline.py <pipeline_file.yaml>")
        sys.exit(2)
    
    pipeline_path = Path(sys.argv[1])
    
    if not pipeline_path.exists():
        print(f"❌ File not found: {pipeline_path}")
        sys.exit(2)
    
    try:
        with open(pipeline_path) as f:
            if pipeline_path.suffix == ".json":
                pipeline = json.load(f)
            else:
                pipeline = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to parse file: {e}")
        sys.exit(2)
    
    linter = PipelineLinter()
    valid = linter.lint(pipeline)
    report = linter.report()
    
    if valid:
        print(f"✅ Pipeline validation PASSED: {pipeline_path}")
        print(json.dumps(report, indent=2))
        sys.exit(0)
    else:
        print(f"❌ Pipeline validation FAILED: {pipeline_path}")
        print(json.dumps(report, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
