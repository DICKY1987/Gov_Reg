"""
Discover and enumerate mapp_py parser files.
Expected: 16-19 files (8 shims + 7 implementations + 1 loader + 0-3 optional docs)
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


def discover_mapp_py_files(mapp_py_root, output_path):
    """
    Enumerate mapp_py files with corrected count expectations.

    Args:
        mapp_py_root: Path to mapp_py directory
        output_path: Where to save manifest JSON
    """
    mapp_py_root = Path(mapp_py_root)

    if not mapp_py_root.exists():
        raise FileNotFoundError(f"mapp_py root not found: {mapp_py_root}")

    manifest = []

    # 8 shims: DOC-SCRIPT-1267 through 1274
    print("Searching for shims (DOC-SCRIPT-1267 through 1274)...")
    for docid in range(1267, 1275):
        pattern = f"DOC-SCRIPT-{docid}*"
        matches = list(mapp_py_root.glob(pattern))
        if matches:
            for file_path in matches:
                if file_path.is_file():
                    print(f"  Found shim: {file_path.name}")
                    manifest.append({
                        'category': 'shim',
                        'docid': f'DOC-SCRIPT-{docid}',
                        'absolute_path': str(file_path),
                        'filename': file_path.name,
                        'sha256': hash_file(file_path),
                        'size_bytes': file_path.stat().st_size
                    })

    # 7 implementations: DOC-SCRIPT-0992 through 0998
    print("Searching for implementations (DOC-SCRIPT-0992 through 0998)...")
    for docid in range(992, 999):
        pattern = f"DOC-SCRIPT-{docid}*"
        matches = list(mapp_py_root.glob(pattern))
        if matches:
            for file_path in matches:
                if file_path.is_file():
                    print(f"  Found implementation: {file_path.name}")
                    manifest.append({
                        'category': 'implementation',
                        'docid': f'DOC-SCRIPT-{docid}',
                        'absolute_path': str(file_path),
                        'filename': file_path.name,
                        'sha256': hash_file(file_path),
                        'size_bytes': file_path.stat().st_size
                    })

    # 1 loader: _docid_loader.py
    print("Searching for loader (_docid_loader.py)...")
    loader = mapp_py_root / '_docid_loader.py'
    if loader.exists():
        print(f"  Found loader: {loader.name}")
        manifest.append({
            'category': 'loader',
            'docid': None,
            'absolute_path': str(loader),
            'filename': loader.name,
            'sha256': hash_file(loader),
            'size_bytes': loader.stat().st_size
        })

    # 0-3 optional: spec/test docs (Decision D10)
    print("Searching for optional docs (spec.md, test.py, README.md)...")
    existing_paths = [Path(f['absolute_path']) for f in manifest]
    for pattern in ['*spec.md', '*test.py', 'README.md']:
        for file_path in mapp_py_root.glob(pattern):
            if file_path.is_file() and file_path not in existing_paths:
                print(f"  Found optional doc: {file_path.name}")
                manifest.append({
                    'category': 'optional_doc',
                    'docid': None,
                    'absolute_path': str(file_path),
                    'filename': file_path.name,
                    'sha256': hash_file(file_path),
                    'size_bytes': file_path.stat().st_size
                })

    result = {
        'files': manifest,
        'total_count': len(manifest),
        'expected_range': [16, 19],
        'breakdown': {
            'shims': len([f for f in manifest if f['category'] == 'shim']),
            'implementations': len([f for f in manifest if f['category'] == 'implementation']),
            'loader': len([f for f in manifest if f['category'] == 'loader']),
            'optional_docs': len([f for f in manifest if f['category'] == 'optional_doc'])
        },
        'variance_acceptable': 16 <= len(manifest) <= 19,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ mapp_py manifest: {len(manifest)} files")
    print(f"  Shims: {result['breakdown']['shims']}")
    print(f"  Implementations: {result['breakdown']['implementations']}")
    print(f"  Loader: {result['breakdown']['loader']}")
    print(f"  Optional docs: {result['breakdown']['optional_docs']}")

    if not result['variance_acceptable']:
        print(f"⚠ Warning: Count {len(manifest)} outside expected range {result['expected_range']}")

    return result


if __name__ == '__main__':
    import sys

    mapp_py_root = Path(r'C:\Users\richg\ALL_AI\mapp_py')
    output_path = Path('.migration/mapping/mapp_py_manifest.json')

    if len(sys.argv) > 1:
        mapp_py_root = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    discover_mapp_py_files(mapp_py_root, output_path)
