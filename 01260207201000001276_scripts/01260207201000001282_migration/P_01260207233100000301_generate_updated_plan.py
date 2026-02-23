"""
Generate updated migration plan based on actual source audit.
"""
import json
from pathlib import Path
from datetime import datetime


def generate_updated_plan():
    """Generate updated migration plan with actual paths and counts."""

    # Load the audit results
    with open('.migration/mapping/UPDATED_source_manifest.json', 'r', encoding='utf-8') as f:
        audit = json.load(f)

    # Load baseline
    with open('.migration/reports/PRE_MIGRATION_TEST_BASELINE.json', 'r', encoding='utf-8') as f:
        baseline = json.load(f)

    total_files = audit['total_count']
    baseline_count = baseline['baseline_count']

    # Define target directory mappings
    target_mappings = {
        'location_1_eafix_repo_autoops': {
            'base_target': 'src/repo_autoops',
            'strategy': 'preserve_structure',
            'description': 'Main repo_autoops code'
        },
        'location_2a_eafix_registry_writer': {
            'base_target': 'src/registry_writer',
            'strategy': 'preserve_structure',
            'description': 'Registry writer service'
        },
        'location_2b_eafix_data_validator': {
            'base_target': 'src/validators',
            'strategy': 'preserve_structure',
            'description': 'Data validator service'
        },
        'location_2c_eafix_generator': {
            'base_target': 'src/generators',
            'strategy': 'preserve_structure',
            'description': 'Generator service'
        },
        'location_2d_eafix_flow_orchestrator': {
            'base_target': 'src/orchestrators',
            'strategy': 'preserve_structure',
            'description': 'Flow orchestrator service'
        },
        'location_2e_eafix_signal_generator': {
            'base_target': 'src/generators',
            'strategy': 'preserve_structure',
            'description': 'Signal generator plugins'
        },
        'location_3_eafix_scripts': {
            'base_target': 'scripts',
            'strategy': 'preserve_structure',
            'description': 'Script files'
        },
        'location_4_eafix_dir_mgmt': {
            'base_target': 'scripts/utilities',
            'strategy': 'flatten',
            'description': 'Directory management utilities'
        },
        'location_5_all_ai_governance': {
            'base_target': 'docs/governance',
            'strategy': 'flatten',
            'description': 'Governance documentation'
        },
        'location_6_all_ai_mapp_py': {
            'base_target': 'scripts/parsers',
            'strategy': 'flatten',
            'description': 'Parser implementations'
        }
    }

    # Calculate target paths for each file
    files_with_targets = []
    for file_info in audit['files']:
        location = file_info['source_location']
        mapping = target_mappings.get(location, {})

        if mapping.get('strategy') == 'preserve_structure':
            # Keep the relative path structure
            target_path = f"{mapping['base_target']}/{file_info['relative_path']}"
        elif mapping.get('strategy') == 'flatten':
            # Just filename in target directory
            target_path = f"{mapping['base_target']}/{file_info['filename']}"
        else:
            target_path = f"src/misc/{file_info['filename']}"

        files_with_targets.append({
            **file_info,
            'target_path': target_path,
            'target_directory': str(Path(target_path).parent),
            'target_filename': Path(target_path).name
        })

    # Calculate expected final registry count
    init_files_count = 15  # Estimate for __init__.py files needed
    buffer = int(total_files * 0.1)
    expected_final_count = baseline_count + total_files + init_files_count

    plan = {
        'plan_version': '3.1',
        'generated': datetime.utcnow().isoformat() + 'Z',
        'status': 'UPDATED - READY FOR EXECUTION',
        'supersedes': 'MIGRATION_PLAN_FINAL_MERGED.md v3.0',

        'summary': {
            'description': 'Updated migration plan with actual source locations',
            'baseline_registry_count': baseline_count,
            'files_to_migrate': total_files,
            'init_files_to_create': init_files_count,
            'buffer': buffer,
            'expected_final_count': expected_final_count,
            'expected_range': [expected_final_count - buffer, expected_final_count + buffer]
        },

        'source_locations': target_mappings,

        'files': files_with_targets,

        'breakdown': {
            'by_location': audit['breakdown_by_location'],
            'by_type': audit['breakdown_by_type'],
            'by_target_directory': {}
        },

        'changes_from_v3_0': [
            'Updated source paths (eafix-modular/repo_autoops instead of registry_files/GOVERNANCE)',
            'Increased file count from 58-66 to 73',
            'Added 10 source locations (split services into specific ones)',
            'Updated baseline count to actual registry size',
            'Added service-based directory mapping strategy'
        ]
    }

    # Calculate breakdown by target directory
    for file_info in files_with_targets:
        target_dir = file_info['target_directory']
        plan['breakdown']['by_target_directory'][target_dir] = \
            plan['breakdown']['by_target_directory'].get(target_dir, 0) + 1

    # Save updated plan
    output_path = Path('.migration/mapping/UPDATED_MIGRATION_PLAN.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"{'='*70}")
    print(f"UPDATED MIGRATION PLAN GENERATED")
    print(f"{'='*70}")
    print(f"\nSummary:")
    print(f"  Files to migrate: {total_files}")
    print(f"  Current registry: {baseline_count} entries")
    print(f"  Expected final: {expected_final_count} ± {buffer}")
    print(f"\nChanges from original plan:")
    for change in plan['changes_from_v3_0']:
        print(f"  • {change}")

    print(f"\nTop target directories:")
    sorted_targets = sorted(
        plan['breakdown']['by_target_directory'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for target_dir, count in sorted_targets[:10]:
        print(f"  {target_dir}: {count} files")

    print(f"\nPlan saved to: {output_path}")

    return plan


if __name__ == '__main__':
    generate_updated_plan()
