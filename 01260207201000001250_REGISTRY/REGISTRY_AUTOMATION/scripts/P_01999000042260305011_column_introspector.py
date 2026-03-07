#!/usr/bin/env python3
"""Column Introspector (Week 2 Track A - Script 7/7)"""
import json
from typing import Dict, Any, Set
from pathlib import Path

class ColumnIntrospector:
    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
    
    def introspect_registry(self) -> Dict[str, Any]:
        """Analyze column usage in registry."""
        with open(self.registry_path, encoding='utf-8') as f:
            registry = json.load(f)
        
        files = registry.get("files", [])
        
        # Collect all unique columns
        all_columns: Set[str] = set()
        for file_record in files:
            all_columns.update(file_record.keys())
        
        # Analyze each column
        column_stats = {}
        for col in sorted(all_columns):
            non_null_count = sum(1 for f in files if f.get(col) is not None)
            
            # Sample values
            sample_values = []
            for f in files:
                val = f.get(col)
                if val is not None and len(sample_values) < 3:
                    sample_values.append(val)
            
            # Infer type
            type_name = "unknown"
            if sample_values:
                first_val = sample_values[0]
                if isinstance(first_val, bool):
                    type_name = "boolean"
                elif isinstance(first_val, int):
                    type_name = "integer"
                elif isinstance(first_val, float):
                    type_name = "real"
                elif isinstance(first_val, str):
                    type_name = "text"
                elif isinstance(first_val, (dict, list)):
                    type_name = "json"
            
            column_stats[col] = {
                "present_count": non_null_count,
                "coverage_percent": round(100 * non_null_count / len(files), 2) if files else 0,
                "inferred_type": type_name,
                "sample_values": sample_values[:3]
            }
        
        return {
            "registry_path": str(self.registry_path),
            "total_files": len(files),
            "total_columns": len(all_columns),
            "column_stats": column_stats
        }

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    introspector = ColumnIntrospector(args.registry)
    report = introspector.introspect_registry()
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Introspection report: {args.output}")
    print(f"   Total files: {report['total_files']}")
    print(f"   Total columns: {report['total_columns']}")

if __name__ == "__main__":
    main()
