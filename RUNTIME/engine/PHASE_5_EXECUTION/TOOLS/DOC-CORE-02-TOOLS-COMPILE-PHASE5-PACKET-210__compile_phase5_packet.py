#!/usr/bin/env python3
"""
compile_phase5_packet.py

Compiler tool that transforms Phase Plan + Prompt Template into Phase 5 Execution Packet.

Usage:
    python compile_phase5_packet.py \\
        --phase-plan <path_to_phase_plan.(json|yml)> \\
        --prompt-template <path_to_prompt_template.json> \\
        --out <output_packet_path> \\
        --schema <path_to_schema.json> \\
        --emit-rendered-prompt true \\
        --strict true

Exit codes:
    0: Success
    1: Invalid arguments
    2: File not found
    3: Compilation error
    4: Validation error
"""
DOC_ID: DOC-CORE-02-TOOLS-COMPILE-PHASE5-PACKET-210

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def generate_ulid() -> str:
    """Generate a ULID-like identifier (simplified)."""
    import time
    import random
    
    # ULID alphabet excludes I, L, O, U
    alphabet = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    
    timestamp = int(time.time() * 1000)
    timestamp_part = format(timestamp, '010X')
    
    # Convert timestamp to base32 using ULID alphabet (10 chars)
    ts_chars = []
    ts = timestamp
    for _ in range(10):
        ts_chars.append(alphabet[ts % 32])
        ts //= 32
    timestamp_part = ''.join(reversed(ts_chars))
    
    # Generate 16 random characters from alphabet
    random_part = ''.join(random.choice(alphabet) for _ in range(16))
    
    return timestamp_part + random_part


def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of string data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def canonical_json(obj: Any) -> str:
    """Convert object to canonical JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def load_file(path: Path) -> Dict[str, Any]:
    """Load JSON or YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    content = path.read_text(encoding='utf-8')
    
    if path.suffix in ['.yaml', '.yml']:
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML not installed. Install with: pip install pyyaml")
        return yaml.safe_load(content)
    elif path.suffix == '.json':
        return json.loads(content)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def format_steps(steps: List[Dict]) -> str:
    """Format execution steps according to specification."""
    lines = []
    for step in steps:
        step_id = step.get('id', 'unknown')
        op_kind = step.get('operation_kind', 'UNKNOWN')
        name = step.get('name', 'Unnamed step')
        patterns = ','.join(step.get('pattern_ids', []))
        tool = step.get('tool_id', 'unknown')
        human_confirm = str(step.get('requires_human_confirmation', False)).lower()
        
        line = f"[{step_id}] {op_kind} :: {name} | patterns={patterns} tool={tool} human_confirm={human_confirm}"
        lines.append(line)
    
    return '\n'.join(lines)


def format_pre_flight_checks(checks: List[Dict]) -> str:
    """Format pre-flight checks according to specification."""
    lines = []
    for check in checks:
        check_id = check.get('id', 'unknown')
        description = check.get('description', '')
        command = check.get('command', {})
        tool_id = command.get('tool_id', 'unknown')
        args = ' '.join(command.get('args', []))
        success = check.get('success_pattern', '')
        on_fail = check.get('on_fail', 'abort')
        
        line = f"[{check_id}] {description} | cmd={tool_id}:{args} | success={success} | on_fail={on_fail}"
        lines.append(line)
    
    return '\n'.join(lines)


def format_acceptance_tests(tests: List[Dict], bindings: Dict[str, str]) -> str:
    """Format acceptance tests according to specification."""
    lines = []
    for test in tests:
        test_id = test.get('id', 'unknown')
        must_pass = str(test.get('must_pass', True)).lower()
        description = test.get('description', '')
        command = test.get('command', {})
        tool_id = command.get('tool_id', 'unknown')
        
        # Join args and substitute placeholders
        args_list = command.get('args', [])
        args = ' '.join(str(arg) for arg in args_list)
        # Substitute placeholders
        for key, value in bindings.items():
            args = args.replace(f'${{{key}}}', value)
        
        success = test.get('success_pattern', '')
        
        line = f"[{test_id}] must_pass={must_pass} | {description} | cmd={tool_id}:{args} | success={success}"
        lines.append(line)
    
    return '\n'.join(lines)


def build_dag_from_steps(steps: List[Dict]) -> Dict[str, Any]:
    """Build DAG structure from execution steps (linear if no explicit deps)."""
    nodes = []
    edges = []
    
    for i, step in enumerate(steps):
        step_id = step.get('id', f'step-{i:02d}')
        node = {
            'node_id': f'node-{i+1:02d}',
            'step_id': step_id,
            'operation_kind': step.get('operation_kind', 'UNKNOWN'),
            'inputs': [],
            'outputs': []
        }
        
        # Extract outputs from expected_outputs
        for output in step.get('expected_outputs', []):
            if isinstance(output, dict):
                output_desc = output.get('description', '')
            else:
                output_desc = str(output)
            nodes.append(node)
        
        # Create linear dependency
        if i > 0:
            edges.append({
                'from': f'node-{i:02d}',
                'to': f'node-{i+1:02d}',
                'dependency_type': 'hard'
            })
    
    return {
        'nodes': nodes,
        'edges': edges,
        'invariants': {
            'must_be_acyclic': True,
            'max_parallelism': 1,
            'dependency_mode': 'strict'
        },
        'io_contracts': []
    }


def compile_packet(
    phase_plan: Dict[str, Any],
    prompt_template: Dict[str, Any],
    emit_rendered_prompt: bool = True
) -> Dict[str, Any]:
    """Compile Phase 5 Execution Packet from phase plan and prompt template."""
    
    # Compute template hash
    template_canonical = canonical_json(prompt_template)
    template_hash = compute_sha256(template_canonical)
    
    # Extract phase identity
    phase_identity = phase_plan.get('phase_identity', {})
    phase_id = phase_identity.get('phase_id', 'PH-UNKNOWN')
    workstream_id = phase_identity.get('workstream_id', 'ws-unknown')
    objective = phase_identity.get('objective', 'No objective specified')
    
    # Extract scope
    scope_and_modules = phase_plan.get('scope_and_modules', {})
    file_scope = scope_and_modules.get('file_scope', {})
    
    read_only = file_scope.get('read_only', [])
    modify = file_scope.get('modify', [])
    create = file_scope.get('create', [])
    forbidden = file_scope.get('forbidden_paths', [])
    
    # Extract execution plan
    execution_plan = phase_plan.get('execution_plan', {})
    steps = execution_plan.get('steps', [])
    
    # Extract pre-flight checks
    pre_flight = phase_plan.get('pre_flight_checks', {})
    checks = pre_flight.get('checks', [])
    
    # Extract acceptance tests
    acceptance = phase_plan.get('acceptance_tests', {})
    tests = acceptance.get('tests', [])
    
    # Extract expected artifacts
    expected_artifacts = phase_plan.get('expected_artifacts', {})
    
    # Extract completion gate
    completion_gate = phase_plan.get('completion_gate', {})
    
    # Build placeholder bindings first
    basic_bindings = {
        'phase_id': phase_id,
        'workstream_id': workstream_id,
        'objective': objective,
    }
    
    # Substitute placeholders in expected_artifacts
    artifacts_str = json.dumps(expected_artifacts, separators=(',', ':'))
    for key, value in basic_bindings.items():
        artifacts_str = artifacts_str.replace(f'${{{key}}}', value)
    
    # Substitute in observability event tags
    observability_config = phase_plan.get('observability_and_metrics', {})
    event_tags = []
    for tag in observability_config.get('event_tags', []):
        # Substitute phase_identity references
        tag = tag.replace('${phase_identity.phase_id}', phase_id)
        tag = tag.replace('${phase_identity.workstream_id}', workstream_id)
        tag = tag.replace('${phase_identity.phase_type}', phase_identity.get('phase_type', 'implementation'))
        event_tags.append(tag)
    
    placeholder_bindings = {
        'phase_id': phase_id,
        'workstream_id': workstream_id,
        'objective': objective,
        'file_scope_modify': ', '.join(modify),
        'file_scope_create': ', '.join(create),
        'file_scope_read_only': ', '.join(read_only),
        'forbidden_paths': ', '.join(forbidden),
        'execution_steps_formatted': format_steps(steps),
        'pre_flight_checks': format_pre_flight_checks(checks),
        'acceptance_tests': format_acceptance_tests(tests, basic_bindings),
        'expected_artifacts': artifacts_str,
        'completion_gate_rules': json.dumps(completion_gate, separators=(',', ':'))
    }
    
    # Render prompt template
    rendered_prompt = ""
    if emit_rendered_prompt:
        # Build prompt sections (simplified)
        rendered_prompt = f"""You are an AI operator executing Phase {phase_id} of Workstream {workstream_id}.

MISSION: {objective}

CRITICAL CONSTRAINTS:

File Scope Enforcement:
- You MAY ONLY modify files matching: {placeholder_bindings['file_scope_modify']}
- You MAY create files in: {placeholder_bindings['file_scope_create']}
- You MAY read files in: {placeholder_bindings['file_scope_read_only']}
- You MUST NEVER touch: {placeholder_bindings['forbidden_paths']}

Ground Truth Over Vibes:
- Trust git status, test output, and filesystem over conversational summaries
- Verify success with actual commands, not assumptions

NO STOP MODE:
- If a step fails, log the error and continue
- Execute ALL steps, collect ALL errors
- Report comprehensive results at the end

EXECUTION STEPS:
{placeholder_bindings['execution_steps_formatted']}

PRE-FLIGHT CHECKS (verify before starting):
{placeholder_bindings['pre_flight_checks']}

ACCEPTANCE TESTS (run after execution):
{placeholder_bindings['acceptance_tests']}

EXPECTED ARTIFACTS:
{placeholder_bindings['expected_artifacts']}

ERROR HANDLING:
- Log error details to stderr
- Add to error collection list
- Continue with next step
- Report all errors in final summary

SUCCESS CRITERIA:
{placeholder_bindings['completion_gate_rules']}

OUTPUT FORMAT (provide structured JSON):
{{
  "phase_id": "{phase_id}",
  "status": "completed|failed|blocked",
  "errors": [],
  "warnings": [],
  "files_modified": [],
  "tests_passed": true|false,
  "artifacts_created": []
}}"""
    
    # Build DAG
    dag = build_dag_from_steps(steps)
    
    # Build execution steps for packet
    packet_steps = []
    for step in steps:
        packet_step = {
            'step_id': step.get('id', 'unknown'),
            'name': step.get('name', ''),
            'operation_kind': step.get('operation_kind', 'UNKNOWN'),
            'pattern_ids': step.get('pattern_ids', []),
            'tool_id': step.get('tool_id', 'unknown'),
            'description': step.get('description', ''),
            'inputs': step.get('inputs', {}),
            'expected_outputs': [
                {'description': out} if isinstance(out, str) else out
                for out in step.get('expected_outputs', [])
            ],
            'requires_human_confirmation': step.get('requires_human_confirmation', False)
        }
        
        # Add commands if present
        if 'commands' in step.get('inputs', {}):
            packet_step['commands'] = step['inputs']['commands']
        
        packet_steps.append(packet_step)
    
    # Build execution profile
    execution_profile = phase_plan.get('execution_profile', {})
    retry_policy = execution_profile.get('retry_policy', {})
    runtime_profile = {
        'run_mode': execution_profile.get('run_mode', 'execute'),
        'concurrency': execution_profile.get('concurrency', {}).get('max_parallel_steps', 1),
        'max_runtime_minutes': execution_profile.get('max_runtime_minutes', 60),
        'retry_policy': {
            'max_attempts': retry_policy.get('default_max_attempts', 1),
            'backoff_strategy': 'none'
        },
        'timeout_behavior': 'abort',
        'dry_run': False
    }
    
    # Build validation section
    validation = {
        'structural_validations': [
            {
                'id': 'VAL-STRUCT-001',
                'description': 'Packet JSON Schema validation',
                'check_type': 'jsonschema'
            }
        ],
        'semantic_validations': [
            {
                'id': 'VAL-SEM-002',
                'description': 'All required placeholders bound; no unresolved placeholders in rendered_prompt',
                'rule': "rendered_prompt MUST NOT contain '${'substring"
            }
        ],
        'toolchain_validations': [
            {
                'id': check.get('id', f'pf-{i}'),
                'description': check.get('description', ''),
                'command': check.get('command', {}),
                'success_pattern': check.get('success_pattern', ''),
                'on_fail': check.get('on_fail', 'abort')
            }
            for i, check in enumerate(checks)
        ],
        'policy_validations': [
            {
                'id': 'POL-001',
                'description': 'File scope enforcement check',
                'policy_type': 'scope_enforcement'
            }
        ],
        'required_passes': [
            'VAL-STRUCT-001',
            'VAL-SEM-002'
        ]
    }
    
    # Build acceptance section
    acceptance_section = {
        'tests': [
            {
                'id': test.get('id', f'acc-{i}'),
                'description': test.get('description', ''),
                'command': {
                    'tool_id': test.get('command', {}).get('tool_id', 'unknown'),
                    'args': [
                        arg.replace(f'${{phase_id}}', phase_id).replace(f'${{workstream_id}}', workstream_id)
                        if isinstance(arg, str) else arg
                        for arg in test.get('command', {}).get('args', [])
                    ]
                },
                'success_pattern': test.get('success_pattern', ''),
                'must_pass': test.get('must_pass', True)
            }
            for i, test in enumerate(tests)
        ],
        'completion_gate': completion_gate,
        'required_artifacts': []
    }
    
    # Build required artifacts - substitute placeholders in paths
    artifact_kind_map = {
        'patches': 'patch',
        'logs': 'log',
        'docs': 'doc',
        'db': 'db_migration'
    }
    
    for artifact_type in ['patches', 'logs', 'docs']:
        for artifact in expected_artifacts.get(artifact_type, []):
            if isinstance(artifact, dict):
                path = artifact.get('path', '')
                # Substitute placeholders
                for key, value in basic_bindings.items():
                    path = path.replace(f'${{{key}}}', value)
                
                acceptance_section['required_artifacts'].append({
                    'artifact_id': path.replace('/', '-').replace('\\', '-').replace('.', '-'),
                    'path': path,
                    'kind': artifact_kind_map.get(artifact_type, 'patch'),
                    'must_exist': artifact.get('must_exist', True)
                })
    
    # Build observability section
    observability = {
        'log_paths': {
            'execution_log': f'.runs/{workstream_id}/{phase_id}/execution.log',
            'error_log': f'.runs/{workstream_id}/{phase_id}/errors.log',
            'metrics_log': f'.runs/{workstream_id}/{phase_id}/metrics.jsonl'
        },
        'jsonl_event_stream_path': f'.runs/{workstream_id}/{phase_id}/events.jsonl',
        'metrics_required': ['duration', 'files_touched', 'test_results', 'error_count'],
        'event_tags': event_tags
    }
    
    # Build complete packet
    packet = {
        'meta': {
            'contract_kind': 'phase5_execution_packet',
            'schema_version': '1.0.0',
            'packet_id': generate_ulid(),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'created_by': 'compile_phase5_packet/1.0.0',
            'source_provenance': {
                'phase_plan_doc_id': phase_plan.get('doc_id', 'UNKNOWN'),
                'phase_plan_template_version': phase_plan.get('template_version', 3),
                'prompt_template_id': prompt_template.get('meta', {}).get('prompt_id', 'UNKNOWN'),
                'prompt_template_version': prompt_template.get('meta', {}).get('version', '0.0.0'),
                'prompt_template_hash': template_hash,
                'compiler_version': 'compile_phase5_packet/1.0.0'
            },
            'engine_min_version': '5.0.0'
        },
        'identity': {
            'phase_id': phase_id,
            'workstream_id': workstream_id,
            'objective': objective,
            'repo_root': scope_and_modules.get('repo_root', '.'),
            'workspace_path': str(Path.cwd())
        },
        'scope': {
            'read_only_paths': read_only,
            'allowed_modify_paths': modify,
            'allowed_create_paths': create,
            'forbidden_paths': forbidden,
            'glob_policy': {
                'engine': 'python-pathlib',
                'case_sensitive': False
            }
        },
        'dag': dag,
        'execution': {
            'steps': packet_steps,
            'runtime_profile': runtime_profile
        },
        'prompt': {
            'prompt_template_ref': {
                'id': prompt_template.get('meta', {}).get('prompt_id', 'UNKNOWN'),
                'version': prompt_template.get('meta', {}).get('version', '0.0.0'),
                'sha256': template_hash
            },
            'placeholder_bindings': placeholder_bindings,
            'rendered_prompt': rendered_prompt,
            'output_contract': prompt_template.get('output_format', {}).get('schema', {})
        },
        'validation': validation,
        'acceptance': acceptance_section,
        'observability': observability,
        'signatures': {
            'packet_hash': '0000000000000000000000000000000000000000000000000000000000000000',
            'sign_off': []
        }
    }
    
    # Compute packet hash (exclude signatures.packet_hash itself)
    packet_for_hash = packet.copy()
    packet_for_hash['signatures'] = {'packet_hash': '', 'sign_off': []}
    packet_hash = compute_sha256(canonical_json(packet_for_hash))
    packet['signatures']['packet_hash'] = packet_hash
    
    return packet


def main():
    parser = argparse.ArgumentParser(
        description='Compile Phase 5 Execution Packet from Phase Plan and Prompt Template'
    )
    parser.add_argument('--phase-plan', required=True, help='Path to phase plan (JSON or YAML)')
    parser.add_argument('--prompt-template', required=True, help='Path to prompt template (JSON)')
    parser.add_argument('--out', required=True, help='Output packet path')
    parser.add_argument('--schema', help='Path to packet schema for validation')
    parser.add_argument('--emit-rendered-prompt', default='true', choices=['true', 'false'],
                        help='Whether to emit rendered prompt (default: true)')
    parser.add_argument('--strict', default='true', choices=['true', 'false'],
                        help='Strict validation mode (default: true)')
    
    args = parser.parse_args()
    
    try:
        # Load inputs
        phase_plan = load_file(Path(args.phase_plan))
        prompt_template = load_file(Path(args.prompt_template))
        
        # Compile packet
        emit_prompt = args.emit_rendered_prompt == 'true'
        packet = compile_packet(phase_plan, prompt_template, emit_prompt)
        
        # Validate against schema if provided
        if args.schema:
            if not JSONSCHEMA_AVAILABLE:
                print("WARNING: jsonschema not installed, skipping validation", file=sys.stderr)
            else:
                schema = load_file(Path(args.schema))
                try:
                    jsonschema.validate(packet, schema)
                    print(f"✓ Packet validates against schema", file=sys.stderr)
                except jsonschema.ValidationError as e:
                    print(f"✗ Validation error: {e.message}", file=sys.stderr)
                    if args.strict == 'true':
                        return 4
        
        # Write output
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(packet, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        print(f"✓ Compiled packet: {out_path}", file=sys.stderr)
        print(f"  Packet ID: {packet['meta']['packet_id']}", file=sys.stderr)
        print(f"  Phase: {packet['identity']['phase_id']}", file=sys.stderr)
        print(f"  Workstream: {packet['identity']['workstream_id']}", file=sys.stderr)
        print(f"  Hash: {packet['signatures']['packet_hash'][:16]}...", file=sys.stderr)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"ERROR: Failed to parse input file: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: Compilation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3


if __name__ == '__main__':
    sys.exit(main())
