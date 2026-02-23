#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0991
"""
Generator 1: ID Type Registry Bootstrapper
Creates registry files, directory structure, and documentation for a new ID type.

Usage:
    python generate_id_registry.py <id_type>

Example:
    python generate_id_registry.py template_id
"""

import argparse
import os
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
import hashlib
import re


def load_id_type_spec(repo_root: Path, id_type: str) -> dict:
    """Load ID type specification from ID_TYPE_REGISTRY.yaml"""
    registry_path = repo_root / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "ID_TYPE_REGISTRY.yaml"

    if not registry_path.exists():
        raise FileNotFoundError(f"ID Type Registry not found at {registry_path}")

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Find the ID type spec
    for spec in registry.get('id_types', []):
        if spec.get('type_id') == id_type:
            return spec

    raise ValueError(f"ID type '{id_type}' not found in ID_TYPE_REGISTRY.yaml")


def generate_dir_id(path: str) -> str:
    """Generate a dir_id for the registry directory"""
    # Slugify path and hash
    path_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', path.replace('/', '-').replace('\\', '-'))
    path_slug = re.sub(r'-+', '-', path_slug).strip('-').upper()

    # Generate 8-char hash
    hash_obj = hashlib.sha256(path.encode('utf-8'))
    hash_str = hash_obj.hexdigest()[:8]

    return f"DIR-{path_slug}-{hash_str}"


def create_registry_file(repo_root: Path, spec: dict) -> Path:
    """Create the registry YAML file"""
    registry_file = spec.get('registry_file')
    if not registry_file:
        raise ValueError(f"No registry_file specified for {spec['type_id']}")

    registry_path = repo_root / registry_file
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine plural form of ID type
    type_id = spec['type_id']
    plural = type_id + 's' if not type_id.endswith('_id') else type_id.replace('_id', '_ids')

    # Generate registry content
    registry_content = {
        'doc_id': f"DOC-REGISTRY-{type_id.upper().replace('_', '-')}-001",
        'meta': {
            'version': '1.0.0',
            'created_utc': datetime.utcnow().isoformat() + 'Z',
            'updated_utc': datetime.utcnow().isoformat() + 'Z',
            'total_entries': 0,
            'owner': spec.get('owner', 'System Architecture'),
            'description': spec.get('description', f'Registry for {spec["name"]}')
        },
        plural: []
    }

    # Add categories if specified
    if spec.get('categories'):
        registry_content['categories'] = {cat: {'description': f'{cat} category'} for cat in spec['categories']}

    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry_content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Created registry file: {registry_path}")
    return registry_path


def create_dir_manifest(registry_dir: Path, spec: dict) -> Path:
    """Create DIR_MANIFEST.yaml for the registry directory"""
    manifest_path = registry_dir / "DIR_MANIFEST.yaml"

    manifest_content = {
        'dir_id': generate_dir_id(str(registry_dir.relative_to(registry_dir.parent.parent.parent))),
        'version': '1.0.0',
        'ownership': {
            'owner': spec.get('owner', 'System Architecture'),
            'created': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        },
        'purpose': f"Registry for {spec['name']} ({spec['type_id']})",
        'classification': spec.get('classification', 'minted'),
        'files': {
            'registries': [
                os.path.basename(spec.get('registry_file', ''))
            ],
            'documentation': ['README.md'],
            'metadata': ['DIR_MANIFEST.yaml', '.dir_id']
        }
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        yaml.dump(manifest_content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Created DIR_MANIFEST.yaml: {manifest_path}")
    return manifest_path


def create_dir_id_file(registry_dir: Path) -> Path:
    """Create .dir_id file"""
    dir_id_path = registry_dir / ".dir_id"
    dir_id = generate_dir_id(str(registry_dir.relative_to(registry_dir.parent.parent.parent)))

    from datetime import datetime, timezone
    dir_id_data = {
        "dir_id": dir_id,
        "repo_relative_path": str(registry_dir.relative_to(registry_dir.parent.parent.parent)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "1.0.0",
        "semantic_keys": [],
        "derivation": "slugified_path + blake2b_8char"
    }
    with open(dir_id_path, 'w', encoding='utf-8') as f:
        json.dump(dir_id_data, f, indent=2)

    print(f"✓ Created .dir_id: {dir_id}")
    return dir_id_path


def create_readme(registry_dir: Path, spec: dict) -> Path:
    """Create README.md from template"""
    readme_path = registry_dir / "README.md"

    # Extract key info
    type_id = spec['type_id']
    name = spec['name']
    format_str = spec.get('format', 'N/A')
    classification = spec.get('classification', 'minted')
    categories = spec.get('categories', [])
    owner = spec.get('owner', 'System Architecture')
    description = spec.get('description', '')

    readme_content = f"""# {name} Registry

**Type ID:** `{type_id}`
**Classification:** {classification}
**Owner:** {owner}
**Status:** Active

---

## Overview

{description}

**Format:** `{format_str}`

## Categories

"""

    if categories:
        for cat in categories:
            readme_content += f"- **{cat}** - {cat} category\n"
    else:
        readme_content += "*No categories defined*\n"

    readme_content += f"""
---

## Registry Structure

```yaml
{type_id}s:
  - id: {format_str.replace('{', '<').replace('}', '>')}
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New {name}

"""

    if classification == 'minted':
        readme_content += f"""1. Run the ID assigner: `python scripts/assign_{type_id}.py`
2. Or manually add to registry following format
3. Validate with: `python scripts/validators/validate_{type_id}.py`
"""
    elif classification == 'derived':
        readme_content += f"""IDs are automatically derived from source data.

**Derivation Rule:** {spec.get('derivation_rule', 'See specification')}
"""
    elif classification == 'runtime':
        readme_content += f"""IDs are generated at runtime using ULID.

**Format:** {format_str}
"""

    readme_content += f"""
---

## Validation

This registry is validated by:
- Format validator (regex: `{spec.get('format_regex', 'N/A')}`)
- Uniqueness validator
- Sync validator (registry ↔ filesystem)
"""

    if spec.get('validators'):
        readme_content += f"\n**Validators:**\n"
        for validator in spec['validators']:
            readme_content += f"- `{validator}`\n"

    readme_content += f"""
---

## Automation

"""

    automation = spec.get('automation', {})
    if automation:
        if automation.get('scanner'):
            readme_content += f"- ✅ Scanner: Auto-discovers entities\n"
        if automation.get('assigner'):
            readme_content += f"- ✅ Assigner: Auto-mints IDs\n"
        if automation.get('pre_commit'):
            readme_content += f"- ✅ Pre-commit hook: Validates before commit\n"
        if automation.get('watcher'):
            readme_content += f"- ✅ Watcher: Monitors for changes\n"
    else:
        readme_content += "*No automation configured*\n"

    readme_content += f"""
---

## References

- **ID Type Registry:** `RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml`
- **Governance:** `.ai/governance.md`
- **Universal Registry Schema:** `CONTEXT/docs/reference/UNIVERSAL_REGISTRY_SCHEMA_REFERENCE.md`

---

**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d')}
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✓ Created README.md: {readme_path}")
    return readme_path


def update_id_type_registry_status(repo_root: Path, id_type: str, new_status: str):
    """Update the status of an ID type in ID_TYPE_REGISTRY.yaml"""
    registry_path = repo_root / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "ID_TYPE_REGISTRY.yaml"

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Update status
    for spec in registry.get('id_types', []):
        if spec.get('type_id') == id_type:
            spec['status'] = new_status
            break

    # Update summary counts
    summary = registry.get('summary', {})
    if new_status == 'active':
        summary['planned'] = summary.get('planned', 0) - 1
        summary['active'] = summary.get('active', 0) + 1

    with open(registry_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✓ Updated ID_TYPE_REGISTRY.yaml: {id_type} status → {new_status}")


def main():
    parser = argparse.ArgumentParser(description='Generate registry infrastructure for an ID type')
    parser.add_argument('id_type', help='ID type to generate (e.g., template_id)')
    parser.add_argument('--repo-root', help='Repository root directory', default='.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be created without creating')

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    print(f"\n{'='*60}")
    print(f"Generator 1: ID Type Registry Bootstrapper")
    print(f"{'='*60}\n")
    print(f"ID Type: {args.id_type}")
    print(f"Repo Root: {repo_root}\n")

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be created\n")

    try:
        # Load spec
        print("📖 Loading ID type specification...")
        spec = load_id_type_spec(repo_root, args.id_type)
        print(f"✓ Loaded spec for: {spec['name']}")
        print(f"  Classification: {spec.get('classification', 'N/A')}")
        print(f"  Priority: {spec.get('priority', 'N/A')}")
        print(f"  Owner: {spec.get('owner', 'N/A')}\n")

        if args.dry_run:
            print("📋 Would create:")
            print(f"  - Registry file: {spec.get('registry_file', 'N/A')}")
            registry_dir = Path(spec.get('registry_file', '')).parent
            print(f"  - DIR_MANIFEST.yaml in {registry_dir}")
            print(f"  - .dir_id in {registry_dir}")
            print(f"  - README.md in {registry_dir}")
            print(f"  - Update ID_TYPE_REGISTRY.yaml status: planned → active")
            return

        # Create artifacts
        print("🔨 Creating registry artifacts...\n")

        registry_path = create_registry_file(repo_root, spec)
        registry_dir = registry_path.parent

        create_dir_manifest(registry_dir, spec)
        create_dir_id_file(registry_dir)
        create_readme(registry_dir, spec)

        # Update status
        update_id_type_registry_status(repo_root, args.id_type, 'active')

        print(f"\n{'='*60}")
        print(f"✅ Registry infrastructure created successfully!")
        print(f"{'='*60}\n")
        print(f"📁 Registry directory: {registry_dir}")
        print(f"\nNext steps:")
        print(f"  1. Review generated files")
        print(f"  2. Run: python scripts/generators/generate_id_validators.py {args.id_type}")
        print(f"  3. Run: python scripts/generators/generate_id_automation.py {args.id_type}")
        print(f"  4. Run: python scripts/generators/generate_id_docs.py {args.id_type}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
