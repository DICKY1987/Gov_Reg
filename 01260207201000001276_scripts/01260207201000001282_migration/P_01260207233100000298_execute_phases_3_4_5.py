"""
Phase 3: Add FILE_ID headers to Python files (simplified)
Phase 4: Update governance registry
Phase 5: Update path_index.yaml
"""
import json
import yaml
from pathlib import Path
from datetime import datetime


def add_file_id_headers():
    """Add FILE_ID headers to all migrated Python files."""

    print("="*70)
    print("PHASE 3: ADD FILE_ID HEADERS (SIMPLIFIED)")
    print("="*70)

    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'r') as f:
        phase12_results = json.load(f)

    updated_files = []

    for file_info in phase12_results['files_copied']:
        target_path = Path(file_info['target'])
        file_id = file_info['id']

        if not target_path.suffix == '.py':
            continue

        try:
            # Read existing content
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add FILE_ID header if not present
            if 'FILE_ID:' not in content:
                header = f'''"""
FILE_ID: {file_id}
Migrated from: {file_info['source']}
"""

'''
                # Insert after shebang or at top
                if content.startswith('#!'):
                    lines = content.split('\n', 1)
                    new_content = lines[0] + '\n' + header + (lines[1] if len(lines) > 1 else '')
                else:
                    new_content = header + content

                # Write back
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                updated_files.append(str(target_path))

        except Exception as e:
            print(f"  ⚠️  Error updating {target_path}: {e}")

    print(f"✓ Added FILE_ID headers to {len(updated_files)} Python files")
    return updated_files


def update_registry():
    """Update governance_registry_unified.json with new entries."""

    print("\n" + "="*70)
    print("PHASE 4: UPDATE GOVERNANCE REGISTRY")
    print("="*70)

    # Directly use known registry path
    registry_path = Path('REGISTRY/01999000042260124503_governance_registry_unified.json')

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # Load Phase 1&2 results
    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'r') as f:
        phase12_results = json.load(f)

    # Get current timestamp
    now = datetime.utcnow().isoformat() + 'Z'

    # Add new file entries
    if 'files' not in registry:
        registry['files'] = []

    added_count = 0
    for file_info in phase12_results['files_copied']:
        target_path = Path(file_info['target'])
        relative_path = str(target_path).replace('\\', '/')

        entry = {
            'file_id': file_info['id'],
            'relative_path': relative_path,
            'filename': target_path.name,
            'extension': target_path.suffix,
            'repo_root_id': '01',
            'record_kind': 'file',
            'has_tests': False,
            'created_utc': now,
            'updated_utc': now
        }

        registry['files'].append(entry)
        added_count += 1

    # Add __init__.py entries
    for init_info in phase12_results['inits_created']:
        init_path = Path(init_info['path'])
        relative_path = str(init_path).replace('\\', '/')

        entry = {
            'file_id': init_info['id'],
            'relative_path': relative_path,
            'filename': '__init__.py',
            'extension': '.py',
            'repo_root_id': '01',
            'record_kind': 'file',
            'has_tests': False,
            'created_utc': now,
            'updated_utc': now
        }

        registry['files'].append(entry)
        added_count += 1

    # Update registry metadata
    registry['generated'] = now
    if 'schema_version' not in registry:
        registry['schema_version'] = '4.0'

    # Save updated registry
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✓ Added {added_count} entries to registry")
    print(f"  Registry now has {len(registry['files'])} total files")
    print(f"  Updated: {registry_path}")

    return added_count


def update_path_index():
    """Update path_index.yaml with semantic keys for new files."""

    print("\n" + "="*70)
    print("PHASE 5: UPDATE PATH_INDEX.YAML")
    print("="*70)

    # Load path_index.yaml
    path_index_file = Path('PATH_FILES/config/path_index.yaml')
    with open(path_index_file, 'r', encoding='utf-8') as f:
        path_index = yaml.safe_load(f)

    if path_index is None:
        path_index = {}

    # Load Phase 1&2 results
    with open('.migration/reports/PHASE_1_2_RESULTS.json', 'r') as f:
        phase12_results = json.load(f)

    # Add semantic keys for important files
    added_keys = []

    # Key files to add semantic keys for
    key_patterns = {
        'orchestrator.py': 'REPO_AUTOOPS_ORCHESTRATOR',
        'registry_writer_service.py': 'REGISTRY_WRITER_SERVICE',
        'validators.py': 'REPO_AUTOOPS_VALIDATORS',
        'generator_orchestrator.py': 'GENERATOR_ORCHESTRATOR'
    }

    for file_info in phase12_results['files_copied']:
        target_path = Path(file_info['target'])
        original_name = file_info['original_name']

        # Check if this is a key file
        semantic_key = key_patterns.get(original_name)

        if semantic_key:
            relative_path = str(target_path).replace('\\', '/')

            path_index[semantic_key] = {
                'path': relative_path,
                'file_id': file_info['id'],
                'description': f"Migrated {original_name}"
            }
            added_keys.append(semantic_key)

    # Save updated path_index.yaml
    with open(path_index_file, 'w', encoding='utf-8') as f:
        yaml.dump(path_index, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Added {len(added_keys)} semantic keys to path_index.yaml")
    for key in added_keys:
        print(f"  - {key}")

    return added_keys


def execute_phases_3_4_5():
    """Execute phases 3, 4, and 5."""

    start_time = datetime.utcnow()

    # Phase 3: Add FILE_ID headers
    updated_files = add_file_id_headers()

    # Phase 4: Update registry
    registry_count = update_registry()

    # Phase 5: Update path_index.yaml
    added_keys = update_path_index()

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Save results
    result = {
        'phases': '3_4_5',
        'phase_3': {
            'files_updated': len(updated_files),
            'file_list': updated_files
        },
        'phase_4': {
            'registry_entries_added': registry_count
        },
        'phase_5': {
            'semantic_keys_added': len(added_keys),
            'keys': added_keys
        },
        'duration_seconds': duration,
        'start_time': start_time.isoformat() + 'Z',
        'end_time': end_time.isoformat() + 'Z'
    }

    with open('.migration/reports/PHASE_3_4_5_RESULTS.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("PHASES 3, 4, 5 COMPLETE")
    print("="*70)
    print(f"Duration: {duration:.1f} seconds")
    print(f"Results saved to: .migration/reports/PHASE_3_4_5_RESULTS.json")

    return result


if __name__ == '__main__':
    execute_phases_3_4_5()
