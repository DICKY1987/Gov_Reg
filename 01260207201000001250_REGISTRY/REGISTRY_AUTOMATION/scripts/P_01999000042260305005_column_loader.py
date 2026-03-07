#!/usr/bin/env python3
"""
Column Runtime Loader (Week 2 Track A - Script 1/7)

Purpose:
  - Load COLUMN_DICTIONARY.json at runtime
  - Parse column definitions (name, type, nullable, default)
  - Provide accessor methods for column metadata
  - Cache loaded definitions

Usage:
  from P_01999000042260305005_column_loader import ColumnLoader
  
  loader = ColumnLoader()
  columns = loader.load_columns()
  col_def = loader.get_column("py_canonical_text_hash")
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List


class ColumnLoader:
    """Runtime loader for column definitions."""
    
    def __init__(self, dictionary_path: Optional[Path] = None):
        """
        Initialize column loader.
        
        Args:
            dictionary_path: Path to COLUMN_DICTIONARY.json
                           If None, uses default location
        """
        if dictionary_path is None:
            # Default: relative to this script
            script_dir = Path(__file__).parent
            self.dictionary_path = (script_dir / "../../01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json").resolve()
        else:
            self.dictionary_path = dictionary_path
        
        self._columns: Optional[Dict[str, Any]] = None
        self._columns_by_phase: Optional[Dict[str, List[str]]] = None
    
    def load_columns(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load column definitions from dictionary.
        
        Args:
            force_reload: If True, reload even if already cached
        
        Returns:
            Dict mapping column_name -> column_definition
        """
        if self._columns is not None and not force_reload:
            return self._columns
        
        if not self.dictionary_path.exists():
            raise FileNotFoundError(f"Column dictionary not found: {self.dictionary_path}")
        
        with open(self.dictionary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract columns array
        columns_array = data.get("columns", [])
        
        # Convert to dict keyed by column_name
        self._columns = {}
        for col_def in columns_array:
            name = col_def.get("column_name")
            if name:
                self._columns[name] = col_def
        
        # Build phase index
        self._columns_by_phase = {}
        for name, col_def in self._columns.items():
            phase = col_def.get("phase", "UNKNOWN")
            if phase not in self._columns_by_phase:
                self._columns_by_phase[phase] = []
            self._columns_by_phase[phase].append(name)
        
        return self._columns
    
    def get_column(self, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Get column definition by name.
        
        Args:
            column_name: Name of column
        
        Returns:
            Column definition dict or None if not found
        """
        if self._columns is None:
            self.load_columns()
        
        return self._columns.get(column_name)
    
    def get_columns_by_phase(self, phase: str) -> List[str]:
        """
        Get list of column names for a phase.
        
        Args:
            phase: Phase identifier (e.g., "PHASE_A", "PHASE_B")
        
        Returns:
            List of column names
        """
        if self._columns_by_phase is None:
            self.load_columns()
        
        return self._columns_by_phase.get(phase, [])
    
    def get_column_type(self, column_name: str) -> Optional[str]:
        """Get data type for column."""
        col_def = self.get_column(column_name)
        return col_def.get("data_type") if col_def else None
    
    def is_nullable(self, column_name: str) -> bool:
        """Check if column is nullable."""
        col_def = self.get_column(column_name)
        if col_def is None:
            return False
        return col_def.get("nullable", False)
    
    def get_default_value(self, column_name: str) -> Any:
        """Get default value for column."""
        col_def = self.get_column(column_name)
        if col_def is None:
            return None
        return col_def.get("default_value")
    
    def validate_value(self, column_name: str, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against column definition.
        
        Args:
            column_name: Column name
            value: Value to validate
        
        Returns:
            (is_valid, error_message)
        """
        col_def = self.get_column(column_name)
        
        if col_def is None:
            return False, f"Column '{column_name}' not found in dictionary"
        
        # Check nullable
        if value is None:
            if not col_def.get("nullable", False):
                return False, f"Column '{column_name}' does not allow NULL"
            return True, None
        
        # Check type
        data_type = col_def.get("data_type")
        
        if data_type == "TEXT":
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"
        
        elif data_type == "INTEGER":
            if not isinstance(value, int):
                return False, f"Expected int, got {type(value).__name__}"
        
        elif data_type == "REAL":
            if not isinstance(value, (int, float)):
                return False, f"Expected number, got {type(value).__name__}"
        
        elif data_type == "BOOLEAN":
            if not isinstance(value, bool):
                return False, f"Expected bool, got {type(value).__name__}"
        
        elif data_type == "JSON":
            # JSON can be dict, list, or primitive
            if not isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return False, f"Invalid JSON type: {type(value).__name__}"
        
        return True, None
    
    def get_all_columns(self) -> List[str]:
        """Get list of all column names."""
        if self._columns is None:
            self.load_columns()
        return list(self._columns.keys())
    
    def get_required_columns(self) -> List[str]:
        """Get list of required (non-nullable) columns."""
        if self._columns is None:
            self.load_columns()
        
        required = []
        for name, col_def in self._columns.items():
            if not col_def.get("nullable", False):
                required.append(name)
        
        return required


def main():
    """CLI for testing column loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Column Runtime Loader')
    parser.add_argument('--list-phases', action='store_true',
                       help='List all phases')
    parser.add_argument('--phase', help='List columns for phase')
    parser.add_argument('--column', help='Show definition for column')
    parser.add_argument('--validate', nargs=2, metavar=('COLUMN', 'VALUE'),
                       help='Validate a value')
    
    args = parser.parse_args()
    
    loader = ColumnLoader()
    loader.load_columns()
    
    if args.list_phases:
        phases = sorted(set(
            col_def.get("phase", "UNKNOWN")
            for col_def in loader._columns.values()
        ))
        print("Phases:")
        for phase in phases:
            cols = loader.get_columns_by_phase(phase)
            print(f"  {phase}: {len(cols)} columns")
    
    elif args.phase:
        cols = loader.get_columns_by_phase(args.phase)
        print(f"Columns in {args.phase}:")
        for col in sorted(cols):
            print(f"  {col}")
    
    elif args.column:
        col_def = loader.get_column(args.column)
        if col_def:
            print(json.dumps(col_def, indent=2))
        else:
            print(f"Column '{args.column}' not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.validate:
        column_name, value_str = args.validate
        
        # Parse value
        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            value = value_str
        
        is_valid, error = loader.validate_value(column_name, value)
        
        if is_valid:
            print(f"✅ Valid: {column_name} = {value}")
        else:
            print(f"❌ Invalid: {error}")
            sys.exit(1)
    
    else:
        print(f"Loaded {len(loader.get_all_columns())} columns")
        print(f"Required: {len(loader.get_required_columns())} columns")


if __name__ == "__main__":
    main()
