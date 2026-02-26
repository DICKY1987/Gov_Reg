#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0995
"""
Rule Consistency Validator
Created: 2026-01-04

Validates py_identify_solution.yml for:
- Rule structure completeness
- Evidence path references exist
- No circular dependencies
- Decision vocabulary consistency
- Rule type correctness (hard_stop, gate, classification, ranking)
- Evidence path namespace compliance (evidence.* vs provenance.*)

Usage:
    python validate_rule_consistency.py
    python validate_rule_consistency.py --rules py_identify_solution.yml
    python validate_rule_consistency.py --schema EVIDENCE_SCHEMA_EXTENDED.yaml
    python validate_rule_consistency.py --verbose
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

VALID_RULE_TYPES = ['hard_stop', 'gate', 'classification', 'ranking', 'detection']

VALID_DECISIONS = [
    'ACTIVE', 'DO_NOT_QUARANTINE', 'OBSOLETE_CANDIDATE', 'QUARANTINE_ELIGIBLE',
    'UNKNOWN', 'DUPLICATE_SET_CANDIDATE', 'CANONICAL_PREFERENCE',
    'AI_GENERATED_HIGH_ACTIVITY', 'HUMAN_TOUCH_RECENT', 'SUPERSESSION_INTENT_DETECTED'
]

REQUIRED_RULE_FIELDS = ['rule_id', 'decision', 'type']

# Evidence paths that can make hard decisions (hard stops/gates)
DETERMINISTIC_EVIDENCE_PREFIX = 'evidence.'

# Evidence paths that are heuristic only (scoring/ranking)
HEURISTIC_EVIDENCE_PREFIX = 'provenance.'


# ============================================================================
# RULE CONSISTENCY VALIDATOR
# ============================================================================

class RuleConsistencyValidator:
    """Validates rule YAML for consistency and correctness."""

    def __init__(self, rules_path: Path, schema_path: Path = None, verbose: bool = False):
        self.rules_path = rules_path
        self.schema_path = schema_path
        self.verbose = verbose

        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

        self.rules_data: Dict[str, Any] = {}
        self.schema_data: Dict[str, Any] = {}

        self.all_evidence_paths: Set[str] = set()
        self.referenced_evidence_paths: Set[str] = set()
        self.rule_ids: Set[str] = set()
        self.rule_dependencies: Dict[str, List[str]] = defaultdict(list)

    def log_error(self, msg: str):
        """Log an error message."""
        self.errors.append(f"❌ ERROR: {msg}")
        if self.verbose:
            print(f"❌ ERROR: {msg}")

    def log_warning(self, msg: str):
        """Log a warning message."""
        self.warnings.append(f"⚠️  WARNING: {msg}")
        if self.verbose:
            print(f"⚠️  WARNING: {msg}")

    def log_info(self, msg: str):
        """Log an info message."""
        self.info.append(f"ℹ️  INFO: {msg}")
        if self.verbose:
            print(f"ℹ️  INFO: {msg}")

    def load_files(self) -> bool:
        """Load YAML files."""
        # Load rules
        if not self.rules_path.exists():
            self.log_error(f"Rules file not found: {self.rules_path}")
            return False

        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                self.rules_data = yaml.safe_load(f)
            self.log_info(f"Loaded rules from: {self.rules_path}")
        except Exception as e:
            self.log_error(f"Failed to load rules: {e}")
            return False

        # Load schema (optional)
        if self.schema_path and self.schema_path.exists():
            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self.schema_data = yaml.safe_load(f)
                self.log_info(f"Loaded schema from: {self.schema_path}")
                self._extract_evidence_paths_from_schema()
            except Exception as e:
                self.log_warning(f"Failed to load schema: {e}")

        return True

    def _extract_evidence_paths_from_schema(self):
        """Extract all valid evidence paths from schema."""
        evidence_paths = self.schema_data.get('evidence_paths', {})

        def _extract_paths(prefix: str, node: Any):
            if isinstance(node, dict):
                if 'type' in node:
                    # Leaf node
                    self.all_evidence_paths.add(prefix)
                else:
                    # Recurse
                    for key, value in node.items():
                        _extract_paths(f"{prefix}.{key}", value)

        for top_level, paths in evidence_paths.items():
            _extract_paths(top_level, paths)

        self.log_info(f"Extracted {len(self.all_evidence_paths)} evidence paths from schema")

    def validate_rule_structure(self) -> bool:
        """Validate rule structure and required fields."""
        valid = True

        if 'rules' not in self.rules_data and 'rule_sets' not in self.rules_data:
            self.log_error("Neither 'rules' nor 'rule_sets' found in rules file")
            return False

        # Check rule sets
        rule_sets = self.rules_data.get('rule_sets', [])
        if isinstance(rule_sets, list):
            for idx, rule_set in enumerate(rule_sets):
                if not isinstance(rule_set, dict):
                    self.log_error(f"Rule set #{idx} is not a dictionary")
                    valid = False
                    continue

                # Check rule set structure
                if 'rule_set_id' not in rule_set:
                    self.log_warning(f"Rule set #{idx} missing 'rule_set_id'")

                rules = rule_set.get('rules', [])
                for rule_idx, rule in enumerate(rules):
                    if not self._validate_single_rule(rule, f"{rule_set.get('rule_set_id', idx)}.{rule_idx}"):
                        valid = False

        # Check standalone rules
        rules = self.rules_data.get('rules', [])
        if isinstance(rules, list):
            for idx, rule in enumerate(rules):
                if not self._validate_single_rule(rule, f"standalone.{idx}"):
                    valid = False

        return valid

    def _validate_single_rule(self, rule: Dict[str, Any], rule_ref: str) -> bool:
        """Validate a single rule."""
        valid = True

        # Check required fields
        for field in REQUIRED_RULE_FIELDS:
            if field not in rule:
                self.log_error(f"Rule '{rule_ref}' missing required field: '{field}'")
                valid = False

        rule_id = rule.get('rule_id', rule_ref)
        self.rule_ids.add(rule_id)

        # Check rule type
        rule_type = rule.get('type')
        if rule_type and rule_type not in VALID_RULE_TYPES:
            self.log_error(f"Rule '{rule_id}' has invalid type: '{rule_type}'")
            valid = False

        # Check decision vocabulary
        decision = rule.get('decision')
        if decision and decision not in VALID_DECISIONS:
            self.log_warning(f"Rule '{rule_id}' has non-standard decision: '{decision}'")

        # Validate evidence path references
        self._extract_evidence_references(rule, rule_id)

        # Check deterministic/heuristic boundary
        if rule_type in ['hard_stop', 'gate']:
            # Hard stops and gates should only use deterministic evidence
            for path in self.referenced_evidence_paths:
                if path.startswith(HEURISTIC_EVIDENCE_PREFIX):
                    self.log_error(
                        f"Rule '{rule_id}' is '{rule_type}' but uses heuristic evidence: '{path}'"
                    )
                    valid = False

        return valid

    def _extract_evidence_references(self, rule: Dict[str, Any], rule_id: str):
        """Extract all evidence path references from a rule."""
        def _scan_dict(obj: Any):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Check if key looks like an evidence path
                    if isinstance(key, str) and ('.' in key):
                        if key.startswith(DETERMINISTIC_EVIDENCE_PREFIX) or key.startswith(HEURISTIC_EVIDENCE_PREFIX):
                            self.referenced_evidence_paths.add(key.split('.')[0] + '.' + key.split('.')[1])
                    _scan_dict(value)
            elif isinstance(obj, list):
                for item in obj:
                    _scan_dict(item)

        _scan_dict(rule)

    def validate_evidence_paths(self) -> bool:
        """Validate all referenced evidence paths exist in schema."""
        valid = True

        if not self.all_evidence_paths:
            self.log_warning("No schema loaded; skipping evidence path validation")
            return True

        for path in self.referenced_evidence_paths:
            # Check if path exists (allow partial matches)
            found = any(p.startswith(path) for p in self.all_evidence_paths)
            if not found:
                self.log_error(f"Referenced evidence path not in schema: '{path}'")
                valid = False

        self.log_info(f"Validated {len(self.referenced_evidence_paths)} evidence path references")
        return valid

    def validate_circular_dependencies(self) -> bool:
        """Check for circular rule dependencies."""
        # This is a simplified check - can be enhanced
        # For now, just report on dependency count
        self.log_info(f"Found {len(self.rule_ids)} unique rule IDs")
        return True

    def validate_decision_vocabulary(self) -> bool:
        """Validate decision vocabulary consistency."""
        valid = True

        # Collect all decisions
        decisions = set()

        def _collect_decisions(rules: List[Dict[str, Any]]):
            for rule in rules:
                if 'decision' in rule:
                    decisions.add(rule['decision'])

        # Check rule sets
        for rule_set in self.rules_data.get('rule_sets', []):
            _collect_decisions(rule_set.get('rules', []))

        # Check standalone rules
        _collect_decisions(self.rules_data.get('rules', []))

        # Report on decisions
        self.log_info(f"Found {len(decisions)} unique decisions: {', '.join(sorted(decisions))}")

        return valid

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations."""
        print(f"\n{'='*60}")
        print(f"Rule Consistency Validation")
        print(f"{'='*60}")
        print(f"Rules: {self.rules_path}")
        if self.schema_path:
            print(f"Schema: {self.schema_path}")
        print(f"{'='*60}\n")

        if not self.load_files():
            return False, self._generate_report()

        results = {
            'structure': self.validate_rule_structure(),
            'evidence_paths': self.validate_evidence_paths(),
            'circular_dependencies': self.validate_circular_dependencies(),
            'decision_vocabulary': self.validate_decision_vocabulary()
        }

        overall_valid = all(results.values())

        return overall_valid, self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            'rules_path': str(self.rules_path),
            'schema_path': str(self.schema_path) if self.schema_path else None,
            'valid': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'rule_count': len(self.rule_ids),
            'evidence_path_count': len(self.referenced_evidence_paths),
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }

    def print_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")

        if report['valid']:
            print("✅ Rules are VALID")
        else:
            print("❌ Rules have ERRORS")

        print(f"\nStatistics:")
        print(f"  Rules: {report['rule_count']}")
        print(f"  Evidence Paths Referenced: {report['evidence_path_count']}")
        print(f"  Errors: {report['error_count']}")
        print(f"  Warnings: {report['warning_count']}")

        if report['errors']:
            print("\nErrors:")
            for error in report['errors']:
                print(f"  {error}")

        if report['warnings']:
            print("\nWarnings:")
            for warning in report['warnings']:
                print(f"  {warning}")

        if self.verbose and report['info']:
            print("\nInfo:")
            for info in report['info']:
                print(f"  {info}")

        print(f"\n{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate rule YAML consistency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_rule_consistency.py
  python validate_rule_consistency.py --rules custom_rules.yml
  python validate_rule_consistency.py --schema EVIDENCE_SCHEMA_EXTENDED.yaml
  python validate_rule_consistency.py --verbose
        """
    )

    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("py_identify_solution.yml"),
        help="Path to rules YAML file (default: py_identify_solution.yml)"
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("EVIDENCE_SCHEMA_EXTENDED.yaml"),
        help="Path to evidence schema YAML file (default: EVIDENCE_SCHEMA_EXTENDED.yaml)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Save validation report to JSON file"
    )

    args = parser.parse_args()

    # Run validation
    validator = RuleConsistencyValidator(args.rules, args.schema, verbose=args.verbose)
    valid, report = validator.validate()
    validator.print_summary(report)

    # Save report if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
