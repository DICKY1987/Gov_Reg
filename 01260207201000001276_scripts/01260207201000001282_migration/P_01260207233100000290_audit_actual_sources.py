"""
Create comprehensive audit of actual source locations for migration.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime


def hash_file(path):
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def audit_source_locations():
    """Audit all actual source locations."""

    # Define actual source locations based on audit
    source_locations = {
        'location_1_eafix_repo_autoops': {
            'path': Path(r'C:\Users\richg\eafix-modular\repo_autoops'),
            'description': 'Main repo_autoops implementation',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc']
        },
        'location_2a_eafix_registry_writer': {
            'path': Path(r'C:\Users\richg\eafix-modular\services\registry_writer'),
            'description': 'Registry writer service',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc']
        },
        'location_2b_eafix_data_validator': {
            'path': Path(r'C:\Users\richg\eafix-modular\services\data-validator'),
            'description': 'Data validator service',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc', 'tests']
        },
        'location_2c_eafix_generator': {
            'path': Path(r'C:\Users\richg\eafix-modular\services\generator'),
            'description': 'Generator service',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc', 'tests']
        },
        'location_2d_eafix_flow_orchestrator': {
            'path': Path(r'C:\Users\richg\eafix-modular\services\flow-orchestrator'),
            'description': 'Flow orchestrator service',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc', 'tests']
        },
        'location_2e_eafix_signal_generator': {
            'path': Path(r'C:\Users\richg\eafix-modular\services\signal-generator'),
            'description': 'Signal generator service',
            'recursive': True,
            'include_patterns': ['*.py'],
            'exclude_patterns': ['__pycache__', '.pyc', 'tests']
        },
        'location_3_eafix_scripts': {
            'path': Path(r'C:\Users\richg\eafix-modular\scripts'),
            'description': 'Script implementations',
            'recursive': True,
            'include_patterns': ['*registry*.py', '*validator*.py', '*generator*.py'],
            'exclude_patterns': ['__pycache__', '.pyc']
        },
        'location_4_eafix_dir_mgmt': {
            'path': Path(r'C:\Users\richg\eafix-modular\Directory management system\03_IMPLEMENTATION'),
            'description': 'Directory management implementations',
            'recursive': False,
            'include_patterns': ['*registry*.py', '*generator*.py'],
            'exclude_patterns': []
        },
        'location_5_all_ai_governance': {
            'path': Path(r'C:\Users\richg\ALL_AI\GOVERNANCE\registries'),
            'description': 'Governance documentation',
            'recursive': False,
            'include_patterns': ['*.md'],
            'exclude_patterns': ['.dir_id']
        },
        'location_6_all_ai_mapp_py': {
            'path': Path(r'C:\Users\richg\ALL_AI\mapp_py'),
            'description': 'Mapp parser implementations',
            'recursive': False,
            'include_patterns': ['*.py'],
            'exclude_patterns': []
        }
    }

    all_files = []
    location_summary = {}

    for location_key, config in source_locations.items():
        root_path = config['path']

        if not root_path.exists():
            print(f"⚠ Warning: {location_key} does not exist: {root_path}")
            location_summary[location_key] = {
                'path': str(root_path),
                'exists': False,
                'file_count': 0
            }
            continue

        print(f"\nScanning {location_key}: {root_path}")
        location_files = []

        # Get files based on patterns
        if config['recursive']:
            file_iter = root_path.rglob('*')
        else:
            file_iter = root_path.glob('*')

        for file_path in file_iter:
            if not file_path.is_file():
                continue

            # Check exclude patterns
            if any(excl in str(file_path) for excl in config['exclude_patterns']):
                continue

            # Check include patterns
            if config['include_patterns']:
                if not any(file_path.match(pattern) for pattern in config['include_patterns']):
                    continue

            try:
                file_info = {
                    'source_location': location_key,
                    'source_path_root': str(root_path),
                    'absolute_path': str(file_path),
                    'relative_path': str(file_path.relative_to(root_path)),
                    'filename': file_path.name,
                    'sha256': hash_file(file_path),
                    'size_bytes': file_path.stat().st_size,
                    'file_type': file_path.suffix,
                    'mtime': file_path.stat().st_mtime
                }

                location_files.append(file_info)
                all_files.append(file_info)

            except Exception as e:
                print(f"  ⚠ Warning: Failed to process {file_path}: {e}")

        location_summary[location_key] = {
            'path': str(root_path),
            'description': config['description'],
            'exists': True,
            'file_count': len(location_files),
            'files': [f['filename'] for f in location_files[:10]]  # First 10 files
        }

        print(f"  Found: {len(location_files)} files")

    # Sort all files deterministically
    all_files.sort(key=lambda x: (x['source_location'], x['relative_path'], x['filename']))

    result = {
        'audit_timestamp': datetime.utcnow().isoformat() + 'Z',
        'source_locations': location_summary,
        'files': all_files,
        'total_count': len(all_files),
        'breakdown_by_location': {
            loc: len([f for f in all_files if f['source_location'] == loc])
            for loc in source_locations.keys()
        },
        'breakdown_by_type': {
            ext: len([f for f in all_files if f['file_type'] == ext])
            for ext in set(f['file_type'] for f in all_files)
        }
    }

    output_path = Path('.migration/mapping/UPDATED_source_manifest.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"AUDIT COMPLETE")
    print(f"{'='*70}")
    print(f"Total files found: {len(all_files)}")
    print(f"\nBreakdown by location:")
    for loc, count in result['breakdown_by_location'].items():
        if count > 0:
            print(f"  {loc}: {count} files")

    print(f"\nBreakdown by type:")
    for ext, count in result['breakdown_by_type'].items():
        print(f"  {ext}: {count} files")

    print(f"\nManifest saved to: {output_path}")

    return result


if __name__ == '__main__':
    audit_source_locations()
