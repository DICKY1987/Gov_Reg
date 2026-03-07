#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-BUILD-MASTER-INDEX-943
"""
pfa_build_master_index.py

Builds multi-dimensional master index from unified E2E schema.
Creates 7 index types plus 5 predefined workflows for navigation.

Usage:
  python pfa_build_master_index.py --schema unified.yaml --output master_index.json
  python pfa_build_master_index.py --schema unified.yaml --output master_index.json --workflows workflow_defs.yaml

DOC_ID: DOC-SCRIPT-TOOLS-PFA-BUILD-MASTER-INDEX-943
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import sys

import yaml

# Add parent directory to path for pfa_common import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import (
    load_yaml, save_yaml, load_json, save_json,
    print_success, print_error, print_info
)


@dataclass
class WorkflowDefinition:
    """Definition of a predefined E2E workflow."""
    workflow_id: str
    name: str
    description: str
    phases: List[str]
    entry_steps: List[str]
    exit_steps: List[str]
    step_filter: Optional[Dict[str, Any]] = None


@dataclass
class DependencyInfo:
    """Dependency information for a step."""
    step_id: str
    depends_on: List[str] = field(default_factory=list)
    enables: List[str] = field(default_factory=list)
    artifacts_consumed: List[str] = field(default_factory=list)
    artifacts_produced: List[str] = field(default_factory=list)


@dataclass
class CrossReference:
    """Cross-reference information for a step."""
    step_id: str
    appears_in_workflows: List[str] = field(default_factory=list)
    related_by_phase: List[str] = field(default_factory=list)
    related_by_component: List[str] = field(default_factory=list)
    related_by_operation: List[str] = field(default_factory=list)
    similar_steps: List[Dict[str, Any]] = field(default_factory=list)


class MasterIndexBuilder:
    """Builds comprehensive multi-dimensional index."""

    def __init__(self, unified_schema: Dict[str, Any]):
        self.schema = unified_schema
        self.steps = unified_schema['steps']
        self.meta = unified_schema.get('meta', {})

        # Initialize indices
        self.by_phase: Dict[str, List[str]] = defaultdict(list)
        self.by_component: Dict[str, List[str]] = defaultdict(list)
        self.by_operation: Dict[str, List[str]] = defaultdict(list)
        self.by_workflow: Dict[str, List[str]] = defaultdict(list)
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.cross_references: Dict[str, CrossReference] = {}
        self.step_lookup: Dict[str, Dict[str, Any]] = {}

    def build(self) -> Dict[str, Any]:
        """Build all indices and return master index."""
        print(f"Building master index for {len(self.steps)} steps...")

        # Build core indices
        self._build_step_lookup()
        self._build_phase_index()
        self._build_component_index()
        self._build_operation_index()
        self._build_dependency_graph()
        self._build_cross_references()

        # Validate dependency graph
        if not self._is_acyclic():
            print("Warning: Dependency graph contains cycles!")
        else:
            print("✓ Dependency graph is acyclic")

        # Build master index structure
        master_index = {
            'meta': {
                'schema_id': self.meta.get('schema_id'),
                'version': self.meta.get('version'),
                'source_schemas': self.meta.get('source_schemas', []),
                'total_steps': len(self.steps),
                'index_types': 7,
                'generated_at': None  # Would add timestamp
            },
            'indices': {
                'by_phase': {k: sorted(v) for k, v in self.by_phase.items()},
                'by_component': {k: sorted(v) for k, v in self.by_component.items()},
                'by_operation': {k: sorted(v) for k, v in self.by_operation.items()},
                'by_workflow': {k: sorted(v) for k, v in self.by_workflow.items()},
                'dependencies': {k: asdict(v) for k, v in self.dependencies.items()},
                'cross_references': {k: asdict(v) for k, v in self.cross_references.items()},
                'step_lookup': self.step_lookup
            },
            'statistics': self._compute_statistics()
        }

        return master_index

    def _build_step_lookup(self):
        """Build quick lookup index by step_id."""
        for step in self.steps:
            step_id = step['step_id']
            self.step_lookup[step_id] = step

    def _build_phase_index(self):
        """Index steps by universal phase."""
        for step in self.steps:
            phase = step['universal_phase']
            self.by_phase[phase].append(step['step_id'])

            # Also index by substage
            substage_key = f"{phase}.{step['substage']}"
            self.by_phase[substage_key].append(step['step_id'])

    def _build_component_index(self):
        """Index steps by responsible component."""
        for step in self.steps:
            component = step['responsible_component']
            self.by_component[component].append(step['step_id'])

            # Also index by base component (before ::)
            if '::' in component:
                base = component.split('::')[0]
                self.by_component[base].append(step['step_id'])

    def _build_operation_index(self):
        """Index steps by operation category."""
        for step in self.steps:
            # Index by unified category
            category = step['unified_operation_category']
            self.by_operation[category].append(step['step_id'])

            # Also index by original operation_kind
            original = step['original_operation_kind']
            self.by_operation[original].append(step['step_id'])

    def _build_dependency_graph(self):
        """Build dependency graph from artifacts and phase ordering."""
        # Initialize dependency info for each step
        for step in self.steps:
            step_id = step['step_id']
            self.dependencies[step_id] = DependencyInfo(
                step_id=step_id,
                artifacts_consumed=step.get('inputs', []),
                artifacts_produced=step.get('expected_outputs', [])
            )

        # Build artifact-based dependencies
        artifact_producers: Dict[str, str] = {}

        for step in self.steps:
            step_id = step['step_id']

            # Register as producer of its outputs
            for artifact in step.get('expected_outputs', []):
                if artifact and isinstance(artifact, str):
                    artifact_producers[artifact] = step_id

        # Link consumers to producers
        for step in self.steps:
            step_id = step['step_id']
            dep_info = self.dependencies[step_id]

            for artifact in step.get('inputs', []):
                if artifact and isinstance(artifact, str) and artifact in artifact_producers:
                    producer_id = artifact_producers[artifact]
                    if producer_id != step_id:
                        dep_info.depends_on.append(producer_id)
                        self.dependencies[producer_id].enables.append(step_id)

        # Add phase-based ordering (steps in later phases depend on earlier phases)
        phase_order = self.schema.get('universal_phases', [])
        for i, phase in enumerate(phase_order):
            current_steps = self.by_phase.get(phase, [])

            # Each step implicitly depends on completion of prior phases
            if i > 0:
                prior_phase = phase_order[i - 1]
                prior_steps = self.by_phase.get(prior_phase, [])

                for step_id in current_steps:
                    dep_info = self.dependencies[step_id]
                    # Add last step of prior phase as dependency (simplified)
                    if prior_steps and prior_steps[-1] not in dep_info.depends_on:
                        dep_info.depends_on.append(prior_steps[-1])

    def _build_cross_references(self):
        """Build cross-reference index."""
        for step in self.steps:
            step_id = step['step_id']
            xref = CrossReference(step_id=step_id)

            # Related by same phase
            phase = step['universal_phase']
            xref.related_by_phase = [
                s for s in self.by_phase[phase] if s != step_id
            ][:10]  # Limit to 10

            # Related by same component
            component = step['responsible_component']
            xref.related_by_component = [
                s for s in self.by_component[component] if s != step_id
            ][:10]

            # Related by same operation
            operation = step['unified_operation_category']
            xref.related_by_operation = [
                s for s in self.by_operation[operation] if s != step_id
            ][:10]

            # Similar steps from merge metadata
            merge_meta = step.get('merge_metadata', {})
            if merge_meta and merge_meta.get('similar_steps'):
                xref.similar_steps = [
                    {'step_id': s.split(' ')[0], 'similarity': s.split('(')[1].strip(')')}
                    for s in merge_meta['similar_steps']
                ]

            self.cross_references[step_id] = xref

    def _is_acyclic(self) -> bool:
        """Check if dependency graph is acyclic using DFS."""
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            dep_info = self.dependencies.get(step_id)
            if dep_info:
                for dep_id in dep_info.depends_on:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        for step_id in self.dependencies:
            if step_id not in visited:
                if has_cycle(step_id):
                    return False

        return True

    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute index statistics."""
        return {
            'total_steps': len(self.steps),
            'total_phases': len([k for k in self.by_phase.keys() if not '.' in k]),
            'total_components': len(self.by_component),
            'total_operations': len(self.by_operation),
            'total_workflows': len(self.by_workflow),
            'avg_dependencies_per_step': sum(
                len(d.depends_on) for d in self.dependencies.values()
            ) / len(self.dependencies) if self.dependencies else 0,
            'steps_by_phase': {
                k: len(v) for k, v in self.by_phase.items() if not '.' in k
            },
            'steps_by_component': {
                k: len(v) for k, v in sorted(
                    self.by_component.items(), key=lambda x: len(x[1]), reverse=True
                )[:10]
            },
            'steps_by_operation': {
                k: len(v) for k, v in sorted(
                    self.by_operation.items(), key=lambda x: len(x[1]), reverse=True
                )[:10]
            }
        }

    def add_workflow(self, workflow: WorkflowDefinition):
        """Add a predefined workflow to the index."""
        print(f"Adding workflow: {workflow.name}")

        # Filter steps based on workflow definition
        workflow_steps = []

        if workflow.step_filter:
            # Apply filters
            for step in self.steps:
                if self._matches_filter(step, workflow.step_filter):
                    workflow_steps.append(step['step_id'])
        elif workflow.phases:
            # Include all steps from specified phases
            for phase in workflow.phases:
                phase_steps = self.by_phase.get(phase, [])
                workflow_steps.extend(phase_steps)
        else:
            # No filters - include all steps (for full_e2e)
            workflow_steps = [step['step_id'] for step in self.steps]

        self.by_workflow[workflow.workflow_id] = workflow_steps

        # Update cross-references
        for step_id in workflow_steps:
            if step_id in self.cross_references:
                self.cross_references[step_id].appears_in_workflows.append(workflow.workflow_id)

    def _matches_filter(self, step: Dict[str, Any], filter_spec: Dict[str, Any]) -> bool:
        """Check if step matches workflow filter."""
        for key, value in filter_spec.items():
            if key not in step:
                return False

            step_value = step[key]

            if isinstance(value, list):
                if step_value not in value:
                    return False
            elif isinstance(value, str):
                if isinstance(step_value, str):
                    if value not in step_value:
                        return False
                elif step_value != value:
                    return False
            elif step_value != value:
                return False

        return True


def load_predefined_workflows() -> List[WorkflowDefinition]:
    """Load 5 predefined workflows."""
    return [
        WorkflowDefinition(
            workflow_id='full_e2e',
            name='Full End-to-End Pipeline',
            description='Complete pipeline covering all 9 phases',
            phases=[],  # Empty list means include all steps
            entry_steps=[],
            exit_steps=[]
        ),
        WorkflowDefinition(
            workflow_id='master_splinter_orchestration',
            name='Master Splinter Multi-Agent Orchestration',
            description='Multi-agent orchestration workflow',
            phases=[],
            entry_steps=[],
            exit_steps=[],
            step_filter={'source_schema': 'PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA'}
        ),
        WorkflowDefinition(
            workflow_id='pattern_automation',
            name='Zero-Touch Pattern Automation',
            description='Automated pattern discovery, generation, and execution',
            phases=[],
            entry_steps=[],
            exit_steps=[],
            step_filter={'source_schema': 'PFA_PATTERNS_PROCESS_STEPS_SCHEMA'}
        ),
        WorkflowDefinition(
            workflow_id='glossary_lifecycle',
            name='Glossary Term Lifecycle Management',
            description='Term proposal through archival lifecycle',
            phases=[],
            entry_steps=[],
            exit_steps=[],
            step_filter={'source_schema': 'PFA_GLOSSARY_PROCESS_STEPS_SCHEMA'}
        ),
        WorkflowDefinition(
            workflow_id='acms_gap_to_execution',
            name='ACMS Gap Analysis to Execution',
            description='Gap discovery through execution and summary',
            phases=['2_DISCOVERY', '3_DESIGN', '6_EXECUTION', '7_CONSOLIDATION'],
            entry_steps=[],
            exit_steps=[],
            step_filter={'source_schema': 'PFA_SSOT_PROCESS_STEPS_SCHEMA'}
        )
    ]


class MasterIndexQuery:
    """Query interface for master index."""

    def __init__(self, index: Dict[str, Any]):
        self.index = index
        self.indices = index['indices']

    def get_steps_by_phase(self, phase: str) -> List[str]:
        """Get all step IDs for a phase."""
        return self.indices['by_phase'].get(phase, [])

    def get_steps_by_component(self, component: str) -> List[str]:
        """Get all step IDs for a component."""
        return self.indices['by_component'].get(component, [])

    def get_steps_by_operation(self, operation: str) -> List[str]:
        """Get all step IDs for an operation category."""
        return self.indices['by_operation'].get(operation, [])

    def get_workflow(self, workflow_id: str) -> List[str]:
        """Get all step IDs for a workflow."""
        return self.indices['by_workflow'].get(workflow_id, [])

    def get_dependencies(self, step_id: str) -> Dict[str, Any]:
        """Get dependency info for a step."""
        return self.indices['dependencies'].get(step_id, {})

    def get_cross_references(self, step_id: str) -> Dict[str, Any]:
        """Get cross-reference info for a step."""
        return self.indices['cross_references'].get(step_id, {})

    def get_step(self, step_id: str) -> Dict[str, Any]:
        """Get full step data."""
        return self.indices['step_lookup'].get(step_id, {})

    def search_steps(self, query: str) -> List[str]:
        """Search steps by name or description."""
        results = []
        query_lower = query.lower()

        for step_id, step_data in self.indices['step_lookup'].items():
            if query_lower in step_data.get('name', '').lower():
                results.append(step_id)
            elif query_lower in step_data.get('description', '').lower():
                results.append(step_id)

        return results


def main():
    parser = argparse.ArgumentParser(description='Build master index from unified schema')
    parser.add_argument('--schema', required=True, help='Unified schema YAML file')
    parser.add_argument('--output', required=True, help='Output master index JSON file')
    parser.add_argument('--workflows', help='Custom workflow definitions YAML (optional)')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')

    args = parser.parse_args()

    # Load unified schema
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print_error(f"Schema file not found: {schema_path}")
        return 1

    unified_schema = load_yaml(schema_path)

    # Build master index
    builder = MasterIndexBuilder(unified_schema)

    # Add predefined workflows
    workflows = load_predefined_workflows()
    for workflow in workflows:
        builder.add_workflow(workflow)

    # Add custom workflows if provided
    if args.workflows:
        workflows_path = Path(args.workflows)
        if workflows_path.exists():
            custom_workflows = load_yaml(workflows_path)

            for wf_data in custom_workflows.get('workflows', []):
                workflow = WorkflowDefinition(**wf_data)
                builder.add_workflow(workflow)

    # Build index
    master_index = builder.build()

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_json(master_index, output_path, indent=2 if args.pretty else None)

    print_success(f"Wrote master index: {output_path}")
    print_info("\nIndex Statistics:")
    stats = master_index['statistics']
    print(f"  Total steps: {stats['total_steps']}")
    print(f"  Total phases: {stats['total_phases']}")
    print(f"  Total components: {stats['total_components']}")
    print(f"  Total operations: {stats['total_operations']}")
    print(f"  Total workflows: {stats['total_workflows']}")
    print(f"  Avg dependencies/step: {stats['avg_dependencies_per_step']:.2f}")

    return 0


if __name__ == '__main__':
    exit(main())
