#!/usr/bin/env python3
"""NULL Coalescer (Week 2 Track A - Script 4/7)"""
import json
from P_01999000042260305005_column_loader import ColumnLoader

class NullCoalescer:
    def __init__(self):
        self.loader = ColumnLoader()
        self.loader.load_columns()
    
    def coalesce_nulls(self, record: dict) -> dict:
        """Replace NULLs with defaults where applicable."""
        coalesced = {}
        
        for col_name, value in record.items():
            if value is None:
                default = self.loader.get_default_value(col_name)
                coalesced[col_name] = default if default is not None else None
            else:
                coalesced[col_name] = value
        
        return coalesced

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    with open(args.input, encoding='utf-8') as f:
        record = json.load(f)
    
    coalescer = NullCoalescer()
    result = coalescer.coalesce_nulls(record)
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Coalesced NULLs: {args.output}")

if __name__ == "__main__":
    main()
