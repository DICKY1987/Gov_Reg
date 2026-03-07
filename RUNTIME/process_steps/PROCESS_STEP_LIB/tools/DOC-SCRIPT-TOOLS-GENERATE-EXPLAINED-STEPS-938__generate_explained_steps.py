#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-GENERATE-EXPLAINED-STEPS-938
"""
Generate plain English explanation document for all 274 steps

DOC_ID: DOC-SCRIPT-TOOLS-GENERATE-EXPLAINED-STEPS-938
"""
import yaml
from pathlib import Path

def layman_explain(step):
    """Create a plain English explanation of what a step does"""
    name = step.get('name', 'No name')
    operation = step.get('operation_kind', 'operation')

    lower_name = name.lower()

    # Pattern-based explanations
    if 'load' in lower_name:
        target = lower_name.replace('load', '').strip()
        return f'Load and read {target} into memory for use'
    elif 'parse' in lower_name:
        target = lower_name.replace('parse', '').strip()
        return f'Read and interpret the structure of {target}'
    elif 'create' in lower_name:
        target = lower_name.replace('create', '').strip()
        return f'Create a new {target} in the system'
    elif 'update' in lower_name:
        target = lower_name.replace('update', '').strip()
        return f'Modify or update existing {target}'
    elif 'invoke' in lower_name or 'call' in lower_name:
        target = lower_name.replace('invoke', '').replace('call', '').strip()
        return f'Start or activate {target}'
    elif 'checkpoint' in lower_name or 'complete' in lower_name:
        return f'Save progress: {name}'
    elif 'guardrail' in lower_name:
        return f'Check safety rules and constraints'
    elif 'transition' in lower_name:
        return f'Move workflow to next state or phase'
    elif 'validate' in lower_name or 'verify' in lower_name:
        target = lower_name.replace('validate', '').replace('verify', '').strip()
        return f'Check that {target} is correct'
    elif 'generate' in lower_name:
        target = lower_name.replace('generate', '').strip()
        return f'Automatically create {target}'
    elif 'scan' in lower_name or 'discover' in lower_name:
        target = lower_name.replace('scan', '').replace('discover', '').strip()
        return f'Search for and find {target}'
    elif 'write' in lower_name or 'save' in lower_name:
        target = lower_name.replace('write', '').replace('save', '').strip()
        return f'Write {target} to disk'
    elif 'execute' in lower_name or 'run' in lower_name:
        target = lower_name.replace('execute', '').replace('run', '').strip()
        return f'Run and execute {target}'
    elif 'sync' in lower_name:
        target = lower_name.replace('sync', '').strip()
        return f'Synchronize {target} with other systems'
    elif 'initialize' in lower_name or 'init' in lower_name:
        target = lower_name.replace('initialize', '').replace('init', '').strip()
        return f'Set up and prepare {target}'
    else:
        # Generic based on operation kind
        ops = {
            'initialization': 'Set up and prepare the system component',
            'discovery': 'Find and identify required items',
            'validation': 'Check and verify correctness',
            'analysis': 'Examine and understand the data',
            'transformation': 'Convert data to a different format',
            'generation': 'Automatically create new content',
            'execution': 'Run and complete the task',
            'persistence': 'Save data to disk for later use'
        }
        return ops.get(operation, name)

def main():
    # Load schema
    schema_path = Path(__file__).parent.parent / 'schemas' / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    steps = schema['steps']
    print(f'Loaded {len(steps)} steps')

    # Group by phase
    phases = {}
    for step in steps:
        step_id = step.get('step_id', 'NO_ID')
        phase_num = step_id.split('-')[1] if '-' in step_id else '0'

        if phase_num not in phases:
            phases[phase_num] = []
        phases[phase_num].append(step)

    # Phase information
    phase_info = {
        '1': {'name': 'BOOTSTRAP', 'full': 'Environment Setup and Initialization', 'contract': 'IO_CONTRACT_BOOTSTRAP.yaml'},
        '2': {'name': 'DISCOVERY', 'full': 'Pattern and Requirement Discovery', 'contract': 'IO_CONTRACT_DISCOVERY.yaml'},
        '3': {'name': 'DESIGN', 'full': 'Solution Design and Planning', 'contract': 'IO_CONTRACT_DESIGN.yaml'},
        '4': {'name': 'APPROVAL', 'full': 'Review and Approval', 'contract': 'IO_CONTRACT_APPROVAL.yaml'},
        '5': {'name': 'REGISTRATION', 'full': 'Component Registration', 'contract': 'IO_CONTRACT_REGISTRATION.yaml'},
        '6': {'name': 'EXECUTION', 'full': 'Task Execution', 'contract': 'IO_CONTRACT_EXECUTION.yaml'},
        '7': {'name': 'CONSOLIDATION', 'full': 'Results Aggregation', 'contract': 'IO_CONTRACT_CONSOLIDATION.yaml'},
        '8': {'name': 'MAINTENANCE', 'full': 'Cleanup and Maintenance', 'contract': 'IO_CONTRACT_MAINTENANCE.yaml'},
        '9': {'name': 'SYNC_FINALIZE', 'full': 'Final Sync and Completion', 'contract': 'IO_CONTRACT_SYNC_FINALIZE.yaml'}
    }

    # Create document
    output_path = Path(__file__).parent.parent / 'guides' / 'ALL_274_STEPS_EXPLAINED.md'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# All 274 End-to-End Process Steps - Explained in Plain English\n\n')
        f.write('**Generated:** December 18, 2025 8:07 PM EST\n\n')
        f.write('**Source:** schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml\n\n')
        f.write('**Total Steps:** 274 steps across 9 phases\n\n')
        f.write('**Format:** Each step explained in plain English for easy understanding\n\n')
        f.write('**Step IDs:** Changed from E2E-X-YYY to PHASE_NAME-YYY format\n\n')
        f.write('---\n\n')

        for phase_num in sorted(phases.keys()):
            phase_steps = phases[phase_num]
            info = phase_info.get(phase_num, {'name': f'PHASE_{phase_num}', 'full': 'Unknown', 'contract': 'IO_CONTRACT.yaml'})

            # Phase header
            f.write('=' * 80 + '\n')
            f.write(f'# PHASE {phase_num}: {info["name"]}\n')
            f.write(f'## {info["full"]}\n\n')
            f.write(f'**Step Count:** {len(phase_steps)}\n\n')
            f.write(f'**Input/Output Contract:** `{info["contract"]}`\n\n')
            f.write('=' * 80 + '\n\n')

            # Sort and write steps
            phase_steps.sort(key=lambda s: s.get('step_id', ''))

            for step in phase_steps:
                old_id = step.get('step_id', 'NO_ID')
                step_num = old_id.split('-')[2] if '-' in old_id else '001'
                new_id = f'{info["name"]}-{step_num}'

                name = step.get('name', 'No name')
                explanation = layman_explain(step)

                f.write(f'### {new_id}\n')
                f.write(f'**What:** {name}\n\n')
                f.write(f'**Plain English:** {explanation}\n\n')
                f.write('---\n\n')

            # Spacing between phases
            f.write('\n\n')

    print(f'✅ Created {output_path}')

if __name__ == '__main__':
    main()
