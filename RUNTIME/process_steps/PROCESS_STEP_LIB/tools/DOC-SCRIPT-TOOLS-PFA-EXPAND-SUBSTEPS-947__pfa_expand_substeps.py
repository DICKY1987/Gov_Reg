#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-EXPAND-SUBSTEPS-947
"""
PFA Substep Expansion Tool

Expands high-level process steps into deterministic substeps based on
the December 18, 2025 patch specification.

Expands:
- P5-STEP-054 → 054.1-054.5 (event bus substeps)
- P5-STEP-061 → 061.1-061.3 (execution request validation)
- P5-STEP-062 → 062.1-062.5 (router workflow)
- P5-STEP-078 → 078.1-078.6 (patch lifecycle)
- MS-EXEC-004 → 140.1-140.5 (circuit breakers)

Usage:
    python pfa_expand_substeps.py --schema SCHEMA.yaml --output EXPANDED.yaml
    python pfa_expand_substeps.py --all  # Expands all source schemas
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-EXPAND-SUBSTEPS-947

import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Substep expansion definitions
SUBSTEP_EXPANSIONS = {
    'P5-STEP-054': {
        'parent_name': 'MINI_PIPE_orchestrator initializes event bus',
        'parent_phase': 'EXECUTION',
        'parent_component': 'mini_pipe_orchestrator',
        'parent_operation': 'initialization',
        'parent_order': 540,
        'substeps': [
            {
                'suffix': 'A',
                'name': 'Define EventEnvelope schema',
                'description': 'Define EventEnvelope schema (event_id, type, run_id, workstream_id, task_id, timestamp, payload)',
                'order_offset': 1,
            },
            {
                'suffix': 'B',
                'name': 'Implement publish/subscribe hooks',
                'description': 'Implement publish/subscribe hooks enabling Phase→Phase automation',
                'order_offset': 2,
            },
            {
                'suffix': 'C',
                'name': 'Emit ROUTING_COMPLETE event',
                'description': 'Emit ROUTING_COMPLETE after generating routing state files (.state/routing_decisions.json, .state/adapter_assignments.json)',
                'order_offset': 3,
            },
            {
                'suffix': 'D',
                'name': 'Emit TASK_FAILED event',
                'description': 'Emit TASK_FAILED on executor failure and persist .state/execution_results.json',
                'order_offset': 4,
            },
            {
                'suffix': 'E',
                'name': 'Schedule automatic retry on FIX_APPLIED',
                'description': 'On FIX_APPLIED, schedule automatic retry loop back to Phase 5 execution',
                'order_offset': 5,
            },
        ]
    },
    'P5-STEP-061': {
        'parent_name': 'For each task, MINI_PIPE_executor consults MINI_PIPE_router',
        'parent_phase': 'EXECUTION',
        'parent_component': 'mini_pipe_executor',
        'parent_operation': 'task_execution',
        'parent_order': 610,
        'substeps': [
            {
                'suffix': 'A',
                'name': 'Validate ExecutionRequest schema',
                'description': 'Validate ExecutionRequest schema; on invalid -> log + drop',
                'order_offset': 1,
            },
            {
                'suffix': 'B',
                'name': 'Resolve and validate PhaseSpec',
                'description': 'Resolve PhaseSpec instance for ER.phase_id and validate vs phase_spec.schema',
                'order_offset': 2,
            },
            {
                'suffix': 'C',
                'name': 'Enforce routing guards',
                'description': 'Enforce scope containment + constraint-tightening + allowed tool-set compatibility before routing',
                'order_offset': 3,
            },
        ]
    },
    'P5-STEP-062': {
        'parent_name': 'MINI_PIPE_router selects tool/adapter for task',
        'parent_phase': 'EXECUTION',
        'parent_component': 'mini_pipe_router',
        'parent_operation': 'task_execution',
        'parent_order': 620,
        'substeps': [
            {
                'suffix': 'A',
                'name': 'Evaluate routing rules',
                'description': 'Evaluate routing.rules in order; first match wins; select tool candidates via strategy',
                'order_offset': 1,
            },
            {
                'suffix': 'B',
                'name': 'Filter tool candidates by allowed tools',
                'description': 'Filter candidates by ER.routing.allowed_tools ∩ Phase.allowed_tools; if empty -> no_routable_tool_for_phase',
                'order_offset': 2,
            },
            {
                'suffix': 'C',
                'name': 'Bind and validate PromptInstance',
                'description': 'Bind ER.prompt_spec to template; build + validate PromptInstance (prompt_instance.v1.json)',
                'order_offset': 3,
            },
            {
                'suffix': 'D',
                'name': 'Enqueue work item to tool inbox',
                'description': 'Enqueue {tool_id, ExecutionRequest, PromptInstance} into tool inbox; apply max_attempts/timeout_seconds',
                'order_offset': 4,
            },
            {
                'suffix': 'E',
                'name': 'Handle tool failure with retry/fallback',
                'description': 'On tool failure: retry same tool, fallback_to next tool, or emit final_failure -> error pipeline',
                'order_offset': 5,
            },
        ]
    },
    'P5-STEP-078': {
        'parent_name': 'OPTIONAL: MINI_PIPE_patch_ledger manages patch lifecycle',
        'parent_phase': 'EXECUTION',
        'parent_component': 'acms_controller',
        'parent_operation': 'task_execution',
        'parent_order': 780,
        'substeps': [
            {
                'suffix': 'A',
                'name': 'Normalize tool output into PatchArtifact',
                'description': 'Normalize tool output into PatchArtifact; enforce format=unified_diff and diff parses cleanly',
                'order_offset': 1,
            },
            {
                'suffix': 'B',
                'name': 'Create PatchLedgerEntry',
                'description': 'Create PatchLedgerEntry with state=created and append-only state_history',
                'order_offset': 2,
            },
            {
                'suffix': 'C',
                'name': 'Validate patch against policies',
                'description': 'Validate patch: schema; scope vs ExecutionRequest; scope vs PhaseSpec; PatchPolicy limits; tests requirements; oscillation detection',
                'order_offset': 3,
            },
            {
                'suffix': 'D',
                'name': 'Apply patch to worktree',
                'description': 'If valid -> state=validated then queued; apply to worktree and record attempts/errors',
                'order_offset': 4,
            },
            {
                'suffix': 'E',
                'name': 'Verify patch with tests',
                'description': 'Verify: run tests; if pass -> verified then committed; else -> apply_failed',
                'order_offset': 5,
            },
            {
                'suffix': 'F',
                'name': 'Quarantine or rollback failed patch',
                'description': 'On max retries/policy violation: quarantine patch (persist ledger + quarantine path) and/or roll_back',
                'order_offset': 6,
            },
        ]
    },
    'MS-EXEC-004': {
        'parent_name': 'Apply Circuit Breakers',
        'parent_phase': 'EXECUTION',
        'parent_component': 'multi_agent_workstream_coordinator',
        'parent_operation': 'circuit_breaker_check',
        'parent_order': None,  # Will preserve from original
        'substeps': [
            {
                'suffix': 'A',
                'name': 'Load and validate circuit breaker config',
                'description': 'Load+validate circuit_breakers.yaml (defaults + per_step overrides); fail fast if invalid/missing',
                'order_offset': 1,
            },
            {
                'suffix': 'B',
                'name': 'Generate error signatures',
                'description': 'Generate stable error signatures (error_code + normalized message) and persist counters',
                'order_offset': 2,
            },
            {
                'suffix': 'C',
                'name': 'Track attempt counts and diff hashes',
                'description': 'Track attempt counts per (run_id, ws_id, step_name) and per signature; compute diff_hash each attempt',
                'order_offset': 3,
            },
            {
                'suffix': 'D',
                'name': 'Evaluate retry conditions',
                'description': 'Evaluate should_retry; if limits exceeded or oscillation detected -> breaker_tripped and halt loop',
                'order_offset': 4,
            },
            {
                'suffix': 'E',
                'name': 'Emit circuit breaker tripped event',
                'description': 'Emit circuit_breaker_tripped event; mark workstream failed; route to quarantine/escalation handlers',
                'order_offset': 5,
            },
        ]
    },
}


def expand_step_with_substeps(parent_step: Dict[str, Any], step_id: str) -> List[Dict[str, Any]]:
    """
    Expand a parent step into parent + substeps.

    Returns list: [parent_step, substep1, substep2, ...]
    """
    if step_id not in SUBSTEP_EXPANSIONS:
        return [parent_step]

    expansion = SUBSTEP_EXPANSIONS[step_id]
    expanded_steps = []

    # Update parent step description to indicate it has substeps
    parent_updated = parent_step.copy()
    parent_updated['description'] = f"{parent_step.get('description', parent_step['name'])} — Parent step with {len(expansion['substeps'])} substeps (see {step_id}A-{step_id}{expansion['substeps'][-1]['suffix']})"
    expanded_steps.append(parent_updated)

    # Create substeps
    base_order = parent_step.get('order', expansion['parent_order'])

    for substep_def in expansion['substeps']:
        substep = {
            'step_id': f"{step_id}{substep_def['suffix']}",
            'phase': parent_step.get('phase', expansion['parent_phase']),
            'name': substep_def['name'],
            'description': substep_def['description'],
            'responsible_component': parent_step.get('responsible_component', expansion['parent_component']),
            'operation_kind': parent_step.get('operation_kind', expansion['parent_operation']),
            'inputs': parent_step.get('inputs', ['Input data']),
            'expected_outputs': parent_step.get('expected_outputs', ['Output data']),
            'requires_human_confirmation': False,
            'order': base_order + (substep_def['order_offset'] / 10) if base_order else None,
            'lens': parent_step.get('lens'),
            'automation_level': parent_step.get('automation_level', 'fully_automatic'),
            'pattern_ids': parent_step.get('pattern_ids', []),
            'artifact_registry_refs': parent_step.get('artifact_registry_refs', []),
            'guardrail_checkpoint': parent_step.get('guardrail_checkpoint', False),
            'guardrail_checkpoint_id': parent_step.get('guardrail_checkpoint_id'),
            'implementation_files': parent_step.get('implementation_files', []),
            'artifacts_created': parent_step.get('artifacts_created', []),
            'artifacts_updated': parent_step.get('artifacts_updated', []),
            'metrics_emitted': parent_step.get('metrics_emitted', []),
            'preconditions': parent_step.get('preconditions', []),
            'postconditions': parent_step.get('postconditions', []),
            'error_handling': parent_step.get('error_handling'),
            'state_transition': parent_step.get('state_transition'),
            'anti_pattern_ids': parent_step.get('anti_pattern_ids', []),
            '_parent_step_id': step_id,  # Track parent relationship
        }
        expanded_steps.append(substep)

    return expanded_steps


def expand_schema_substeps(input_file: Path, output_file: Path) -> Dict[str, Any]:
    """
    Expand substeps in a schema file.

    Returns statistics about the expansion.
    """
    print(f"\nExpanding substeps in: {input_file.name}")

    with open(input_file, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    if 'steps' not in schema:
        print(f"  ⚠️  No 'steps' key found in {input_file.name}")
        return {'steps_processed': 0, 'substeps_added': 0, 'steps_expanded': []}

    original_count = len(schema['steps'])
    expanded_steps = []
    stats = {
        'steps_processed': 0,
        'substeps_added': 0,
        'steps_expanded': []
    }

    for step in schema['steps']:
        step_id = step.get('step_id')
        stats['steps_processed'] += 1

        if step_id in SUBSTEP_EXPANSIONS:
            # Expand this step
            expanded = expand_step_with_substeps(step, step_id)
            expanded_steps.extend(expanded)
            substep_count = len(expanded) - 1  # Subtract parent
            stats['substeps_added'] += substep_count
            stats['steps_expanded'].append(step_id)
            print(f"  ✓ Expanded {step_id} into {substep_count} substeps")
        else:
            # Keep as-is
            expanded_steps.append(step)

    # Update schema
    schema['steps'] = expanded_steps

    # Update metadata
    if 'meta' not in schema:
        schema['meta'] = {}

    schema['meta']['substep_expansion'] = {
        'expanded_at': datetime.utcnow().isoformat() + 'Z',
        'original_step_count': original_count,
        'expanded_step_count': len(expanded_steps),
        'substeps_added': stats['substeps_added'],
        'steps_expanded': stats['steps_expanded'],
    }

    # Save expanded schema
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"  ✓ Saved to: {output_file.name}")
    print(f"  ✓ Steps: {original_count} → {len(expanded_steps)} (+{len(expanded_steps) - original_count})")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Expand process steps with deterministic substeps'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        help='Input schema file to expand'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file for expanded schema'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Expand all source schemas (SSOT, PROCESS, MASTER_SPLINTER)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed statistics'
    )

    args = parser.parse_args()

    print("━" * 70)
    print("PFA SUBSTEP EXPANSION TOOL")
    print("━" * 70)

    if args.all:
        # Expand all source schemas
        schemas_to_expand = [
            ('PFA_SSOT_PROCESS_STEPS_SCHEMA.yaml', 'PFA_SSOT_PROCESS_STEPS_SCHEMA_EXPANDED.yaml'),
            ('PFA_PROCESS_STEPS_SCHEMA.yaml', 'PFA_PROCESS_STEPS_SCHEMA_EXPANDED.yaml'),
            ('PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA.yaml', 'PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA_EXPANDED.yaml'),
        ]

        total_stats = {
            'schemas_processed': 0,
            'total_substeps_added': 0,
            'all_steps_expanded': set()
        }

        for input_name, output_name in schemas_to_expand:
            input_path = Path(__file__).parent / input_name
            output_path = Path(__file__).parent / output_name

            if not input_path.exists():
                print(f"\n⚠️  Skipping {input_name} (not found)")
                continue

            stats = expand_schema_substeps(input_path, output_path)
            total_stats['schemas_processed'] += 1
            total_stats['total_substeps_added'] += stats['substeps_added']
            total_stats['all_steps_expanded'].update(stats['steps_expanded'])

        print("\n" + "━" * 70)
        print("EXPANSION SUMMARY")
        print("━" * 70)
        print(f"\nSchemas processed:     {total_stats['schemas_processed']}")
        print(f"Total substeps added:  {total_stats['total_substeps_added']}")
        print(f"Unique steps expanded: {len(total_stats['all_steps_expanded'])}")
        print(f"  {', '.join(sorted(total_stats['all_steps_expanded']))}")

    elif args.schema and args.output:
        # Expand single schema
        stats = expand_schema_substeps(args.schema, args.output)

        if args.stats:
            print("\n" + "━" * 70)
            print("EXPANSION STATISTICS")
            print("━" * 70)
            print(f"\nSubsteps added: {stats['substeps_added']}")
            print(f"Steps expanded: {', '.join(stats['steps_expanded'])}")

    else:
        parser.print_help()
        return 1

    print("\n" + "━" * 70)
    print("✓ EXPANSION COMPLETE")
    print("━" * 70)
    print("\nNext steps:")
    print("  1. Review expanded schemas")
    print("  2. Re-run merger: python pfa_merge_schemas.py --all")
    print("  3. Rebuild index: python pfa_build_master_index.py --schema PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml")
    print("  4. Regenerate docs: python pfa_generate_e2e_docs.py --all")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
