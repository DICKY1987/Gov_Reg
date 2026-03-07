#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-IDENTIFY-MISSING-FILES-950
"""
PFA Missing Implementation Files Identifier

Identifies process steps that are missing implementation file attachments
and generates a report for automated file discovery and attachment.

Usage:
    python pfa_identify_missing_files.py [schema_file] [--output json|yaml|md]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-IDENTIFY-MISSING-FILES-950

import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the unified schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def analyze_missing_files(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze steps missing implementation files."""
    steps = schema.get('steps', [])

    steps_without_files = []
    steps_with_files = []

    for step in steps:
        step_info = {
            'step_id': step.get('step_id'),
            'name': step.get('name'),
            'phase': step.get('universal_phase'),
            'operation_kind': step.get('operation_kind'),
            'responsible_component': step.get('responsible_component'),
            'description': step.get('description', ''),
            'implementation_files': step.get('implementation_files', []),
            'artifact_registry_refs': step.get('artifact_registry_refs', [])
        }

        if not step.get('implementation_files'):
            steps_without_files.append(step_info)
        else:
            steps_with_files.append(step_info)

    # Group by phase
    by_phase = {}
    for step in steps_without_files:
        phase = step['phase']
        if phase not in by_phase:
            by_phase[phase] = []
        by_phase[phase].append(step)

    # Group by operation kind
    by_operation = {}
    for step in steps_without_files:
        op = step['operation_kind']
        if op not in by_operation:
            by_operation[op] = []
        by_operation[op].append(step)

    return {
        'summary': {
            'total_steps': len(steps),
            'steps_with_files': len(steps_with_files),
            'steps_without_files': len(steps_without_files),
            'coverage_percentage': round(len(steps_with_files) / len(steps) * 100, 2) if steps else 0,
            'analysis_date': datetime.utcnow().isoformat()
        },
        'steps_without_files': steps_without_files,
        'by_phase': {phase: len(steps) for phase, steps in by_phase.items()},
        'by_operation': {op: len(steps) for op, steps in by_operation.items()},
        'phase_details': by_phase
    }


def generate_markdown_report(analysis: Dict[str, Any]) -> str:
    """Generate markdown report."""
    summary = analysis['summary']

    md = f"""# Process Steps Missing Implementation Files

**Generated**: {summary['analysis_date']}

## Summary

- **Total Steps**: {summary['total_steps']}
- **Steps with Files**: {summary['steps_with_files']} ({summary['coverage_percentage']}%)
- **Steps WITHOUT Files**: {summary['steps_without_files']} ({100 - summary['coverage_percentage']:.2f}%)

## Missing Files by Phase

"""

    for phase, count in sorted(analysis['by_phase'].items()):
        md += f"- **{phase}**: {count} steps\n"

    md += "\n## Missing Files by Operation Kind\n\n"

    for op, count in sorted(analysis['by_operation'].items()):
        md += f"- **{op}**: {count} steps\n"

    md += "\n## Detailed List\n\n"

    for phase, steps in sorted(analysis['phase_details'].items()):
        md += f"\n### {phase} ({len(steps)} steps)\n\n"
        for step in steps:
            desc = step['description'][:100] + '...' if len(step['description']) > 100 else step['description']
            md += f"#### {step['step_id']}: {step['name']}\n\n"
            md += f"- **Operation**: {step['operation_kind']}\n"
            md += f"- **Component**: {step['responsible_component']}\n"
            md += f"- **Description**: {desc}\n"
            if step['artifact_registry_refs']:
                md += f"- **Artifact Refs**: {', '.join(step['artifact_registry_refs'])}\n"
            md += "\n"

    return md


def main():
    if len(sys.argv) < 2:
        schema_path = Path(__file__).parent.parent / 'schemas' / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
    else:
        schema_path = Path(sys.argv[1])

    output_format = 'md'
    if len(sys.argv) >= 3 and sys.argv[2].startswith('--output='):
        output_format = sys.argv[2].split('=')[1]

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)

    print(f"Loading schema: {schema_path}")
    schema = load_schema(schema_path)

    print("Analyzing missing implementation files...")
    analysis = analyze_missing_files(schema)

    # Output
    output_dir = Path(__file__).parent.parent / 'workspace'
    output_dir.mkdir(exist_ok=True)

    if output_format == 'json':
        output_file = output_dir / 'missing_files_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)
        print(f"JSON report written to: {output_file}")

    elif output_format == 'yaml':
        output_file = output_dir / 'missing_files_analysis.yaml'
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(analysis, f, default_flow_style=False, sort_keys=False)
        print(f"YAML report written to: {output_file}")

    else:  # markdown
        output_file = output_dir / 'missing_files_analysis.md'
        md_report = generate_markdown_report(analysis)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"Markdown report written to: {output_file}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total steps: {analysis['summary']['total_steps']}")
    print(f"Steps with files: {analysis['summary']['steps_with_files']} ({analysis['summary']['coverage_percentage']}%)")
    print(f"Steps without files: {analysis['summary']['steps_without_files']}")
    print("\nTop phases missing files:")
    for phase, count in sorted(analysis['by_phase'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {phase}: {count}")


if __name__ == '__main__':
    main()
