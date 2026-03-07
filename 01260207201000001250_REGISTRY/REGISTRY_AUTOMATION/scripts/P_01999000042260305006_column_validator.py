#!/usr/bin/env python3
"""Column Type Validator (Week 2 Track A - Script 2/7)"""
import json
from typing import Any, Optional
from P_01999000042260305005_column_loader import ColumnLoader

class ColumnValidator:
    def __init__(self):
        self.loader = ColumnLoader()
        self.loader.load_columns()
    
    def validate_record(self, record: dict) -> tuple[bool, list[str]]:
        """Validate all columns in a record."""
        errors = []
        
        for col_name, value in record.items():
            is_valid, error = self.loader.validate_value(col_name, value)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def validate_required_columns(self, record: dict) -> tuple[bool, list[str]]:
        """Check if all required columns are present."""
        required = self.loader.get_required_columns()
        missing = [col for col in required if col not in record]
        
        if missing:
            return False, [f"Missing required column: {col}" for col in missing]
        return True, []

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--record-json', required=True)
    args = parser.parse_args()
    
    with open(args.record_json) as f:
        record = json.load(f)
    
    validator = ColumnValidator()
    is_valid, errors = validator.validate_record(record)
    
    if is_valid:
        print("✅ Record valid")
        sys.exit(0)
    else:
        print("❌ Validation errors:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
