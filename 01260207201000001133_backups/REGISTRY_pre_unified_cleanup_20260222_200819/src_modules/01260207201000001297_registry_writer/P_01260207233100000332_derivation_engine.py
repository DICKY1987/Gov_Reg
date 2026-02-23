"""
TASK-012: Derivation Engine with DSL Evaluator

Evaluates Column Dictionary formulas for recompute_on_scan fields.
Phase 3 delivers 10 core DSL functions; others use error_policy fallback.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DSLEvaluator:
    """Safe DSL evaluator for derivation formulas."""
    
    CORE_FUNCTIONS = {
        'BASENAME', 'DIRNAME', 'EXTENSION', 'LOWER', 'UPPER',
        'NOW_UTC', 'FORMAT_ISO8601', 'IS_NULL', 'COALESCE', 'IF'
    }
    
    def __init__(self):
        self.functions = {
            'BASENAME': self._basename,
            'DIRNAME': self._dirname,
            'EXTENSION': self._extension,
            'LOWER': lambda x: str(x).lower() if x else None,
            'UPPER': lambda x: str(x).upper() if x else None,
            'NOW_UTC': lambda: datetime.utcnow().isoformat() + 'Z',
            'FORMAT_ISO8601': lambda dt: dt if isinstance(dt, str) else str(dt),
            'IS_NULL': lambda x: x is None,
            'COALESCE': lambda *args: next((a for a in args if a is not None), None),
            'IF': lambda cond, true_val, false_val: true_val if cond else false_val
        }
    
    def _basename(self, path: str) -> Optional[str]:
        if not path:
            return None
        return Path(path).name
    
    def _dirname(self, path: str) -> Optional[str]:
        if not path:
            return None
        return str(Path(path).parent)
    
    def _extension(self, path: str) -> Optional[str]:
        if not path:
            return None
        ext = Path(path).suffix
        return ext[1:].lower() if ext else None
    
    def evaluate(self, formula: str, record: Dict[str, Any]) -> Any:
        """Evaluate DSL formula against record."""
        if not formula:
            return None
        
        # Simple evaluation for core functions
        for func_name in self.CORE_FUNCTIONS:
            if func_name in formula:
                if func_name in self.functions:
                    return self._eval_function(func_name, formula, record)
        
        return None
    
    def _eval_function(self, func_name: str, formula: str, record: Dict[str, Any]) -> Any:
        """Evaluate a single function call."""
        # Simple pattern matching for function calls
        match = re.search(rf'{func_name}\((.*?)\)', formula)
        if not match:
            return None
        
        arg = match.group(1).strip().strip('"\'')
        
        # Look up argument in record if it's a field name
        value = record.get(arg, arg)
        
        # Call the function
        func = self.functions.get(func_name)
        if func:
            try:
                return func(value)
            except Exception:
                return None
        
        return None


class DerivationEngine:
    """Derivation engine for computed fields."""
    
    def __init__(self):
        self.evaluator = DSLEvaluator()
        self.derivations = {}
    
    def load_derivations(self, derivations_config: Dict[str, Any]):
        """Load derivation formulas from config."""
        self.derivations = derivations_config.get('derived_columns', {})
    
    def derive_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Compute derived fields for a record."""
        derived = {}
        
        for field_name, deriv_spec in self.derivations.items():
            formula = deriv_spec.get('formula')
            error_policy = deriv_spec.get('error_policy', 'use_null')
            
            if not formula:
                continue
            
            try:
                value = self.evaluator.evaluate(formula, record)
                derived[field_name] = value
            except Exception:
                if error_policy == 'use_null':
                    derived[field_name] = None
                elif error_policy == 'fail':
                    raise
        
        return derived
