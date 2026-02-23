#!/usr/bin/env python3
"""
Validate All Schemas
Validates all JSON schema files are syntactically correct.
"""
import sys
import json
import jsonschema
from pathlib import Path


def validate_schemas(schema_dir: Path):
    """Validate all schema files"""
    results = {
        "schemas_checked": 0,
        "schemas_passed": 0,
        "schemas_failed": 0,
        "details": []
    }
    
    for schema_file in schema_dir.glob("*.json"):
        results["schemas_checked"] += 1
        
        try:
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # Verify it's a valid JSON Schema
            # (Draft 2020-12 validator will validate the schema itself)
            if "$schema" in schema:
                jsonschema.Draft202012Validator.check_schema(schema)
            
            results["schemas_passed"] += 1
            results["details"].append({
                "file": schema_file.name,
                "status": "VALID",
                "error": None
            })
            
        except json.JSONDecodeError as e:
            results["schemas_failed"] += 1
            results["details"].append({
                "file": schema_file.name,
                "status": "INVALID_JSON",
                "error": str(e)
            })
        except jsonschema.SchemaError as e:
            results["schemas_failed"] += 1
            results["details"].append({
                "file": schema_file.name,
                "status": "INVALID_SCHEMA",
                "error": str(e)
            })
        except Exception as e:
            results["schemas_failed"] += 1
            results["details"].append({
                "file": schema_file.name,
                "status": "ERROR",
                "error": str(e)
            })
    
    return results


def main():
    schema_dir = Path("schemas")
    
    if not schema_dir.exists():
        print("❌ schemas/ directory not found")
        return 1
    
    results = validate_schemas(schema_dir)
    
    print("=" * 70)
    print(f"Schema Validation Report")
    print("=" * 70)
    print()
    print(f"  Total schemas: {results['schemas_checked']}")
    print(f"  Passed: {results['schemas_passed']}")
    print(f"  Failed: {results['schemas_failed']}")
    print()
    
    for detail in results["details"]:
        if detail["status"] == "VALID":
            print(f"  ✓ {detail['file']}")
        else:
            print(f"  ✗ {detail['file']}: {detail['error']}")
    
    print()
    
    if results["schemas_failed"] == 0:
        print(f"✅ All {results['schemas_passed']} schemas valid")
        
        # Save evidence
        evidence_dir = Path(".planning_loop_state/evidence/PH-00")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        with open(evidence_dir / "schema_validation.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        return 0
    else:
        print(f"❌ {results['schemas_failed']} schema(s) failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
