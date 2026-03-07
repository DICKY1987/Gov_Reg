#!/usr/bin/env python3
"""Missing Column Reporter (Week 2 Track A - Script 6/7)"""
import json
from typing import List, Dict, Any
from P_01999000042260305005_column_loader import ColumnLoader

class MissingColumnReporter:
    def __init__(self):
        self.loader = ColumnLoader()
        self.loader.load_columns()
    
    def find_missing_columns(self, record: dict) -> List[str]:
        """Find columns defined in dictionary but missing from record."""
        all_cols = set(self.loader.get_all_columns())
        present_cols = set(record.keys())
        return sorted(all_cols - present_cols)
    
    def generate_report(self, records: List[dict]) -> Dict[str, Any]:
        """Generate missing column report for multiple records."""
        column_presence = {}
        
        for col in self.loader.get_all_columns():
            column_presence[col] = sum(1 for r in records if col in r)
        
        total = len(records)
        missing_report = []
        
        for col, count in sorted(column_presence.items(), key=lambda x: x[1]):
            if count < total:
                missing_report.append({
                    "column": col,
                    "present_count": count,
                    "missing_count": total - count,
                    "coverage_percent": round(100 * count / total, 2) if total > 0 else 0
                })
        
        return {
            "total_records": total,
            "total_columns": len(column_presence),
            "missing_columns": missing_report
        }

def main():
    import sys
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--registry', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    with open(args.registry, encoding='utf-8') as f:
        registry = json.load(f)
    
    files = registry.get("files", [])
    
    reporter = MissingColumnReporter()
    report = reporter.generate_report(files)
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Missing column report: {args.output}")
    print(f"   Total records: {report['total_records']}")
    print(f"   Columns with gaps: {len(report['missing_columns'])}")

if __name__ == "__main__":
    main()
