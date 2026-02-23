"""Phase 0.7: Allocate 20-digit IDs for migration files"""
import json
from datetime import datetime
from pathlib import Path

# Load baseline
with open('.migration/reports/PRE_MIGRATION_TEST_BASELINE.json', 'r') as f:
    baseline = json.load(f)
baseline_count = baseline['baseline_count']

# Load updated manifest
with open('.migration/mapping/UPDATED_source_manifest.json', 'r') as f:
    manifest = json.load(f)
discovered_count = manifest['total_count']

# Load updated plan
with open('.migration/mapping/UPDATED_MIGRATION_PLAN.json', 'r') as f:
    plan = json.load(f)

# Starting ID (standard Gov_Reg 20-digit format)
# Format: 01999000042260124XXX
next_id = 1999000042260125000  # Start after existing IDs

# Allocate IDs for each file
id_allocations = []
current_id = next_id

print(f"Allocating IDs for {discovered_count} files...")
print(f"Starting ID: {current_id:020d}")

for file_info in plan['files']:
    id_allocations.append({
        'filename': file_info['filename'],
        'source_path': file_info['absolute_path'],
        'target_path': file_info['target_path'],
        'allocated_id': f"{current_id:020d}",
        'order': len(id_allocations) + 1
    })
    current_id += 1

# Allocate IDs for __init__.py files
init_files = [
    'src/repo_autoops/__init__.py',
    'src/repo_autoops/models/__init__.py',
    'src/repo_autoops/automation_descriptor/__init__.py',
    'src/registry_writer/__init__.py',
    'src/validators/__init__.py',
    'src/generators/__init__.py',
    'src/orchestrators/__init__.py',
    'scripts/__init__.py',
    'scripts/parsers/__init__.py',
    'scripts/utilities/__init__.py',
    'docs/__init__.py',
    'docs/governance/__init__.py'
]

print(f"\nAllocating IDs for {len(init_files)} __init__.py files...")

for init_file in init_files:
    id_allocations.append({
        'filename': '__init__.py',
        'source_path': None,
        'target_path': f"Gov_Reg/{init_file}",
        'allocated_id': f"{current_id:020d}",
        'order': len(id_allocations) + 1,
        'is_new_init': True
    })
    current_id += 1

# Calculate expected final count
init_file_count = len(init_files)
buffer_count = int(discovered_count * 0.1)
expected_final_count = baseline_count + discovered_count + init_file_count

result = {
    'baseline_count': baseline_count,
    'discovered_count': discovered_count,
    'init_file_count': init_file_count,
    'buffer_count': buffer_count,
    'expected_final_count': expected_final_count,
    'formula': 'baseline_count + discovered_count + init_file_count',
    'allocations': id_allocations,
    'total_allocated': len(id_allocations),
    'starting_id': f"{next_id:020d}",
    'next_available_id': f"{current_id:020d}",
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

with open('.migration/mapping/id_allocation.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✓ {len(id_allocations)} IDs allocated")
print(f"  Start ID: {next_id:020d}")
print(f"  End ID: {current_id-1:020d}")
print(f"  Next available: {current_id:020d}")
print(f"\nExpected final registry count: {expected_final_count}")
print(f"  Baseline: {baseline_count}")
print(f"  Discovered files: {discovered_count}")
print(f"  Init files: {init_file_count}")
