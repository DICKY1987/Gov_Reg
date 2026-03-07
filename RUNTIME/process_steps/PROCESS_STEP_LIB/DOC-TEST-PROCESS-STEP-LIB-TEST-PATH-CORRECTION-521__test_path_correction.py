# DOC_LINK: DOC-TEST-PROCESS-STEP-LIB-TEST-PATH-CORRECTION-521
import json
import pytest
from pathlib import Path

# Skip if semantic mapping doesn't exist
mapping_file = Path('workspace/semantic_file_mapping.json')
if not mapping_file.exists():
    pytest.skip("Requires workspace/semantic_file_mapping.json", allow_module_level=True)

# Load mappings
with open('workspace/semantic_file_mapping.json', 'r') as f:
    mapping = json.load(f)

# Test E2E-1-005 with path correction
step_id = 'E2E-1-005'

print("=" * 70)
print(f"TESTING: Step {step_id} - Initialize Pattern Database")
print("=" * 70)

# Check sample files with corrected paths
test_files = [
    "SUB_PATTERNS\\automation\\analyzers\\performance_analyzer.py",
    "SUB_PATTERNS\\automation\\detectors\\anti_pattern_detector.py",
    "SUB_PATTERNS\\automation\\detectors\\duplicate_detector.py",
    "SUB_PATTERNS\\validate_patterns_schema.py"
]

exists_count = 0
for file_rel in test_files:
    file_path = Path("..") / file_rel
    exists = file_path.exists()
    if exists:
        exists_count += 1
    print(f"{'✓' if exists else '✗'} {file_rel}")

print("\n" + "=" * 70)
print(f"RESULT: {exists_count}/{len(test_files)} pattern files exist")
print("\nISSUE IDENTIFIED:")
print("  Classification report uses old paths: 'patterns\\' (archived)")
print("  Current structure uses: 'SUB_PATTERNS\\'")
print("\nRECOMMENDATION:")
print("  Re-run classification with current directory structure")
print("=" * 70)
