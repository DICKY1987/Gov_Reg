#!/usr/bin/env python3
"""
Phase A Column Transformation Layer (Week 1 Step 1.4)

Purpose:
  - Transform raw py_* columns from Phase A analyzers into registry format
  - Apply column mapping rules from COLUMN_DICTIONARY
  - Handle data type conversions
  - Validate output against schema

Usage:
  python P_01999000042260305002_phase_a_transformer.py --input ANALYSIS.json --output TRANSFORMED.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Column mappings: analyzer_output -> registry_column
PHASE_A_COLUMN_MAP = {
    # Text normalization
    "py_canonical_text_hash": "py_canonical_text_hash",
    "py_encoding_detected": "py_encoding_detected",
    "py_newline_style": "py_newline_style",
    
    # Component extraction
    "py_defs_classes_count": "py_defs_classes_count",
    "py_defs_functions_count": "py_defs_functions_count",
    "py_component_count": "py_component_count",
    "py_components_list": "py_components_list",
    "py_defs_public_api_hash": "py_defs_public_api_hash",
    
    # Dependencies
    "py_imports_list": "py_imports_list",
    "py_imports_hash": "py_imports_hash",
    "py_stdlib_imports_count": "py_stdlib_imports_count",
    "py_external_imports_count": "py_external_imports_count",
    
    # AST
    "py_ast_dump_hash": "py_ast_dump_hash",
    "py_ast_parse_ok": "py_ast_parse_ok",
    
    # I/O Surface
    "py_reads_filesystem": "py_reads_filesystem",
    "py_writes_filesystem": "py_writes_filesystem",
    "py_network_io": "py_network_io",
    
    # Capabilities
    "py_capability_tags": "py_capability_tags",
    "py_capability_facts_hash": "py_capability_facts_hash",
    
    # Complexity
    "py_complexity_cyclomatic": "py_complexity_cyclomatic",
    "py_max_complexity": "py_max_complexity",
    
    # Tests
    "py_tests_executed": "py_tests_executed",
    "py_pytest_exit_code": "py_pytest_exit_code",
    "py_test_pass_count": "py_test_pass_count",
    "py_test_fail_count": "py_test_fail_count",
    "py_coverage_percent": "py_coverage_percent",
    
    # Lint
    "py_static_issues_count": "py_static_issues_count",
    "py_lint_score": "py_lint_score",
}


class PhaseATransformer:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def transform_value(self, key: str, value: Any) -> Any:
        """Transform value based on expected type."""
        # Handle None
        if value is None:
            return None
        
        # Count columns should be integers
        if key.endswith("_count"):
            try:
                return int(value)
            except (ValueError, TypeError):
                self.warnings.append(f"Could not convert {key} to int: {value}")
                return 0
        
        # Percent columns should be floats
        if key.endswith("_percent"):
            try:
                return float(value)
            except (ValueError, TypeError):
                self.warnings.append(f"Could not convert {key} to float: {value}")
                return 0.0
        
        # Boolean columns
        if key.endswith("_ok") or key.startswith("py_tests_") or key.startswith("py_reads_") or key.startswith("py_writes_") or key.startswith("py_network_"):
            if isinstance(value, bool):
                return value
            # Convert string to bool
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        
        # List columns
        if key.endswith("_list") or key.endswith("_tags"):
            if isinstance(value, list):
                return value
            self.warnings.append(f"Expected list for {key}, got {type(value).__name__}")
            return []
        
        # Hash columns should be strings
        if key.endswith("_hash"):
            return str(value) if value is not None else None
        
        # Default: return as-is
        return value
    
    def transform_phase_a_output(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Phase A analyzer output to registry format."""
        transformed = {}
        
        for analyzer_key, registry_key in PHASE_A_COLUMN_MAP.items():
            if analyzer_key in analysis:
                raw_value = analysis[analyzer_key]
                transformed_value = self.transform_value(registry_key, raw_value)
                transformed[registry_key] = transformed_value
        
        return transformed
    
    def validate_transformed(self, transformed: Dict[str, Any]) -> bool:
        """Basic validation of transformed data."""
        required_fields = [
            "py_canonical_text_hash",
            "py_ast_parse_ok",
        ]
        
        missing = [f for f in required_fields if f not in transformed]
        if missing:
            self.errors.append(f"Missing required fields: {missing}")
            return False
        
        return True
    
    def transform_file(self, input_path: Path, output_path: Path) -> int:
        """Transform a single analysis file."""
        try:
            print(f"Loading: {input_path}")
            with open(input_path, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
            
            print("Transforming...")
            transformed = self.transform_phase_a_output(analysis)
            
            print("Validating...")
            if not self.validate_transformed(transformed):
                print(f"❌ Validation failed")
                return 1
            
            # Add metadata
            output = {
                "transformed_at": datetime.utcnow().isoformat() + "Z",
                "transformer": "P_01999000042260305002_phase_a_transformer.py",
                "source_file": str(input_path),
                "data": transformed
            }
            
            print(f"Writing: {output_path}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} warnings:")
                for w in self.warnings[:5]:
                    print(f"  • {w}")
                if len(self.warnings) > 5:
                    print(f"  ... and {len(self.warnings) - 5} more")
            
            print("✅ Transformation complete")
            return 0
            
        except FileNotFoundError:
            print(f"❌ Error: Input file not found: {input_path}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 2


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase A Column Transformer')
    parser.add_argument('--input', required=True, help='Input analysis JSON')
    parser.add_argument('--output', required=True, help='Output transformed JSON')
    
    args = parser.parse_args()
    
    transformer = PhaseATransformer()
    exit_code = transformer.transform_file(Path(args.input), Path(args.output))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
