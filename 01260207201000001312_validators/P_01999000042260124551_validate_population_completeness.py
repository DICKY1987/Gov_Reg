"""
Population Completeness Validator
P_01999000042260124551_validate_population_completeness.py

Validates population plan completeness and consistency.
Error codes: POP001-POP005
"""

from pathlib import Path
from typing import List, Dict, Set
import yaml
import sys


class ValidationError:
    """Represents a validation error"""
    def __init__(self, code: str, severity: str, message: str, column: str = None):
        self.code = code
        self.severity = severity
        self.message = message
        self.column = column
    
    def __repr__(self):
        col_info = f" (column: {self.column})" if self.column else ""
        return f"[{self.severity}] {self.code}: {self.message}{col_info}"


class PopulationCompletenessValidator:
    """Validates derivation completeness and consistency"""
    
    # Error code definitions
    ERROR_CODES = {
        'POP001_MISSING_DERIVATION': 'Error: recompute_on_* column has no derivation',
        'POP002_CYCLIC_DEPENDENCY': 'Error: Dependency cycle detected',
        'POP003_TYPE_MISMATCH': 'Error: Formula output != declared type',
        'POP004_UNKNOWN_DEPENDENCY': 'Error: depends_on references unknown column',
        'POP005_FORBIDDEN_FUNCTION': 'Error: Formula uses forbidden function'
    }
    
    def __init__(self, derivations_path: Path, write_policy_path: Path):
        self.derivations_path = derivations_path
        self.write_policy_path = write_policy_path
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.derivations = {}
        self.write_policies = {}
        self.all_columns = set()
    
    def load_files(self):
        """Load YAML files"""
        with open(self.derivations_path, 'r', encoding='utf-8') as f:
            derivations_data = yaml.safe_load(f)
        
        with open(self.write_policy_path, 'r', encoding='utf-8') as f:
            write_policy_data = yaml.safe_load(f)
        
        if 'derived_columns' in derivations_data:
            self.derivations = derivations_data['derived_columns']
        
        if 'columns' in write_policy_data:
            self.write_policies = write_policy_data['columns']
            self.all_columns = set(write_policy_data['columns'].keys())
    
    def validate_missing_derivations(self):
        """Check for recompute_on_* columns without derivations"""
        for col_name, policy in self.write_policies.items():
            update_policy = policy.get('update_policy', '')
            if update_policy in ['recompute_on_scan', 'recompute_on_build']:
                if col_name not in self.derivations:
                    self.errors.append(ValidationError(
                        'POP001_MISSING_DERIVATION',
                        'Error',
                        f"Column '{col_name}' has update_policy '{update_policy}' but no derivation",
                        col_name
                    ))
    
    def validate_unknown_dependencies(self):
        """Check for dependencies referencing unknown columns"""
        for col_name, derivation in self.derivations.items():
            depends_on = derivation.get('depends_on', [])
            if depends_on is None:
                depends_on = []
            for dep in depends_on:
                if dep not in self.all_columns and dep not in self.derivations:
                    self.errors.append(ValidationError(
                        'POP004_UNKNOWN_DEPENDENCY',
                        'Error',
                        f"Column '{col_name}' depends on unknown column '{dep}'",
                        col_name
                    ))
    
    def detect_cycles(self):
        """Detect cycles in dependencies"""
        def has_cycle_from(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            if node in self.derivations:
                for neighbor in self.derivations[node].get('depends_on', []):
                    if neighbor not in visited:
                        if has_cycle_from(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for col in self.derivations:
            if col not in visited:
                if has_cycle_from(col, visited, set()):
                    self.errors.append(ValidationError(
                        'POP002_CYCLIC_DEPENDENCY',
                        'Error',
                        f"Cycle detected involving column '{col}'",
                        col
                    ))
    
    def validate(self) -> bool:
        """Run all validations"""
        self.load_files()
        self.validate_missing_derivations()
        self.validate_unknown_dependencies()
        self.detect_cycles()
        
        return len(self.errors) == 0
    
    def get_report(self) -> Dict:
        """Generate validation report"""
        return {
            'all_valid': len(self.errors) == 0,
            'cycle_count': len([e for e in self.errors if e.code == 'POP002_CYCLIC_DEPENDENCY']),
            'missing_derivation_count': len([e for e in self.errors if e.code == 'POP001_MISSING_DERIVATION']),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': [str(e) for e in self.errors],
            'warnings': [str(w) for w in self.warnings]
        }


def main():
    """CLI entry point"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Validate Population Completeness')
    parser.add_argument('--derivations', required=True, help='Path to DERIVATIONS.yaml')
    parser.add_argument('--write-policy', required=True, help='Path to WRITE_POLICY.yaml')
    parser.add_argument('--output', help='Output path for validation report')
    
    args = parser.parse_args()
    
    validator = PopulationCompletenessValidator(
        Path(args.derivations),
        Path(args.write_policy)
    )
    
    is_valid = validator.validate()
    report = validator.get_report()
    
    # Print summary
    print(f"all_valid: {report['all_valid']}")
    print(f"cycle_count: {report['cycle_count']}")
    print(f"missing_derivation_count: {report['missing_derivation_count']}")
    print(f"error_count: {report['error_count']}")
    
    # Print errors
    for error in validator.errors:
        print(error)
    
    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {output_path}")
    
    return 0 if is_valid else 1


if __name__ == '__main__':
    sys.exit(main())
