#!/usr/bin/env python3
"""Column Default Injector (Week 2 Track A - Script 3/7)"""
import json
from P_01999000042260305005_column_loader import ColumnLoader

class DefaultInjector:
    def __init__(self):
        self.loader = ColumnLoader()
        self.loader.load_columns()
    
    def inject_defaults(self, record: dict) -> dict:
        """Inject default values for missing columns."""
        injected = record.copy()
        
        for col_name in self.loader.get_all_columns():
            if col_name not in injected:
                default = self.loader.get_default_value(col_name)
                if default is not None:
                    injected[col_name] = default
        
        return injected

def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    with open(args.input) as f:
        record = json.load(f)
    
    injector = DefaultInjector()
    result = injector.inject_defaults(record)
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Injected defaults: {args.output}")

if __name__ == "__main__":
    main()
