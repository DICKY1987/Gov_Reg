"""
Build source file manifest with metadata (sha256, size, type, mtime).
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


def build_manifest(source_roots, output_path, exclude_patterns=None):
    """
    Enumerate all files from source roots with metadata.

    Args:
        source_roots: List of Path objects to scan
        output_path: Where to save manifest JSON
        exclude_patterns: List of patterns to exclude (e.g., ['.dir_id', 'identity_pipeline.py'])
    """
    if exclude_patterns is None:
        exclude_patterns = ['.dir_id', 'identity_pipeline.py']

    manifest = []

    for root in source_roots:
        if not root.exists():
            print(f"⚠ Warning: {root} does not exist, skipping")
            continue

        print(f"Scanning {root}...")

        for file_path in root.rglob('*'):
            if not file_path.is_file():
                continue

            # Apply exclusion filters
            if any(pattern in file_path.name for pattern in exclude_patterns):
                print(f"  Skipping: {file_path.name} (matches exclusion pattern)")
                continue

            try:
                manifest.append({
                    'source_location': str(root),
                    'relative_path': str(file_path.relative_to(root)),
                    'absolute_path': str(file_path),
                    'filename': file_path.name,
                    'sha256': hash_file(file_path),
                    'size_bytes': file_path.stat().st_size,
                    'file_type': file_path.suffix,
                    'mtime': file_path.stat().st_mtime
                })
            except Exception as e:
                print(f"⚠ Warning: Failed to process {file_path}: {e}")

    # Sort deterministically
    manifest.sort(key=lambda x: (x['source_location'], x['relative_path'], x['filename']))

    result = {
        'files': manifest,
        'total_count': len(manifest),
        'expected_range': [58, 66],
        'variance_acceptable': abs(len(manifest) - 62) <= 4,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Manifest created: {len(manifest)} files")
    if not result['variance_acceptable']:
        print(f"⚠ Warning: File count {len(manifest)} outside expected range {result['expected_range']}")

    return result


if __name__ == '__main__':
    import sys

    # Default source roots
    source_roots = [
        Path(r'C:\Users\richg\eafix-modular\registry_files\GOVERNANCE'),
        Path(r'C:\Users\richg\ALL_AI\registry_files'),
        Path(r'C:\Users\richg\ALL_AI\GOVERNANCE\registries'),
    ]

    output_path = Path('.migration/mapping/source_manifest.json')

    # Allow override via command line
    if len(sys.argv) > 1:
        source_roots = [Path(p) for p in sys.argv[1:-1]]
        output_path = Path(sys.argv[-1])

    build_manifest(source_roots, output_path)
