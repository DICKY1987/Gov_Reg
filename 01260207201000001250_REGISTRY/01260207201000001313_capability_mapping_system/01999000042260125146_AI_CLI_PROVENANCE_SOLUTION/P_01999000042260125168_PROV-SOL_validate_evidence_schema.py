#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0993
"""
Evidence Schema Validator
Created: 2026-01-04

Validates EVIDENCE_SCHEMA_EXTENDED.yaml for:
- Structural correctness
- Required fields presence
- Type constraint compliance
- Evidence path naming conventions
- Collector registry completeness

Usage:
    python validate_evidence_schema.py
    python validate_evidence_schema.py --schema EVIDENCE_SCHEMA_EXTENDED.yaml
    python validate_evidence_schema.py --verbose
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


# ============================================================================
# VALIDATION RULES
# ============================================================================

REQUIRED_TOP_LEVEL_KEYS = [
    "schema_version",
    "description",
    "evidence_paths",
    "collectors",
    "validation",
    "privacy",
    "safety"
]

REQUIRED_EVIDENCE_PATH_FIELDS = [
    "type",
    "description",
    "source"
]

VALID_TYPES = [
    "boolean",
    "integer",
    "float",
    "string",
    "datetime",
    "array",
    "enum"
]

EVIDENCE_PATH_PREFIXES = {
    "evidence": "Deterministic evidence (hard decisions allowed)",
    "provenance": "Heuristic evidence (scoring/ranking only)"
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

class SchemaValidator:
    """Validates evidence schema YAML file."""

    def __init__(self, schema_path: Path, verbose: bool = False):
        self.schema_path = schema_path
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.schema_data: Dict[str, Any] = {}

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

    def load_schema(self) -> bool:
        """Load YAML schema file."""
        if not self.schema_path.exists():
            self.log_error(f"Schema file not found: {self.schema_path}")
            return False

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema_data = yaml.safe_load(f)
            self.log_info(f"Loaded schema from: {self.schema_path}")
            return True
        except yaml.YAMLError as e:
            self.log_error(f"YAML parsing error: {e}")
            return False
        except Exception as e:
            self.log_error(f"Failed to load schema: {e}")
            return False

    def validate_structure(self) -> bool:
        """Validate top-level structure."""
        valid = True

        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in self.schema_data:
                self.log_error(f"Missing required top-level key: '{key}'")
                valid = False

        if valid:
            self.log_info("Top-level structure is valid")

        return valid

    def validate_evidence_paths(self) -> bool:
        """Validate evidence path definitions."""
        valid = True
        evidence_paths = self.schema_data.get("evidence_paths", {})

        if not evidence_paths:
            self.log_error("No evidence paths defined")
            return False

        # Check for required prefixes
        for prefix, description in EVIDENCE_PATH_PREFIXES.items():
            if prefix not in evidence_paths:
                self.log_error(f"Missing evidence path prefix: '{prefix}' ({description})")
                valid = False

        # Validate individual paths
        path_count = 0
        for prefix, paths in evidence_paths.items():
            if prefix not in EVIDENCE_PATH_PREFIXES:
                self.log_warning(f"Unexpected evidence path prefix: '{prefix}'")

            path_count += self._validate_path_tree(f"{prefix}", paths)

        self.log_info(f"Total evidence paths defined: {path_count}")
        return valid

    def _validate_path_tree(self, path_prefix: str, node: Any) -> int:
        """Recursively validate evidence path tree."""
        if not isinstance(node, dict):
            return 0

        count = 0

        # Check if this is a leaf node (has type/description/source)
        if "type" in node:
            count += 1
            self._validate_leaf_node(path_prefix, node)
        else:
            # Recurse into child nodes
            for key, value in node.items():
                child_path = f"{path_prefix}.{key}"
                count += self._validate_path_tree(child_path, value)

        return count

    def _validate_leaf_node(self, path: str, node: Dict[str, Any]):
        """Validate a leaf evidence path node."""
        # Check required fields
        for field in REQUIRED_EVIDENCE_PATH_FIELDS:
            if field not in node:
                self.log_error(f"Path '{path}' missing required field: '{field}'")

        # Validate type
        path_type = node.get("type")
        if path_type not in VALID_TYPES:
            self.log_error(f"Path '{path}' has invalid type: '{path_type}'")

        # Validate type-specific constraints
        if path_type == "float":
            range_val = node.get("range")
            if range_val and (not isinstance(range_val, list) or len(range_val) != 2):
                self.log_warning(f"Path '{path}' has invalid range specification")

        if path_type == "enum":
            if "values" not in node:
                self.log_error(f"Path '{path}' is enum but missing 'values' field")

        if path_type == "array":
            if "items" not in node:
                self.log_warning(f"Path '{path}' is array but missing 'items' specification")

    def validate_collectors(self) -> bool:
        """Validate collector registry."""
        valid = True
        collectors = self.schema_data.get("collectors", [])

        if not collectors:
            self.log_error("No collectors defined")
            return False

        collector_ids = set()
        for idx, collector in enumerate(collectors):
            collector_id = collector.get("collector_id")

            if not collector_id:
                self.log_error(f"Collector #{idx} missing 'collector_id'")
                valid = False
                continue

            if collector_id in collector_ids:
                self.log_error(f"Duplicate collector_id: '{collector_id}'")
                valid = False

            collector_ids.add(collector_id)

            # Validate required fields
            if "source" not in collector:
                self.log_error(f"Collector '{collector_id}' missing 'source'")
                valid = False

            if "evidence_paths" not in collector:
                self.log_error(f"Collector '{collector_id}' missing 'evidence_paths'")
                valid = False

        self.log_info(f"Total collectors defined: {len(collectors)}")
        return valid

    def validate_privacy_safety(self) -> bool:
        """Validate privacy and safety configurations."""
        valid = True

        privacy = self.schema_data.get("privacy", {})
        safety = self.schema_data.get("safety", {})

        # Privacy checks
        required_privacy = ["prompt_storage", "path_filtering", "repo_root"]
        for field in required_privacy:
            if field not in privacy:
                self.log_error(f"Missing privacy field: '{field}'")
                valid = False

        # Check prompt storage is hash-only
        if privacy.get("prompt_storage") != "SHA256_HASH_ONLY":
            self.log_warning("Prompt storage should be SHA256_HASH_ONLY for privacy")

        # Safety checks
        required_safety = ["graceful_degradation", "default_behavior"]
        for field in required_safety:
            if field not in safety:
                self.log_error(f"Missing safety field: '{field}'")
                valid = False

        if valid:
            self.log_info("Privacy and safety configurations are valid")

        return valid

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations and return results."""
        print(f"\n{'='*60}")
        print(f"Evidence Schema Validation")
        print(f"{'='*60}")
        print(f"Schema: {self.schema_path}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        if not self.load_schema():
            return False, self._generate_report()

        results = {
            "structure": self.validate_structure(),
            "evidence_paths": self.validate_evidence_paths(),
            "collectors": self.validate_collectors(),
            "privacy_safety": self.validate_privacy_safety()
        }

        overall_valid = all(results.values())

        return overall_valid, self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        report = {
            "schema_path": str(self.schema_path),
            "timestamp": datetime.now().isoformat(),
            "valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }

        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")

        if report["valid"]:
            print("✅ Schema is VALID")
        else:
            print("❌ Schema is INVALID")

        print(f"\nErrors: {report['error_count']}")
        print(f"Warnings: {report['warning_count']}")
        print(f"Info: {len(report['info'])}")

        if report["errors"]:
            print("\nErrors:")
            for error in report["errors"]:
                print(f"  {error}")

        if report["warnings"]:
            print("\nWarnings:")
            for warning in report["warnings"]:
                print(f"  {warning}")

        if self.verbose and report["info"]:
            print("\nInfo:")
            for info in report["info"]:
                print(f"  {info}")

        print(f"\n{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate evidence schema YAML file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_evidence_schema.py
  python validate_evidence_schema.py --schema custom_schema.yaml
  python validate_evidence_schema.py --verbose
  python validate_evidence_schema.py --output report.json
        """
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("EVIDENCE_SCHEMA_EXTENDED.yaml"),
        help="Path to schema YAML file (default: EVIDENCE_SCHEMA_EXTENDED.yaml)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output validation report to JSON file"
    )

    args = parser.parse_args()

    # Run validation
    validator = SchemaValidator(args.schema, verbose=args.verbose)
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
