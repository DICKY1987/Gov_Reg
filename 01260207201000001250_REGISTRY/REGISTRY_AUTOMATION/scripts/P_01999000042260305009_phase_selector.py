#!/usr/bin/env python3
"""Phase Selector (Week 2 Track A - Script 5/7)"""
import json
from typing import Dict, Any
from P_01999000042260305005_column_loader import ColumnLoader

class PhaseSelector:
    def __init__(self):
        self.loader = ColumnLoader()
        self.loader.load_columns()
    
    def select_phase_columns(self, record: dict, phase: str) -> dict:
        """Extract only columns belonging to specified phase."""
        phase_cols = self.loader.get_columns_by_phase(phase)
        return {k: v for k, v in record.items() if k in phase_cols}
    
    def split_by_phases(self, record: dict) -> Dict[str, dict]:
        """Split record into phase-specific sub-records."""
        phases = set()
        for col_def in self.loader._columns.values():
            phase = col_def.get("phase", "UNKNOWN")
            phases.add(phase)
        
        result = {}
        for phase in phases:
            result[phase] = self.select_phase_columns(record, phase)
        
        return result

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--phase', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    with open(args.input) as f:
        record = json.load(f)
    
    selector = PhaseSelector()
    result = selector.select_phase_columns(record, args.phase)
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Selected {args.phase} columns: {len(result)} fields")

if __name__ == "__main__":
    main()
