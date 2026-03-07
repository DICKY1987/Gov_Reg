#!/usr/bin/env python3
# DOC_LINK: DOC-PATTERN-AUTOMATION-PRE-COMMIT-001
"""
Pattern ID Pre-commit Hook
Validates pattern_id format, uniqueness and sync before commit
"""
# DOC_ID: DOC-PATTERN-AUTOMATION-PRE-COMMIT-001

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def main():
    """Run all pattern_id validations."""
    base = Path(__file__).parent.parent
    validators = [
        base / '2_VALIDATION_FIXING' / 'validate_pattern_id_format.py',
        base / '2_VALIDATION_FIXING' / 'validate_pattern_id_uniqueness.py',
        base / '2_VALIDATION_FIXING' / 'validate_pattern_id_sync.py',
    ]

    print("\n" + "="*60)
    print("PATTERN_ID PRE-COMMIT VALIDATION")
    print("="*60 + "\n")

    failed = []
    for validator in validators:
        if not validator.exists():
            print(f"⚠️  Validator not found: {validator.name}")
            continue

        print(f"Running {validator.name}...")
        import subprocess
        result = subprocess.run([sys.executable, str(validator)], capture_output=True)
        if result.returncode != 0:
            failed.append(validator.name)
            print(f"❌ {validator.name} FAILED")
        else:
            print(f"✅ {validator.name} PASSED")

    print("\n" + "="*60)
    if failed:
        print(f"❌ {len(failed)} validation(s) failed: {', '.join(failed)}")
        print("="*60 + "\n")
        return 1
    else:
        print("✅ All pattern_id validations passed")
        print("="*60 + "\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())
