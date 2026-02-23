#!/usr/bin/env python3
"""
Command Spec Validator

Validates that all gates/tools use structured command specs (no free-form strings).
Checks sections for command fields and ensures they conform to command_spec.schema.json.

Usage:
    python validators/validate_command_spec.py --sections-dir sections/
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple


def load_command_spec_schema(schema_path: Path) -> Dict:
    """Load command_spec.schema.json"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_command_field(data: Any, path: str, violations: List[Dict]) -> None:
    """Recursively check for 'command' fields and validate structure"""
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if key == "command":
                # Found a command field - check if it's a string (violation)
                if isinstance(value, str):
                    violations.append({
                        "path": current_path,
                        "type": "free_form_command",
                        "value": value[:100] + "..." if len(value) > 100 else value,
                        "expected": "Structured command object with 'exe' and 'args' fields"
                    })
                elif isinstance(value, dict):
                    # Check if it has required fields
                    if 'exe' not in value or 'args' not in value:
                        violations.append({
                            "path": current_path,
                            "type": "incomplete_command_spec",
                            "value": value,
                            "expected": "Must have 'exe' and 'args' fields"
                        })
                    elif not isinstance(value.get('args'), list):
                        violations.append({
                            "path": current_path,
                            "type": "invalid_args_type",
                            "value": value,
                            "expected": "'args' must be an array of strings"
                        })
            else:
                # Recurse into nested structures
                check_command_field(value, current_path, violations)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            check_command_field(item, current_path, violations)


def validate_section_file(section_path: Path) -> Tuple[bool, List[Dict]]:
    """Validate a single section file for command spec compliance"""
    violations = []
    
    try:
        with open(section_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check all command fields in the section
        check_command_field(data, "", violations)
        
        return len(violations) == 0, violations
    
    except json.JSONDecodeError as e:
        return False, [{"path": str(section_path), "type": "json_parse_error", "error": str(e)}]
    except Exception as e:
        return False, [{"path": str(section_path), "type": "validation_error", "error": str(e)}]


def main():
    parser = argparse.ArgumentParser(description="Validate command spec compliance in sections")
    parser.add_argument('--sections-dir', type=str, required=True, help="Path to sections directory")
    parser.add_argument('--schema', type=str, default='schemas/command_spec.schema.json', 
                        help="Path to command_spec.schema.json")
    parser.add_argument('--output', type=str, help="Output JSON file for results")
    
    args = parser.parse_args()
    
    sections_dir = Path(args.sections_dir)
    schema_path = Path(args.schema)
    
    if not sections_dir.exists():
        print(f"Error: Sections directory not found: {sections_dir}", file=sys.stderr)
        sys.exit(2)
    
    # Load schema (for reference, not used for validation yet)
    if schema_path.exists():
        schema = load_command_spec_schema(schema_path)
    else:
        schema = None
    
    # Find all sec_*.json files
    section_files = sorted(sections_dir.glob("sec_*.json"))
    
    if not section_files:
        print(f"Warning: No sec_*.json files found in {sections_dir}", file=sys.stderr)
    
    all_violations = []
    files_checked = 0
    files_with_violations = 0
    
    for section_file in section_files:
        files_checked += 1
        is_valid, violations = validate_section_file(section_file)
        
        if not is_valid:
            files_with_violations += 1
            for violation in violations:
                violation['file'] = str(section_file.name)
                all_violations.append(violation)
    
    # Prepare results
    results = {
        "all_commands_structured": len(all_violations) == 0,
        "files_checked": files_checked,
        "files_with_violations": files_with_violations,
        "total_violations": len(all_violations),
        "violations": sorted(all_violations, key=lambda x: (x.get('file', ''), x.get('path', '')))
    }
    
    # Output results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    
    # Print summary
    print(f"all_commands_structured: {results['all_commands_structured']}")
    print(f"files_checked: {results['files_checked']}")
    print(f"files_with_violations: {results['files_with_violations']}")
    print(f"total_violations: {results['total_violations']}")
    
    if all_violations:
        print("\nViolations found:", file=sys.stderr)
        for v in all_violations[:5]:  # Show first 5
            print(f"  - {v['file']}: {v['path']} ({v['type']})", file=sys.stderr)
        if len(all_violations) > 5:
            print(f"  ... and {len(all_violations) - 5} more", file=sys.stderr)
    
    sys.exit(0 if results['all_commands_structured'] else 1)


if __name__ == "__main__":
    main()
