#!/usr/bin/env python3
# DOC_LINK: DOC-TOOL-ID-TYPE-MANAGER-001
# DOC_ID: DOC-TOOL-ID-TYPE-MANAGER-001
"""
doc_id: DOC-TOOL-ID-TYPE-MANAGER-001
Lifecycle management CLI for ID types
"""

import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime
import shutil

REGISTRY_FILE = Path(__file__).parent / "ID_TYPE_REGISTRY.yaml"

def load_registry():
    """Load the ID type registry"""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_registry(registry):
    """Save the ID type registry"""
    registry['meta']['updated_utc'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def list_types(args):
    """List all ID types"""
    registry = load_registry()

    if args.status:
        types = [t for t in registry['id_types'] if t['status'] == args.status]
    else:
        types = registry['id_types']

    print(f"\n{'='*80}")
    print(f"ID TYPE REGISTRY - {len(types)} types")
    print(f"{'='*80}\n")

    for id_type in types:
        status_icon = {
            'production': '✅',
            'active': '🔄',
            'planned': '📋',
            'deprecated': '⚠️',
            'retired': '❌'
        }.get(id_type['status'], '❓')

        print(f"{status_icon} {id_type['type_id']:<20} {id_type['name']:<35} {id_type['status']}")
        if args.verbose:
            print(f"   Format: {id_type['format']}")
            print(f"   Classification: {id_type['classification']}")
            print(f"   Priority: {id_type['priority']}")
            print()

def register_type(args):
    """Register a new ID type"""
    registry = load_registry()

    # Check if type already exists
    existing = next((t for t in registry['id_types'] if t['type_id'] == args.type), None)
    if existing:
        print(f"❌ Error: Type '{args.type}' already exists")
        return 1

    new_type = {
        'type_id': args.type,
        'name': args.name,
        'classification': args.classification,
        'tier': args.tier,
        'format': args.format,
        'format_regex': args.regex,
        'status': 'planned',
        'priority': args.priority,
        'owner': args.owner,
        'registry_file': args.registry_file,
        'description': args.description,
    }

    if args.categories:
        new_type['categories'] = args.categories.split(',')

    registry['id_types'].append(new_type)
    registry['summary']['total_types'] += 1
    registry['summary']['planned'] += 1

    # Log the change
    if 'lifecycle_log' not in registry:
        registry['lifecycle_log'] = []

    registry['lifecycle_log'].append({
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'action': 'registered',
        'type_id': args.type,
        'notes': f"Registered new ID type: {args.name}"
    })

    save_registry(registry)
    print(f"✅ Successfully registered ID type: {args.type}")
    return 0

def update_status(args):
    """Update the status of an ID type"""
    registry = load_registry()

    id_type = next((t for t in registry['id_types'] if t['type_id'] == args.type), None)
    if not id_type:
        print(f"❌ Error: Type '{args.type}' not found")
        return 1

    old_status = id_type['status']
    new_status = args.status

    # Validate status transition
    valid_transitions = {
        'planned': ['active', 'deprecated'],
        'active': ['production', 'deprecated'],
        'production': ['deprecated'],
        'deprecated': ['retired'],
        'retired': []
    }

    if new_status not in valid_transitions.get(old_status, []):
        print(f"❌ Error: Invalid transition from '{old_status}' to '{new_status}'")
        print(f"   Valid transitions from '{old_status}': {', '.join(valid_transitions[old_status])}")
        return 1

    # Update status
    id_type['status'] = new_status

    # Update summary counts
    registry['summary'][old_status] = registry['summary'].get(old_status, 0) - 1
    registry['summary'][new_status] = registry['summary'].get(new_status, 0) + 1

    # Log the change
    registry['lifecycle_log'].append({
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'action': 'status_change',
        'type_id': args.type,
        'old_status': old_status,
        'new_status': new_status,
        'notes': args.notes or f"Status changed from {old_status} to {new_status}"
    })

    save_registry(registry)
    print(f"✅ Successfully updated {args.type}: {old_status} → {new_status}")
    return 0

def scaffold_type(args):
    """Create directory structure for a new ID type"""
    registry = load_registry()

    id_type = next((t for t in registry['id_types'] if t['type_id'] == args.type), None)
    if not id_type:
        print(f"❌ Error: Type '{args.type}' not found in registry")
        return 1

    if id_type['classification'] == 'runtime':
        print(f"⚠️  Warning: Runtime IDs don't need scaffolding (no persistent structure)")
        return 0

    # Determine base directory
    base_dir = Path(__file__).parent / args.type

    if base_dir.exists() and not args.force:
        print(f"❌ Error: Directory already exists: {base_dir}")
        print(f"   Use --force to overwrite")
        return 1

    # Create 7-layer structure (for minted/derived types)
    if id_type['classification'] in ['minted', 'derived']:
        layers = [
            '1_CORE_OPERATIONS',
            '2_VALIDATION_FIXING',
            '3_AUTOMATION_HOOKS',
            '4_REPORTING_MONITORING',
            '5_REGISTRY_DATA',
            '6_TESTS',
            '7_CLI_INTERFACE',
            'common',
            'docs'
        ]

        print(f"\n📁 Creating directory structure for {args.type}...")
        base_dir.mkdir(parents=True, exist_ok=True)

        for layer in layers:
            layer_dir = base_dir / layer
            layer_dir.mkdir(exist_ok=True)

            # Create __init__.py for Python packages
            if layer not in ['docs']:
                (layer_dir / '__init__.py').touch()

            print(f"   ✅ Created {layer}/")

        # Create basic files
        (base_dir / 'README.md').write_text(f"""# {id_type['name']}

**Type ID**: {args.type}
**Status**: {id_type['status']}
**Classification**: {id_type['classification']}
**Format**: `{id_type['format']}`

## Overview

{id_type.get('description', 'TODO: Add description')}

## Directory Structure

- `1_CORE_OPERATIONS/` - Scanner and assigner scripts
- `2_VALIDATION_FIXING/` - Validators for format, uniqueness, sync, coverage, references
- `3_AUTOMATION_HOOKS/` - Pre-commit hooks, watchers, scheduled tasks
- `4_REPORTING_MONITORING/` - Coverage reports, dashboards, alerts
- `5_REGISTRY_DATA/` - Registry file and inventory snapshots
- `6_TESTS/` - Unit and integration tests
- `7_CLI_INTERFACE/` - Command-line interface
- `common/` - Shared validation rules and utilities
- `docs/` - Additional documentation

## Implementation Status

- [ ] Scanner implemented
- [ ] Assigner implemented
- [ ] Format validator implemented
- [ ] Uniqueness validator implemented
- [ ] Sync validator implemented
- [ ] Coverage validator implemented
- [ ] Reference validator implemented
- [ ] CLI implemented
- [ ] Tests passing
- [ ] Documentation complete

## Next Steps

1. Implement scanner in `1_CORE_OPERATIONS/`
2. Create validation rules in `common/rules.py`
3. Implement validators in `2_VALIDATION_FIXING/`
4. Add tests in `6_TESTS/`
5. Create CLI in `7_CLI_INTERFACE/`
""")

        # Create DIR_MANIFEST.yaml
        (base_dir / 'DIR_MANIFEST.yaml').write_text(f"""---
doc_id: DOC-MANIFEST-{args.type.upper().replace('_', '-')}-001
directory_name: {args.type}
owner: {id_type['owner']}
purpose: Implementation of {id_type['name']} stable ID system
status: scaffolded
created: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}

files:
  tracked: []
  generated: []

dependencies:
  internal: []
  external: []

notes: "Scaffolded by id_type_manager.py"
""")

        print(f"\n✅ Successfully scaffolded {args.type}")
        print(f"   Location: {base_dir}")
        print(f"\n📝 Next: Implement scanner in {base_dir}/1_CORE_OPERATIONS/")

    else:
        print(f"ℹ️  Classification '{id_type['classification']}' - minimal scaffolding")
        base_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created base directory: {base_dir}")

    return 0

def info(args):
    """Show detailed information about an ID type"""
    registry = load_registry()

    id_type = next((t for t in registry['id_types'] if t['type_id'] == args.type), None)
    if not id_type:
        print(f"❌ Error: Type '{args.type}' not found")
        return 1

    print(f"\n{'='*80}")
    print(f"ID TYPE: {id_type['type_id']}")
    print(f"{'='*80}\n")

    print(f"Name:           {id_type['name']}")
    print(f"Status:         {id_type['status']}")
    print(f"Classification: {id_type['classification']}")
    print(f"Tier:           {id_type['tier']}")
    print(f"Priority:       {id_type['priority']}")
    print(f"Owner:          {id_type['owner']}")
    print(f"\nFormat:         {id_type['format']}")
    print(f"Regex:          {id_type['format_regex']}")

    if 'categories' in id_type:
        print(f"\nCategories:")
        for cat in id_type['categories']:
            print(f"  - {cat}")

    if 'validators' in id_type:
        print(f"\nValidators:")
        for val in id_type['validators']:
            print(f"  - {val}")

    if 'coverage' in id_type:
        cov = id_type['coverage']
        print(f"\nCoverage:")
        print(f"  Total IDs:  {cov.get('total_ids', 'N/A')}")
        print(f"  Percentage: {cov.get('percentage', 'N/A')}%")
        print(f"  Target:     {cov.get('target', 'N/A')}%")

    print(f"\nDescription:")
    print(f"  {id_type.get('description', 'N/A')}")

    if 'notes' in id_type:
        print(f"\nNotes:")
        print(f"  {id_type['notes']}")

    print()
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='Manage ID type lifecycle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all ID types
  python id_type_manager.py list

  # List only production types
  python id_type_manager.py list --status production

  # Register new type
  python id_type_manager.py register --type schema_id --name "Schema ID" \\
    --classification minted --format "SCHEMA-{TYPE}-{NAME}-{SEQ}" \\
    --regex "^SCHEMA-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$"

  # Update status
  python id_type_manager.py update-status --type schema_id --status active

  # Scaffold directory structure
  python id_type_manager.py scaffold --type schema_id

  # Show type info
  python id_type_manager.py info --type doc_id
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List ID types')
    list_parser.add_argument('--status', choices=['production', 'active', 'planned', 'deprecated', 'retired'],
                            help='Filter by status')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed info')

    # Register command
    reg_parser = subparsers.add_parser('register', help='Register new ID type')
    reg_parser.add_argument('--type', required=True, help='Type ID (e.g., schema_id)')
    reg_parser.add_argument('--name', required=True, help='Human-readable name')
    reg_parser.add_argument('--classification', required=True,
                           choices=['minted', 'derived', 'runtime', 'natural'],
                           help='ID classification')
    reg_parser.add_argument('--tier', type=int, choices=[1, 2, 3], default=2,
                           help='Tier (1=critical, 2=core, 3=supporting)')
    reg_parser.add_argument('--format', required=True, help='Format string')
    reg_parser.add_argument('--regex', required=True, help='Format regex pattern')
    reg_parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'],
                           default='medium', help='Priority level')
    reg_parser.add_argument('--owner', required=True, help='Team/person responsible')
    reg_parser.add_argument('--registry-file', required=True, help='Path to registry file')
    reg_parser.add_argument('--description', required=True, help='Description')
    reg_parser.add_argument('--categories', help='Comma-separated category list')

    # Update status command
    status_parser = subparsers.add_parser('update-status', help='Update ID type status')
    status_parser.add_argument('--type', required=True, help='Type ID')
    status_parser.add_argument('--status', required=True,
                              choices=['active', 'production', 'deprecated', 'retired'],
                              help='New status')
    status_parser.add_argument('--notes', help='Notes about the change')

    # Scaffold command
    scaffold_parser = subparsers.add_parser('scaffold', help='Create directory structure')
    scaffold_parser.add_argument('--type', required=True, help='Type ID')
    scaffold_parser.add_argument('--force', action='store_true', help='Overwrite existing')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show type information')
    info_parser.add_argument('--type', required=True, help='Type ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'list': list_types,
        'register': register_type,
        'update-status': update_status,
        'scaffold': scaffold_type,
        'info': info
    }

    return commands[args.command](args)

if __name__ == '__main__':
    sys.exit(main())
