# DOC_LINK: DOC-TEST-PROCESS-STEP-LIB-TEST-PATTERN-STEP-522
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

with open('workspace/process_dag.json', 'r') as f:
    dag = json.load(f)

# Test E2E-1-005 (Pattern system)
step_id = 'E2E-1-005'
step = next(s for s in dag['nodes'] if s['step_id'] == step_id)

print("=" * 70)
print(f"SAMPLE TEST: Step {step_id}")
print("=" * 70)
print(f"Step Name: {step['name']}")
print(f"Phase: {step['phase']}")
print(f"Operation: {step['operation_kind']}")
print(f"\nMapped Files ({len(mapping[step_id])} total - showing first 10):")
print("-" * 70)

exists_count = 0
for i, file_info in enumerate(mapping[step_id][:10], 1):
    file_path = Path("..") / file_info['file'].replace('\\', '/')
    exists = file_path.exists()
    if exists:
        exists_count += 1

    print(f"\n{i}. {file_info['file']}")
    print(f"   Confidence: {file_info['confidence']}% | Exists: {'✓' if exists else '✗'}")

print("\n" + "=" * 70)
print(f"Files exist: {exists_count}/10 checked")
print("=" * 70)
