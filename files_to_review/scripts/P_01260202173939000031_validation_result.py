#!/usr/bin/env python3
"""
Validation Gate: file_id Format Compliance

Ensures all file_id values in the registry match the SSOT specification:
- Pattern: ^[0-9]{20}$
- Format: 20-digit string
- Type: string (not numeric)

Work ID: WORK-MAPP-PY-001
Gate: PY_FILE_ID_FORMAT_V1
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Configuration
REGISTRY_ROOT = Path(r"C:\Users\richg\Gov_Reg\REGISTRY")
REGISTRY_FILE = REGISTRY_ROOT / "01999000042260124503_governance_registry_unified.json"
SSOT_FILE = REGISTRY_ROOT / "01999000042260124527_COMPLETE_SSOT.json"

# Expected patterns per SSOT
EXPECTED_PREFIX_PRIMARY = "01999000042260124"
EXPECTED_PREFIXES = ["01999000042260120", "01999000042260124", "01999000042260125"]
EXPECTED_PATTERN = re.compile(r'^01\d{15}\d{3}$')  # 01 + 15 digits + 3 digits
GENERIC_20_DIGIT = re.compile(r'^\d{20}$')


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.total_checked = 0
        self.valid_count = 0

    def add_error(self, msg):
        self.errors.append(msg)

    def add_warning(self, msg):
        self.warnings.append(msg)

    def add_info(self, msg):
        self.info.append(msg)

    def passed(self):
        return len(self.errors) == 0

    def summary(self):
        return {
            "passed": self.passed(),
            "total_checked": self.total_checked,
            "valid_count": self.valid_count,
            "errors": len(self.errors),
            "warnings": len(self.warnings)
        }


def load_ssot_specification():
    """Load file_id specification from SSOT."""
    try:
        with open(SSOT_FILE, 'r', encoding='utf-8') as f:
            ssot = json.load(f)

        spec = ssot.get("id_system", {}).get("file_id_format", {})
        prefix_config = spec.get("structure", {}).get("prefix", {})

        # Support both old single-prefix and new multi-prefix format
        valid_prefixes = prefix_config.get("valid_prefixes", [])
        if not valid_prefixes:
            # Fallback to old format
            single_prefix = prefix_config.get("value") or prefix_config.get("primary_prefix", EXPECTED_PREFIX_PRIMARY)
            valid_prefixes = [single_prefix]

        return {
            "pattern": spec.get("pattern", "^[0-9]{20}$"),
            "valid_prefixes": valid_prefixes,
            "primary_prefix": prefix_config.get("primary_prefix", valid_prefixes[0] if valid_prefixes else EXPECTED_PREFIX_PRIMARY),
            "prefix_length": prefix_config.get("length", 17),
            "suffix_length": spec.get("structure", {}).get("suffix", {}).get("length", 3),
            "total_length": spec.get("total_length", 20)
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not load SSOT specification: {e}")
        return {
            "pattern": "^[0-9]{20}$",
            "valid_prefixes": EXPECTED_PREFIXES,
            "primary_prefix": EXPECTED_PREFIX_PRIMARY,
            "prefix_length": 17,
            "suffix_length": 3,
            "total_length": 20
        }


def validate_file_id(file_id, spec, result):
    """Validate a single file_id against SSOT specification."""
    if not file_id:
        result.add_error("Missing file_id (null or empty)")
        return False

    # Check type (must be string, not numeric)
    if not isinstance(file_id, str):
        result.add_error(f"file_id is not a string: {file_id} (type: {type(file_id).__name__})")
        return False

    # Check length
    if len(file_id) != spec["total_length"]:
        result.add_error(f"file_id has wrong length: '{file_id}' (expected {spec['total_length']}, got {len(file_id)})")
        return False

    # Check it's all digits
    if not GENERIC_20_DIGIT.match(file_id):
        result.add_error(f"file_id contains non-digits: '{file_id}'")
        return False

    # Check prefix matches SSOT (allow any valid prefix)
    actual_prefix = file_id[:spec["prefix_length"]]
    if actual_prefix not in spec["valid_prefixes"]:
        valid_list = "', '".join(spec["valid_prefixes"])
        result.add_error(f"file_id has invalid prefix: '{file_id}' (expected one of: ['{valid_list}'], got '{actual_prefix}')")
        return False

    # Check suffix is valid (numeric, 3 digits)
    suffix = file_id[spec["prefix_length"]:]
    if len(suffix) != spec["suffix_length"]:
        result.add_error(f"file_id has wrong suffix length: '{file_id}' (expected {spec['suffix_length']}, got {len(suffix)})")
        return False

    # All checks passed
    return True


def validate_registry(registry_path, spec):
    """Validate all file_id values in the registry."""
    result = ValidationResult()

    print(f"📂 Loading registry: {registry_path.name}")

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception as e:
        result.add_error(f"Failed to load registry: {e}")
        return result

    files = registry.get("files", [])
    result.add_info(f"Found {len(files)} file records")

    print(f"🔍 Validating {len(files)} file_id values...")
    print()

    for idx, file_record in enumerate(files):
        file_id = file_record.get("file_id")
        relative_path = file_record.get("relative_path", f"<record #{idx}>")

        result.total_checked += 1

        if validate_file_id(file_id, spec, result):
            result.valid_count += 1
        else:
            # Add context to errors
            result.errors[-1] = f"  [{relative_path}] {result.errors[-1]}"

        # Also check anchor_file_id if present
        anchor_id = file_record.get("anchor_file_id")
        if anchor_id:
            result.total_checked += 1
            if validate_file_id(anchor_id, spec, result):
                result.valid_count += 1
            else:
                result.errors[-1] = f"  [{relative_path}] anchor_file_id: {result.errors[-1]}"

    return result


def print_results(result, spec):
    """Print validation results."""
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print()

    print(f"📋 Specification:")
    print(f"   Pattern:         {spec['pattern']}")
    print(f"   Valid Prefixes:  {', '.join(spec['valid_prefixes'])} ({spec['prefix_length']} digits each)")
    print(f"   Primary Prefix:  {spec['primary_prefix']}")
    print(f"   Suffix Length:   {spec['suffix_length']} digits")
    print(f"   Total Length:    {spec['total_length']} digits")
    print()

    print(f"📊 Summary:")
    print(f"   Total checked: {result.total_checked}")
    print(f"   Valid:         {result.valid_count}")
    print(f"   Errors:        {len(result.errors)}")
    print(f"   Warnings:      {len(result.warnings)}")
    print()

    if result.errors:
        print("❌ ERRORS:")
        for error in result.errors[:20]:  # Limit to first 20
            print(f"   {error}")
        if len(result.errors) > 20:
            print(f"   ... and {len(result.errors) - 20} more errors")
        print()

    if result.warnings:
        print("⚠️  WARNINGS:")
        for warning in result.warnings[:10]:
            print(f"   {warning}")
        if len(result.warnings) > 10:
            print(f"   ... and {len(result.warnings) - 10} more warnings")
        print()

    if result.passed():
        print("✅ GATE PASSED: All file_id values are valid")
    else:
        print("❌ GATE FAILED: file_id validation errors detected")

    print()
    print("=" * 70)


def main():
    """Main execution."""
    print("=" * 70)
    print("FILE_ID FORMAT VALIDATION GATE")
    print("=" * 70)
    print()

    # Load SSOT specification
    spec = load_ssot_specification()
    print(f"✓ Loaded SSOT specification")
    print(f"  Valid prefixes: {', '.join(spec['valid_prefixes'])}")
    print(f"  Primary prefix: {spec['primary_prefix']}")
    print(f"  Expected pattern: {spec['pattern']}")
    print()

    # Validate registry
    result = validate_registry(REGISTRY_FILE, spec)

    # Print results
    print_results(result, spec)

    # Save validation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "gate_id": "PY_FILE_ID_FORMAT_V1",
        "work_id": "WORK-MAPP-PY-001",
        "specification": spec,
        "results": result.summary(),
        "errors": result.errors[:100],  # Limit to first 100
        "warnings": result.warnings[:50]
    }

    report_path = REGISTRY_ROOT / ".runs" / f"validation_file_id_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"📄 Validation report saved: {report_path}")
    print()

    # Exit with appropriate code
    sys.exit(0 if result.passed() else 1)


if __name__ == "__main__":
    main()
