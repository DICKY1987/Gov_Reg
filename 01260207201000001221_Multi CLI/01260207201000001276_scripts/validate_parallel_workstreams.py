#!/usr/bin/env python3
"""
Validate parallel workstreams configuration and write manifests.
Gates: GATE-PWE-001 (scope validate), GATE-PWE-002 (write manifest validate)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import jsonschema


class ValidationResult:
    def __init__(self, gate_id: str, passed: bool, error: str = None):
        self.gate_id = gate_id
        self.passed = passed
        self.error = error
        self.timestamp = datetime.utcnow().isoformat() + "Z"


class ParallelWorkstreamsValidator:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Any]:
        """Load all required schemas"""
        schemas = {}
        schema_files = [
            "parallel_workstreams.schema.json",
            "write_manifest.schema.json"
        ]
        
        for schema_file in schema_files:
            schema_path = self.schema_dir / schema_file
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema not found: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_name = schema_file.replace('.schema.json', '')
                schemas[schema_name] = json.load(f)
        
        return schemas

    def validate_parallel_workstreams(self, plan_data: Dict[str, Any]) -> ValidationResult:
        """GATE-PWE-001: Validate parallel workstreams configuration"""
        try:
            if 'parallel_workstreams' not in plan_data:
                return ValidationResult(
                    "GATE-PWE-001",
                    False,
                    "Missing 'parallel_workstreams' section in plan"
                )
            
            pw_config = plan_data['parallel_workstreams']
            
            # Validate against schema
            jsonschema.validate(
                instance=pw_config,
                schema=self.schemas['parallel_workstreams']
            )
            
            # Additional validations
            workstream_ids = set()
            for ws in pw_config['workstreams']:
                ws_id = ws['workstream_id']
                
                # Check for duplicate IDs
                if ws_id in workstream_ids:
                    return ValidationResult(
                        "GATE-PWE-001",
                        False,
                        f"Duplicate workstream_id: {ws_id}"
                    )
                workstream_ids.add(ws_id)
                
                # Validate dependencies reference existing workstreams
                for dep in ws.get('dependencies', []):
                    if dep not in workstream_ids and dep != ws_id:
                        # Dependency might be declared later, collect for second pass
                        pass
            
            # Second pass: validate all dependencies exist
            for ws in pw_config['workstreams']:
                for dep in ws.get('dependencies', []):
                    if dep not in workstream_ids:
                        return ValidationResult(
                            "GATE-PWE-001",
                            False,
                            f"Workstream {ws['workstream_id']} depends on non-existent workstream: {dep}"
                        )
            
            return ValidationResult("GATE-PWE-001", True)
            
        except jsonschema.ValidationError as e:
            return ValidationResult(
                "GATE-PWE-001",
                False,
                f"Schema validation failed: {e.message}"
            )
        except Exception as e:
            return ValidationResult(
                "GATE-PWE-001",
                False,
                f"Unexpected error: {str(e)}"
            )

    def validate_write_manifests(self, plan_data: Dict[str, Any], plan_dir: Path) -> ValidationResult:
        """GATE-PWE-002: Validate all write manifests"""
        try:
            if 'parallel_workstreams' not in plan_data:
                return ValidationResult(
                    "GATE-PWE-002",
                    False,
                    "Missing 'parallel_workstreams' section in plan"
                )
            
            pw_config = plan_data['parallel_workstreams']
            
            for ws in pw_config['workstreams']:
                ws_id = ws['workstream_id']
                manifest_path = plan_dir / ws['write_manifest']
                
                # Check manifest file exists
                if not manifest_path.exists():
                    return ValidationResult(
                        "GATE-PWE-002",
                        False,
                        f"Write manifest not found for {ws_id}: {manifest_path}"
                    )
                
                # Load and validate manifest
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                
                # Validate against schema
                jsonschema.validate(
                    instance=manifest_data,
                    schema=self.schemas['write_manifest']
                )
                
                # Check workstream_id matches
                if manifest_data['workstream_id'] != ws_id:
                    return ValidationResult(
                        "GATE-PWE-002",
                        False,
                        f"Manifest workstream_id mismatch: expected {ws_id}, got {manifest_data['workstream_id']}"
                    )
                
                # Validate declared_writes is not empty
                if not manifest_data.get('declared_writes'):
                    return ValidationResult(
                        "GATE-PWE-002",
                        False,
                        f"Empty declared_writes for workstream {ws_id}"
                    )
            
            return ValidationResult("GATE-PWE-002", True)
            
        except jsonschema.ValidationError as e:
            return ValidationResult(
                "GATE-PWE-002",
                False,
                f"Schema validation failed: {e.message}"
            )
        except Exception as e:
            return ValidationResult(
                "GATE-PWE-002",
                False,
                f"Unexpected error: {str(e)}"
            )

    def write_gate_result(self, result: ValidationResult, output_dir: Path):
        """Write gate result to evidence directory"""
        gate_dir = output_dir / "evidence" / "gates"
        gate_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = gate_dir / f"{result.gate_id}.result.json"
        
        result_data = {
            "gate_id": result.gate_id,
            "passed": result.passed,
            "timestamp": result.timestamp,
            "error": result.error
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Validate parallel workstreams configuration"
    )
    parser.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="Path to plan JSON file"
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Path to schemas directory (default: auto-detect)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for gate results (default: plan directory)"
    )
    
    args = parser.parse_args()
    
    # Auto-detect schema directory if not provided
    if args.schema_dir is None:
        script_dir = Path(__file__).parent
        args.schema_dir = script_dir.parent / "01260207201000001275_schemas"
    
    # Default output directory to plan directory
    if args.output_dir is None:
        args.output_dir = args.plan.parent
    
    try:
        # Load plan
        with open(args.plan, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        # Initialize validator
        validator = ParallelWorkstreamsValidator(args.schema_dir)
        
        # Run validations
        result_001 = validator.validate_parallel_workstreams(plan_data)
        validator.write_gate_result(result_001, args.output_dir)
        
        if not result_001.passed:
            print(f"GATE-PWE-001 FAILED: {result_001.error}", file=sys.stderr)
            sys.exit(1)
        
        result_002 = validator.validate_write_manifests(plan_data, args.plan.parent)
        validator.write_gate_result(result_002, args.output_dir)
        
        if not result_002.passed:
            print(f"GATE-PWE-002 FAILED: {result_002.error}", file=sys.stderr)
            sys.exit(1)
        
        print("✓ GATE-PWE-001: Parallel workstreams validation passed")
        print("✓ GATE-PWE-002: Write manifest validation passed")
        sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
