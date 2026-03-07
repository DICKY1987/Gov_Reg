#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-VALIDATE-PROCESS-STEPS-SCHEMA-957
"""
Process Steps Schema Validator

Validates PROCESS_STEPS_SCHEMA.yaml against the standardized schema
derived from MASTER_SPLINTER execution_plan_steps requirements.

Usage:
    python validate_process_steps_schema.py

Features:
    - Validates required fields per step
    - Checks artifact_registry references
    - Validates guardrail_checkpoint references
    - Checks operation_kind taxonomy compliance
    - Validates component references
    - Reports schema compliance metrics
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-VALIDATE-PROCESS-STEPS-SCHEMA-957

import sys
from pathlib import Path
from typing import Dict, List, Set, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class ProcessStepsValidator:
    """Validates process steps schema against MASTER_SPLINTER requirements."""

    # Required fields from MASTER_SPLINTER execution_plan_steps
    REQUIRED_FIELDS = {
        "step_id",
        "phase",
        "name",
        "responsible_component",
        "operation_kind",
        "description",
        "inputs",
        "expected_outputs",
        "requires_human_confirmation"
    }

    # Valid phases from state machine
    VALID_PHASES = {
        "INIT",
        "GAP_ANALYSIS",
        "PLANNING",
        "EXECUTION",
        "SUMMARY",
        "DONE"
    }

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_schema(self) -> bool:
        """Load YAML schema file."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = yaml.safe_load(f)
            return True
        except Exception as e:
            self.errors.append(f"Failed to load schema: {e}")
            return False

    def validate_meta(self) -> None:
        """Validate meta section."""
        if 'meta' not in self.schema:
            self.errors.append("Missing 'meta' section")
            return

        meta = self.schema['meta']
        required_meta = ['doc_id', 'version', 'last_updated']
        for field in required_meta:
            if field not in meta:
                self.errors.append(f"Missing meta.{field}")

    def validate_operation_kinds(self) -> Set[str]:
        """Validate and return valid operation_kind values."""
        if 'operation_kinds' not in self.schema:
            self.errors.append("Missing 'operation_kinds' taxonomy")
            return set()

        return set(self.schema['operation_kinds'].keys())

    def validate_components(self) -> Set[str]:
        """Validate and return valid component names."""
        if 'components' not in self.schema:
            self.errors.append("Missing 'components' registry")
            return set()

        components = set(self.schema['components'].keys())

        # Validate each component has required fields
        for comp_name, comp_data in self.schema['components'].items():
            if 'file' not in comp_data:
                self.warnings.append(f"Component '{comp_name}' missing 'file' field")
            if 'role' not in comp_data:
                self.warnings.append(f"Component '{comp_name}' missing 'role' field")

        return components

    def validate_step(self, step: Dict[str, Any], step_index: int,
                     valid_operation_kinds: Set[str],
                     valid_components: Set[str]) -> None:
        """Validate a single step."""
        step_id = step.get('step_id', f'UNKNOWN_{step_index}')

        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(step.keys())
        if missing_fields:
            self.errors.append(
                f"Step {step_id}: Missing required fields: {missing_fields}"
            )

        # Validate phase
        phase = step.get('phase')
        if phase and phase not in self.VALID_PHASES:
            self.errors.append(
                f"Step {step_id}: Invalid phase '{phase}'. "
                f"Must be one of: {self.VALID_PHASES}"
            )

        # Validate operation_kind
        operation_kind = step.get('operation_kind')
        if operation_kind and operation_kind not in valid_operation_kinds:
            self.errors.append(
                f"Step {step_id}: Invalid operation_kind '{operation_kind}'. "
                f"Must be one of: {valid_operation_kinds}"
            )

        # Validate responsible_component
        component = step.get('responsible_component')
        if component and component not in valid_components:
            self.warnings.append(
                f"Step {step_id}: Unknown component '{component}'. "
                f"Known components: {valid_components}"
            )

        # Validate inputs is a list
        inputs = step.get('inputs')
        if inputs is not None and not isinstance(inputs, list):
            self.errors.append(f"Step {step_id}: 'inputs' must be a list")

        # Validate expected_outputs is a list
        outputs = step.get('expected_outputs')
        if outputs is not None and not isinstance(outputs, list):
            self.errors.append(f"Step {step_id}: 'expected_outputs' must be a list")

        # Validate requires_human_confirmation is boolean
        human_confirm = step.get('requires_human_confirmation')
        if human_confirm is not None and not isinstance(human_confirm, bool):
            self.errors.append(
                f"Step {step_id}: 'requires_human_confirmation' must be boolean"
            )

        # Check optional but recommended fields
        if 'lens' not in step:
            self.warnings.append(f"Step {step_id}: Missing recommended field 'lens'")

        if 'automation_level' not in step:
            self.warnings.append(
                f"Step {step_id}: Missing recommended field 'automation_level'"
            )

    def validate_phases(self, valid_operation_kinds: Set[str],
                       valid_components: Set[str]) -> int:
        """Validate all phases and their steps."""
        if 'phases' not in self.schema:
            self.errors.append("Missing 'phases' section")
            return 0

        total_steps = 0
        phases = self.schema['phases']

        for phase_id, phase_data in phases.items():
            if not isinstance(phase_data, dict):
                self.errors.append(f"Phase {phase_id}: Invalid structure")
                continue

            if 'steps' not in phase_data:
                self.warnings.append(f"Phase {phase_id}: No steps defined")
                continue

            steps = phase_data['steps']
            if not isinstance(steps, list):
                self.errors.append(f"Phase {phase_id}: 'steps' must be a list")
                continue

            for step_index, step in enumerate(steps):
                self.validate_step(
                    step, step_index, valid_operation_kinds, valid_components
                )
                total_steps += 1

        return total_steps

    def validate_artifact_registry(self) -> None:
        """Validate artifact_registry references."""
        if 'artifact_registry' not in self.schema:
            self.warnings.append("Missing 'artifact_registry' section")
            return

        artifacts = self.schema['artifact_registry']

        for artifact_name, artifact_data in artifacts.items():
            if 'path' not in artifact_data:
                self.errors.append(
                    f"Artifact '{artifact_name}': Missing 'path' field"
                )

            if 'created_by' not in artifact_data:
                self.warnings.append(
                    f"Artifact '{artifact_name}': Missing 'created_by' field"
                )

    def validate_guardrail_checkpoints(self) -> None:
        """Validate guardrail_checkpoints references."""
        if 'guardrail_checkpoints' not in self.schema:
            self.warnings.append("Missing 'guardrail_checkpoints' section")
            return

        checkpoints = self.schema['guardrail_checkpoints']

        for cp_id, cp_data in checkpoints.items():
            if 'step_id' not in cp_data:
                self.errors.append(
                    f"Checkpoint '{cp_id}': Missing 'step_id' field"
                )

            if 'phase' not in cp_data:
                self.errors.append(
                    f"Checkpoint '{cp_id}': Missing 'phase' field"
                )

            if 'validation_type' not in cp_data:
                self.warnings.append(
                    f"Checkpoint '{cp_id}': Missing 'validation_type' field"
                )

    def validate(self) -> bool:
        """Run all validations."""
        if not self.load_schema():
            return False

        # Validate top-level sections
        self.validate_meta()
        valid_operation_kinds = self.validate_operation_kinds()
        valid_components = self.validate_components()

        # Validate phases and steps
        total_steps = self.validate_phases(valid_operation_kinds, valid_components)

        # Validate registries
        self.validate_artifact_registry()
        self.validate_guardrail_checkpoints()

        return len(self.errors) == 0

    def print_report(self, total_steps: int) -> None:
        """Print validation report."""
        print("=" * 80)
        print("PROCESS STEPS SCHEMA VALIDATION REPORT")
        print("=" * 80)
        print(f"Schema file: {self.schema_path}")
        print(f"Total steps validated: {total_steps}")
        print()

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   - {error}")
            print()
        else:
            print("✅ No errors found")
            print()

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   - {warning}")
            print()
        else:
            print("✅ No warnings")
            print()

        if not self.errors:
            print("🎉 Schema validation PASSED")
        else:
            print("💥 Schema validation FAILED")

        print("=" * 80)


def main():
    """Main entry point."""
    # Find schema file
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    schema_path = repo_root / "docs" / "minipipe" / "PROCESS_STEPS_SCHEMA.yaml"

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)

    # Run validation
    validator = ProcessStepsValidator(schema_path)

    # Validate and collect step count
    valid_operation_kinds = validator.validate_operation_kinds()
    valid_components = validator.validate_components()
    total_steps = validator.validate_phases(valid_operation_kinds, valid_components)

    success = validator.validate()

    # Print report
    validator.print_report(total_steps)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
