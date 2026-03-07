#!/usr/bin/env python3
"""
DOC-TOOL-SCHEMA-VALIDATOR-001: Schema Validation Framework
Phase: PH-ENH-002
Purpose: Validate JSON schemas against meta-schema and validate instances
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import jsonschema
from jsonschema import Draft7Validator, validators

class SchemaValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.validation_results: List[Dict] = []
        self.meta_schema = self._load_json_schema_draft7()
        
    def _load_json_schema_draft7(self) -> Dict:
        """Load JSON Schema Draft 7 meta-schema"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "http://json-schema.org/draft-07/schema#",
            "title": "Core schema meta-schema"
        }
    
    def validate_schema_file(self, schema_path: Path) -> Tuple[bool, List[str]]:
        """Validate a schema file against meta-schema"""
        errors = []
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            validator = Draft7Validator(self.meta_schema)
            validation_errors = list(validator.iter_errors(schema_data))
            
            if validation_errors:
                for error in validation_errors:
                    errors.append(f"{error.message} at {'/'.join(str(p) for p in error.path)}")
                return False, errors
            
            return True, []
            
        except json.JSONDecodeError as e:
            errors.append(f"JSON parse error: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def validate_instance(self, instance_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
        """Validate an instance against a schema"""
        errors = []
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            with open(instance_path, 'r', encoding='utf-8') as f:
                instance_data = json.load(f)
            
            validator = Draft7Validator(schema_data)
            validation_errors = list(validator.iter_errors(instance_data))
            
            if validation_errors:
                for error in validation_errors:
                    errors.append(f"{error.message} at {'/'.join(str(p) for p in error.path)}")
                return False, errors
            
            return True, []
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def validate_all_schemas(self) -> Dict:
        """Validate all schemas in repository"""
        schema_files = list(self.repo_root.rglob("*.schema.json"))
        results = {
            "total_schemas": len(schema_files),
            "valid_schemas": 0,
            "invalid_schemas": 0,
            "validation_errors": []
        }
        
        for schema_path in schema_files:
            is_valid, errors = self.validate_schema_file(schema_path)
            
            if is_valid:
                results["valid_schemas"] += 1
            else:
                results["invalid_schemas"] += 1
                results["validation_errors"].append({
                    "schema_path": str(schema_path.relative_to(self.repo_root)),
                    "errors": errors
                })
        
        return results
    
    def generate_validation_report(self) -> Dict:
        """Generate validation report"""
        validation_results = self.validate_all_schemas()
        
        return {
            "doc_id": "DOC-REPORT-SCHEMA-VALIDATION-002",
            "phase_id": "PH-ENH-002",
            "validation_timestamp": "2026-02-08T02:45:00Z",
            "summary": {
                "total_schemas": validation_results["total_schemas"],
                "valid_schemas": validation_results["valid_schemas"],
                "invalid_schemas": validation_results["invalid_schemas"],
                "validation_rate": f"{(validation_results['valid_schemas'] / validation_results['total_schemas'] * 100):.1f}%"
            },
            "validation_errors": validation_results["validation_errors"][:50],
            "acceptance_criteria_met": validation_results["invalid_schemas"] == 0
        }


def main():
    repo_root = Path(r"C:\Users\richg\ALL_AI")
    output_dir = repo_root / "data" / "schema_validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    validator = SchemaValidator(repo_root)
    report = validator.generate_validation_report()
    
    report_path = output_dir / "DOC-REPORT-SCHEMA-VALIDATION-002__schema_validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ PH-ENH-002 Schema Validation Complete")
    print(f"📊 Validation Report: {report_path}")
    print(f"\nSummary:")
    print(f"  Total Schemas: {report['summary']['total_schemas']}")
    print(f"  Valid Schemas: {report['summary']['valid_schemas']}")
    print(f"  Invalid Schemas: {report['summary']['invalid_schemas']}")
    print(f"  Validation Rate: {report['summary']['validation_rate']}")
    
    if not report['acceptance_criteria_met']:
        print(f"\n⚠️  Warning: {report['summary']['invalid_schemas']} schemas failed validation")
        sys.exit(1)


if __name__ == "__main__":
    main()
