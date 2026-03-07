#!/usr/bin/env python3
"""
validate_phase5_packet.py

Validator tool for Phase 5 Execution Packets.

Usage:
    python validate_phase5_packet.py \\
        --packet <path_to_packet.json> \\
        --schema <path_to_schema.json> \\
        --prompt-template <path_to_template.json> \\
        --strict true

Exit codes:
    0: Validation passed
    1: Invalid arguments
    2: Invalid schema (structural)
    3: Invalid semantics
    10: Tool error
"""
DOC_ID: DOC-CORE-02-TOOLS-VALIDATE-PHASE5-PACKET-211

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def compute_sha256(data: str) -> str:
    """Compute SHA-256 hash of string data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def canonical_json(obj: Any) -> str:
    """Convert object to canonical JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding='utf-8'))


class ValidationReport:
    """Track validation results."""

    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []

    def add_pass(self, rule_id: str):
        self.passed.append(rule_id)

    def add_fail(self, rule_id: str, message: str):
        self.failed.append((rule_id, message))

    def add_warning(self, rule_id: str, message: str):
        self.warnings.append((rule_id, message))

    def has_failures(self) -> bool:
        return len(self.failed) > 0

    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"✓ Passed: {len(self.passed)}")
        print(f"✗ Failed: {len(self.failed)}")
        print(f"⚠ Warnings: {len(self.warnings)}")

        if self.failed:
            print(f"\n{'='*60}")
            print("FAILURES:")
            print(f"{'='*60}")
            for rule_id, message in self.failed:
                print(f"✗ [{rule_id}] {message}")

        if self.warnings:
            print(f"\n{'='*60}")
            print("WARNINGS:")
            print(f"{'='*60}")
            for rule_id, message in self.warnings:
                print(f"⚠ [{rule_id}] {message}")

        print(f"{'='*60}\n")

    def to_json(self) -> Dict[str, Any]:
        return {
            'passed_count': len(self.passed),
            'failed_count': len(self.failed),
            'warnings_count': len(self.warnings),
            'passed_rules': self.passed,
            'failed_rules': [{'rule_id': r, 'message': m} for r, m in self.failed],
            'warnings': [{'rule_id': r, 'message': m} for r, m in self.warnings],
            'exit_code': 3 if self.has_failures() else 0
        }


def validate_structural(packet: Dict[str, Any], schema: Dict[str, Any], report: ValidationReport):
    """Run structural validations (JSON Schema)."""
    if not JSONSCHEMA_AVAILABLE:
        report.add_warning('VAL-STRUCT-001', 'jsonschema not installed, skipping structural validation')
        return

    try:
        jsonschema.validate(packet, schema)
        report.add_pass('VAL-STRUCT-001')
    except jsonschema.ValidationError as e:
        report.add_fail('VAL-STRUCT-001', f'Schema validation failed: {e.message} at {".".join(str(p) for p in e.path)}')
    except Exception as e:
        report.add_fail('VAL-STRUCT-001', f'Schema validation error: {str(e)}')


def validate_required_sections(packet: Dict[str, Any], report: ValidationReport):
    """Verify all required top-level sections are present."""
    required = ['meta', 'identity', 'scope', 'dag', 'execution', 'prompt', 'validation', 'acceptance', 'observability', 'signatures']

    for section in required:
        if section not in packet:
            report.add_fail('VAL-STRUCT-002', f'Missing required section: {section}')
        else:
            report.add_pass(f'VAL-STRUCT-002-{section}')

    # Check for extra top-level keys
    extra = set(packet.keys()) - set(required)
    if extra:
        report.add_warning('VAL-STRUCT-002', f'Unexpected top-level keys: {extra}')


def validate_prompt_template_ref(packet: Dict[str, Any], prompt_template: Dict[str, Any], report: ValidationReport):
    """Verify prompt template reference matches actual template."""
    prompt_ref = packet.get('prompt', {}).get('prompt_template_ref', {})
    template_meta = prompt_template.get('meta', {})

    expected_id = template_meta.get('prompt_id', '')
    expected_version = template_meta.get('version', '')

    actual_id = prompt_ref.get('id', '')
    actual_version = prompt_ref.get('version', '')

    if actual_id != expected_id:
        report.add_fail('VAL-SEM-001', f'Template ID mismatch: expected "{expected_id}", got "{actual_id}"')
    else:
        report.add_pass('VAL-SEM-001-id')

    if actual_version != expected_version:
        report.add_fail('VAL-SEM-001', f'Template version mismatch: expected "{expected_version}", got "{actual_version}"')
    else:
        report.add_pass('VAL-SEM-001-version')

    # Verify hash
    template_canonical = canonical_json(prompt_template)
    expected_hash = compute_sha256(template_canonical)
    actual_hash = prompt_ref.get('sha256', '')

    if actual_hash != expected_hash:
        report.add_fail('VAL-SEM-001', f'Template hash mismatch: expected "{expected_hash[:16]}...", got "{actual_hash[:16]}..."')
    else:
        report.add_pass('VAL-SEM-001-hash')


def validate_no_unresolved_placeholders(packet: Dict[str, Any], report: ValidationReport):
    """Verify rendered prompt has no unresolved ${...} placeholders."""
    rendered = packet.get('prompt', {}).get('rendered_prompt', '')

    # Check for ${...} pattern
    if '${' in rendered:
        matches = re.findall(r'\$\{[^}]+\}', rendered)
        report.add_fail('VAL-SEM-002', f'Unresolved placeholders found: {matches[:5]}')
    else:
        report.add_pass('VAL-SEM-002')


def validate_scope_coherence(packet: Dict[str, Any], report: ValidationReport):
    """Verify scope lists are coherent (no overlaps with forbidden)."""
    scope = packet.get('scope', {})

    read_only = set(scope.get('read_only_paths', []))
    modify = set(scope.get('allowed_modify_paths', []))
    create = set(scope.get('allowed_create_paths', []))
    forbidden = set(scope.get('forbidden_paths', []))

    # Check for overlaps
    modify_forbidden = modify & forbidden
    create_forbidden = create & forbidden
    read_forbidden = read_only & forbidden

    if modify_forbidden:
        report.add_fail('VAL-SEM-003', f'Modify paths overlap with forbidden: {modify_forbidden}')
    else:
        report.add_pass('VAL-SEM-003-modify')

    if create_forbidden:
        report.add_fail('VAL-SEM-003', f'Create paths overlap with forbidden: {create_forbidden}')
    else:
        report.add_pass('VAL-SEM-003-create')

    if read_forbidden:
        report.add_fail('VAL-SEM-003', f'Read-only paths overlap with forbidden: {read_forbidden}')
    else:
        report.add_pass('VAL-SEM-003-read')

    # Check scope lists are non-empty
    if not (read_only or modify or create):
        report.add_warning('VAL-SEM-003', 'All scope lists are empty')


def validate_pattern_enforcement(packet: Dict[str, Any], report: ValidationReport):
    """Verify each step has pattern_ids or explicit waiver."""
    steps = packet.get('execution', {}).get('steps', [])

    for step in steps:
        step_id = step.get('step_id', 'unknown')
        pattern_ids = step.get('pattern_ids', [])
        waiver = step.get('pattern_waiver')

        if not pattern_ids:
            if not waiver or not waiver.get('reason'):
                report.add_fail('VAL-SEM-004', f'Step {step_id} has no pattern_ids and no valid waiver')
            else:
                if len(waiver.get('reason', '')) < 20:
                    report.add_fail('VAL-SEM-004', f'Step {step_id} waiver reason too short (min 20 chars)')
                else:
                    report.add_pass(f'VAL-SEM-004-{step_id}')
        else:
            report.add_pass(f'VAL-SEM-004-{step_id}')


def validate_dag(packet: Dict[str, Any], report: ValidationReport):
    """Verify DAG is acyclic and all references are valid."""
    dag = packet.get('dag', {})
    nodes = dag.get('nodes', [])
    edges = dag.get('edges', [])

    # Check node IDs are unique
    node_ids = [n.get('node_id', '') for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        report.add_fail('VAL-DAG-001', 'Duplicate node IDs found')
        return

    node_id_set = set(node_ids)

    # Check edges reference valid nodes
    for edge in edges:
        from_node = edge.get('from', '')
        to_node = edge.get('to', '')

        if from_node not in node_id_set:
            report.add_fail('VAL-DAG-001', f'Edge references invalid from node: {from_node}')

        if to_node not in node_id_set:
            report.add_fail('VAL-DAG-001', f'Edge references invalid to node: {to_node}')

    # Check for cycles (simple DFS)
    def has_cycle():
        # Build adjacency list
        adj = {node_id: [] for node_id in node_ids}
        for edge in edges:
            adj[edge.get('from', '')].append(edge.get('to', ''))

        visited = set()
        rec_stack = set()

        def visit(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if visit(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node_id in node_ids:
            if node_id not in visited:
                if visit(node_id):
                    return True
        return False

    if has_cycle():
        report.add_fail('VAL-DAG-001', 'DAG contains cycle')
    else:
        report.add_pass('VAL-DAG-001')


def validate_required_artifacts(packet: Dict[str, Any], report: ValidationReport):
    """Verify required artifacts paths are unique and resolve."""
    artifacts = packet.get('acceptance', {}).get('required_artifacts', [])

    paths = [a.get('path', '') for a in artifacts]
    if len(paths) != len(set(paths)):
        report.add_fail('VAL-ACC-001', 'Duplicate artifact paths found')
    else:
        report.add_pass('VAL-ACC-001')

    # Check paths are non-empty
    for artifact in artifacts:
        if not artifact.get('path'):
            report.add_fail('VAL-ACC-001', f'Artifact {artifact.get("artifact_id", "unknown")} has empty path')


def main():
    parser = argparse.ArgumentParser(
        description='Validate Phase 5 Execution Packet'
    )
    parser.add_argument('--packet', required=True, help='Path to packet JSON')
    parser.add_argument('--schema', required=True, help='Path to schema JSON')
    parser.add_argument('--prompt-template', required=True, help='Path to prompt template JSON')
    parser.add_argument('--strict', default='true', choices=['true', 'false'],
                        help='Strict mode (default: true)')
    parser.add_argument('--report-json', help='Path to write JSON report')

    args = parser.parse_args()

    try:
        # Load files
        packet = load_json(Path(args.packet))
        schema = load_json(Path(args.schema))
        prompt_template = load_json(Path(args.prompt_template))

        # Run validations
        report = ValidationReport()

        print("Running validations...", file=sys.stderr)

        # Structural validations
        validate_structural(packet, schema, report)
        validate_required_sections(packet, report)

        # Semantic validations
        validate_prompt_template_ref(packet, prompt_template, report)
        validate_no_unresolved_placeholders(packet, report)
        validate_scope_coherence(packet, report)
        validate_pattern_enforcement(packet, report)

        # DAG validations
        validate_dag(packet, report)

        # Acceptance validations
        validate_required_artifacts(packet, report)

        # Print summary
        report.print_summary()

        # Write JSON report if requested
        if args.report_json:
            report_path = Path(args.report_json)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(report.to_json(), indent=2),
                encoding='utf-8'
            )
            print(f"✓ Validation report written: {report_path}", file=sys.stderr)

        # Exit with appropriate code
        if report.has_failures():
            if args.strict == 'true':
                return 3
            else:
                print("⚠ Validation failed but continuing (non-strict mode)", file=sys.stderr)
                return 0
        else:
            print("✓ All validations passed", file=sys.stderr)
            return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 10


if __name__ == '__main__':
    sys.exit(main())
