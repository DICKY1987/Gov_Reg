"""
Backup source files with hash verification.
"""
import json
import shutil
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


def backup_sources(source_manifest_path, mapp_py_manifest_path, backup_root, output_path):
    """
    Create verified backups of all source files.

    Args:
        source_manifest_path: Path to source_manifest.json
        mapp_py_manifest_path: Path to mapp_py_manifest.json
        backup_root: Root directory for backups
        output_path: Where to save backup manifest
    """
    # Load manifests
    with open(source_manifest_path, 'r', encoding='utf-8') as f:
        source_manifest = json.load(f)
    with open(mapp_py_manifest_path, 'r', encoding='utf-8') as f:
        mapp_py_manifest = json.load(f)

    all_files = source_manifest['files'] + mapp_py_manifest['files']

    backup_root = Path(backup_root)
    backup_root.mkdir(parents=True, exist_ok=True)

    backup_records = []

    print(f"Backing up {len(all_files)} files...")

    for i, file_info in enumerate(all_files, 1):
        source_path = Path(file_info['absolute_path'])

        if not source_path.exists():
            print(f"⚠ Warning: Source file not found: {source_path}")
            continue

        # Preserve directory structure
        if 'relative_path' in file_info:
            rel_path = file_info['relative_path']
        else:
            # mapp_py files don't have relative_path
            rel_path = f"mapp_py/{source_path.name}"

        backup_path = backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(source_path, backup_path)

        # Verify hash
        original_hash = file_info.get('sha256') or hash_file(source_path)
        backup_hash = hash_file(backup_path)

        verified = original_hash == backup_hash

        backup_records.append({
            'original': str(source_path),
            'backup': str(backup_path),
            'original_hash': original_hash,
            'backup_hash': backup_hash,
            'verified': verified,
            'size_bytes': file_info.get('size_bytes', backup_path.stat().st_size)
        })

        status = "✓" if verified else "✗"
        print(f"  [{i}/{len(all_files)}] {status} {source_path.name}")

    result = {
        'backup_records': backup_records,
        'total_files': len(backup_records),
        'all_verified': all(r['verified'] for r in backup_records),
        'total_size_bytes': sum(r['size_bytes'] for r in backup_records),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    if not result['all_verified']:
        failed = [r for r in backup_records if not r['verified']]
        print(f"\n✗ Hash verification failed for {len(failed)} files!")
        for r in failed:
            print(f"  {r['original']}")
        raise Exception('Source backup verification failed!')

    print(f"\n✓ {len(backup_records)} source files backed up and verified")
    print(f"  Total size: {result['total_size_bytes'] / 1024 / 1024:.2f} MB")

    return result


if __name__ == '__main__':
    import sys

    source_manifest = Path('.migration/mapping/source_manifest.json')
    mapp_py_manifest = Path('.migration/mapping/mapp_py_manifest.json')
    backup_root = Path('.migration/backups/sources')
    output_path = Path('.migration/reports/SOURCE_BACKUP_MANIFEST.json')

    if len(sys.argv) > 1:
        source_manifest = Path(sys.argv[1])
    if len(sys.argv) > 2:
        mapp_py_manifest = Path(sys.argv[2])
    if len(sys.argv) > 3:
        backup_root = Path(sys.argv[3])
    if len(sys.argv) > 4:
        output_path = Path(sys.argv[4])

    backup_sources(source_manifest, mapp_py_manifest, backup_root, output_path)
