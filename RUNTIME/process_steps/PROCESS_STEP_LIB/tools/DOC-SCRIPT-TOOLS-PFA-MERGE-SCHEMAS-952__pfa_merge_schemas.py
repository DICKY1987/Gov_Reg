#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-MERGE-SCHEMAS-952
"""
pfa_merge_schemas.py

Merges multiple PFA process step schemas into a single unified E2E schema.
Handles phase mapping, duplicate detection, and conflict resolution.

Usage:
  python pfa_merge_schemas.py --all --output unified.yaml
  python pfa_merge_schemas.py --schemas schema1.yaml schema2.yaml --output merged.yaml
  python pfa_merge_schemas.py --all --dry-run --report conflicts.json

DOC_ID: DOC-SCRIPT-TOOLS-PFA-MERGE-SCHEMAS-952
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from DOC-SCRIPT-TOOLS-PFA-COMMON-944__pfa_common import (
    load_yaml, save_yaml, load_json, save_json,
    compute_content_hash, print_success, print_error, print_warning
)


@dataclass
class MergeMetadata:
    """Metadata about merge operation for a step."""
    is_duplicate: bool = False
    similar_steps: List[str] = field(default_factory=list)
    merge_sources: List[str] = field(default_factory=list)
    conflict_resolutions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UnifiedStep:
    """Unified step structure with mapping metadata."""
    step_id: str
    original_step_id: str
    source_schema: str
    universal_phase: str
    original_phase: str
    substage: str
    unified_operation_category: str
    original_operation_kind: str

    # Canonical fields
    name: str
    description: str
    responsible_component: str
    operation_kind: str
    inputs: List[str]
    expected_outputs: List[str]
    requires_human_confirmation: bool

    # Optional fields
    order: Optional[int] = None
    lens: Optional[str] = None
    automation_level: Optional[str] = None
    pattern_ids: List[str] = field(default_factory=list)
    artifact_registry_refs: List[str] = field(default_factory=list)
    guardrail_checkpoint: Optional[bool] = None
    guardrail_checkpoint_id: Optional[str] = None
    implementation_files: List[str] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    artifacts_updated: List[str] = field(default_factory=list)
    metrics_emitted: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    error_handling: Optional[str] = None
    state_transition: Optional[str] = None
    anti_pattern_ids: List[str] = field(default_factory=list)

    # Merge metadata
    merge_metadata: MergeMetadata = field(default_factory=MergeMetadata)
    _content_hash: Optional[str] = None


class PhaseMapper:
    """Maps original phases to universal phase taxonomy."""

    def __init__(self, mappings_file: Path):
        self.config = load_yaml(mappings_file)
        self.mappings = self.config['mappings']
        self.universal_phases = self.config['universal_phases']
        self.semantic_conflicts = self.config.get('semantic_conflicts', {})

    def map_phase(self, schema_name: str, original_phase: str, step_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Map original phase to universal phase and substage.
        Returns: (universal_phase, substage)
        """
        schema_key = self._normalize_schema_name(schema_name)

        if schema_key not in self.mappings:
            raise ValueError(f"Unknown schema: {schema_name}")

        if original_phase not in self.mappings[schema_key]:
            raise ValueError(f"Unknown phase '{original_phase}' for schema '{schema_name}'")

        mapping = self.mappings[schema_key][original_phase]
        universal_phase = mapping['universal_phase']
        substage = mapping['substage']

        # Handle semantic conflicts
        if original_phase in self.semantic_conflicts:
            substage = self._resolve_semantic_conflict(
                original_phase, schema_name, step_data
            )

        return universal_phase, substage

    def _normalize_schema_name(self, schema_name: str) -> str:
        """Normalize schema name to match config keys."""
        # Extract key from schema names like "PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA"
        if "MASTER_SPLINTER" in schema_name:
            return "MASTER_SPLINTER"
        elif "PATTERNS" in schema_name:
            return "PATTERNS"
        elif "GLOSSARY" in schema_name:
            return "GLOSSARY"
        elif "SSOT" in schema_name:
            return "SSOT"
        elif "DIRECTORY_INTEGRATION" in schema_name:
            return "DIRECTORY_INTEGRATION"
        elif "PROCESS" in schema_name or "CANONICAL" in schema_name:
            return "PROCESS"
        return schema_name

    def _resolve_semantic_conflict(self, phase: str, schema: str, step_data: Dict[str, Any]) -> str:
        """Resolve semantic conflicts based on context."""
        conflicts = self.semantic_conflicts.get(phase, {})
        schema_key = self._normalize_schema_name(schema).lower()

        if schema_key in conflicts:
            return conflicts[schema_key]['substage']

        # Default to first available substage
        return list(conflicts.values())[0]['substage'] if conflicts else "default"


class OperationTaxonomy:
    """Categorizes operation kinds into unified taxonomy."""

    def __init__(self, taxonomy_file: Path):
        self.config = load_yaml(taxonomy_file)
        self.categories = self.config['universal_categories']
        self.mappings = self.config['mappings']
        self.patterns = self.config.get('operation_patterns', [])
        self.ambiguous = self.config.get('ambiguous_operations', {})

    def categorize(self, operation_kind: str, context: Dict[str, Any] = None) -> str:
        """
        Categorize an operation_kind into unified category.
        Returns: unified category name
        """
        operation_kind = operation_kind.strip().lower()

        # Direct mapping lookup
        for category, variants in self.mappings.items():
            if operation_kind in [v.lower() for v in variants]:
                return category

        # Pattern-based matching
        for pattern_rule in self.patterns:
            if re.match(pattern_rule['pattern'], operation_kind, re.IGNORECASE):
                return pattern_rule['category']

        # Handle ambiguous operations with context
        if operation_kind in self.ambiguous:
            return self._resolve_ambiguous(operation_kind, context or {})

        # Default to original if no match
        return operation_kind

    def _resolve_ambiguous(self, operation: str, context: Dict[str, Any]) -> str:
        """Resolve ambiguous operations using context rules."""
        rules = self.ambiguous[operation]
        default = rules.get('default_category', operation)

        for rule in rules.get('context_rules', []):
            condition = rule['condition']
            # Simple eval (production would use safer parser)
            try:
                if self._evaluate_condition(condition, context):
                    return rule['category']
            except Exception:
                continue

        return default

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate condition string."""
        # Simple contains/in checks for safety
        if 'in [' in condition:
            var, values_str = condition.split(' in ')
            var = var.strip()
            values = eval(values_str)  # Safe for list literals
            return context.get(var) in values
        elif 'contains' in condition:
            var, needle = condition.split(' contains ')
            var = var.strip()
            needle = needle.strip().strip("'\"")
            return needle in str(context.get(var, ''))
        return False


class DuplicateDetector:
    """Detects duplicate and similar steps across schemas."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.hash_index: Dict[str, List[UnifiedStep]] = defaultdict(list)
        self.step_id_index: Dict[str, UnifiedStep] = {}

    def add_step(self, step: UnifiedStep):
        """Add step to indices."""
        if step._content_hash:
            self.hash_index[step._content_hash].append(step)
        self.step_id_index[step.original_step_id] = step

    def find_duplicates(self, step: UnifiedStep) -> List[UnifiedStep]:
        """Find exact duplicates by content hash."""
        if not step._content_hash:
            return []

        candidates = self.hash_index.get(step._content_hash, [])
        return [s for s in candidates if s.step_id != step.step_id]

    def find_similar(self, step: UnifiedStep) -> List[Tuple[UnifiedStep, float]]:
        """Find semantically similar steps."""
        similar = []
        step_text = f"{step.name} {step.description}".lower()

        for other in self.step_id_index.values():
            if other.step_id == step.step_id:
                continue

            other_text = f"{other.name} {other.description}".lower()
            similarity = self._text_similarity(step_text, other_text)

            if similarity >= self.similarity_threshold:
                similar.append((other, similarity))

        return sorted(similar, key=lambda x: x[1], reverse=True)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity for text comparison."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class ConflictResolver:
    """Resolves field-level conflicts during merge."""

    @staticmethod
    def resolve_description(descriptions: List[str]) -> str:
        """Prefer most detailed description."""
        return max(descriptions, key=len)

    @staticmethod
    def resolve_component(component: str, schema_prefix: str) -> str:
        """Add schema namespace prefix to component."""
        if '::' not in component:
            return f"{schema_prefix}::{component}"
        return component

    @staticmethod
    def merge_lists(lists: List[List[str]]) -> List[str]:
        """Merge lists preserving order and uniqueness."""
        seen = set()
        result = []
        for lst in lists:
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result


class SchemaMerger:
    """Main merger orchestrator."""

    def __init__(
        self,
        phase_mapper: PhaseMapper,
        operation_taxonomy: OperationTaxonomy,
        duplicate_detector: DuplicateDetector,
        conflict_resolver: ConflictResolver
    ):
        self.phase_mapper = phase_mapper
        self.operation_taxonomy = operation_taxonomy
        self.duplicate_detector = duplicate_detector
        self.conflict_resolver = conflict_resolver
        self.phase_counters: Dict[str, int] = defaultdict(int)

    def merge_schemas(self, schema_files: List[Path]) -> Tuple[List[UnifiedStep], Dict[str, Any]]:
        """
        Merge multiple schemas into unified step list.
        Returns: (unified_steps, merge_report)
        """
        all_steps: List[UnifiedStep] = []
        merge_stats = {
            'total_steps_loaded': 0,
            'unique_steps_after_dedup': 0,
            'duplicates_removed': 0,
            'conflicts_resolved': 0,
            'source_schemas': [],
            'steps_by_schema': {}
        }

        # Load and convert all schemas
        for schema_file in schema_files:
            schema_name = schema_file.stem
            steps = self._load_schema(schema_file)

            merge_stats['source_schemas'].append(schema_name)
            merge_stats['steps_by_schema'][schema_name] = len(steps)
            merge_stats['total_steps_loaded'] += len(steps)

            for step_dict in steps:
                unified_step = self._convert_to_unified(step_dict, schema_name)
                all_steps.append(unified_step)
                self.duplicate_detector.add_step(unified_step)

        # Deduplicate
        unique_steps = self._deduplicate_steps(all_steps, merge_stats)

        # Sort by universal phase and substage
        unique_steps.sort(key=lambda s: (s.universal_phase, s.substage, s.order or 0))

        merge_stats['unique_steps_after_dedup'] = len(unique_steps)
        merge_stats['duplicates_removed'] = merge_stats['total_steps_loaded'] - len(unique_steps)

        return unique_steps, merge_stats

    def _load_schema(self, schema_file: Path) -> List[Dict[str, Any]]:
        """Load steps from schema file."""
        doc = load_yaml(schema_file)

        # Handle different schema structures
        if 'steps' in doc and isinstance(doc['steps'], list):
            return doc['steps']
        elif 'phases' in doc:
            steps = []
            for phase_data in doc['phases'].values():
                if isinstance(phase_data, dict) and 'steps' in phase_data:
                    steps.extend(phase_data['steps'])
            return steps

        return []

    def _convert_to_unified(self, step_dict: Dict[str, Any], schema_name: str) -> UnifiedStep:
        """Convert original step to unified format."""
        original_phase = step_dict.get('phase', 'UNKNOWN')
        original_step_id = step_dict.get('step_id', 'UNKNOWN')
        operation_kind = step_dict.get('operation_kind', 'unknown')

        # Map phase
        universal_phase, substage = self.phase_mapper.map_phase(
            schema_name, original_phase, step_dict
        )

        # Categorize operation
        context = {
            'phase': universal_phase,
            'responsible_component': step_dict.get('responsible_component', ''),
            'expected_outputs': step_dict.get('expected_outputs', [])
        }
        unified_category = self.operation_taxonomy.categorize(operation_kind, context)

        # Generate new unified step ID
        self.phase_counters[universal_phase] += 1
        phase_prefix = universal_phase.split('_')[0]  # "1" from "1_BOOTSTRAP"
        seq = self.phase_counters[universal_phase]
        new_step_id = f"E2E-{phase_prefix}-{seq:03d}"

        # Prefix component with schema namespace
        component = step_dict.get('responsible_component', '')
        schema_prefix = self.phase_mapper._normalize_schema_name(schema_name).lower()
        prefixed_component = self.conflict_resolver.resolve_component(component, schema_prefix)

        # Compute content hash
        content_hash = self._compute_hash(step_dict)

        # Build unified step
        unified_step = UnifiedStep(
            step_id=new_step_id,
            original_step_id=original_step_id,
            source_schema=schema_name,
            universal_phase=universal_phase,
            original_phase=original_phase,
            substage=substage,
            unified_operation_category=unified_category,
            original_operation_kind=operation_kind,
            name=step_dict.get('name', ''),
            description=step_dict.get('description', ''),
            responsible_component=prefixed_component,
            operation_kind=operation_kind,
            inputs=step_dict.get('inputs', []),
            expected_outputs=step_dict.get('expected_outputs', []),
            requires_human_confirmation=step_dict.get('requires_human_confirmation', False),
            order=step_dict.get('order'),
            lens=step_dict.get('lens'),
            automation_level=step_dict.get('automation_level'),
            pattern_ids=step_dict.get('pattern_ids', []),
            artifact_registry_refs=step_dict.get('artifact_registry_refs', []),
            guardrail_checkpoint=step_dict.get('guardrail_checkpoint'),
            guardrail_checkpoint_id=step_dict.get('guardrail_checkpoint_id'),
            implementation_files=step_dict.get('implementation_files', []),
            artifacts_created=step_dict.get('artifacts_created', []),
            artifacts_updated=step_dict.get('artifacts_updated', []),
            metrics_emitted=step_dict.get('metrics_emitted', []),
            preconditions=step_dict.get('preconditions', []),
            postconditions=step_dict.get('postconditions', []),
            error_handling=step_dict.get('error_handling'),
            state_transition=step_dict.get('state_transition'),
            anti_pattern_ids=step_dict.get('anti_pattern_ids', []),
            _content_hash=content_hash
        )

        return unified_step

    def _compute_hash(self, step_dict: Dict[str, Any]) -> str:
        """Compute stable content hash for duplicate detection."""
        # Use core semantic fields only
        payload = {
            'name': step_dict.get('name', ''),
            'description': step_dict.get('description', ''),
            'operation_kind': step_dict.get('operation_kind', ''),
            'inputs': sorted(step_dict.get('inputs', [])),
            'expected_outputs': sorted(step_dict.get('expected_outputs', []))
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()

    def _deduplicate_steps(self, steps: List[UnifiedStep], stats: Dict[str, Any]) -> List[UnifiedStep]:
        """Remove duplicates and merge similar steps."""
        seen_hashes: Set[str] = set()
        unique_steps: List[UnifiedStep] = []

        for step in steps:
            if step._content_hash in seen_hashes:
                # Exact duplicate - skip but record
                step.merge_metadata.is_duplicate = True
                stats['duplicates_removed'] = stats.get('duplicates_removed', 0) + 1
                continue

            # Find similar steps
            similar = self.duplicate_detector.find_similar(step)
            if similar:
                step.merge_metadata.similar_steps = [
                    f"{s.step_id} ({score:.2f})" for s, score in similar[:3]
                ]

            seen_hashes.add(step._content_hash)
            unique_steps.append(step)

        return unique_steps


def main():
    parser = argparse.ArgumentParser(description='Merge PFA process step schemas')
    parser.add_argument('--all', action='store_true', help='Merge all 6 schemas')
    parser.add_argument('--schemas', nargs='+', help='Specific schema files to merge')
    parser.add_argument('--output', required=True, help='Output unified schema file')
    parser.add_argument('--report', help='Output merge report JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without writing output')
    parser.add_argument('--expanded', action='store_true', help='Use expanded schemas with substeps')
    parser.add_argument('--phase-mappings', default='phase_mappings.yaml',
                        help='Phase mappings config file')
    parser.add_argument('--operation-taxonomy', default='operation_taxonomy.yaml',
                        help='Operation taxonomy config file')

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent  # PROCESS_STEP_LIB directory

    # Select schemas to merge
    if args.all:
        # Use expanded schemas if requested (for substep support)
        if args.expanded:
            schema_files = [
                base_dir / 'schemas' / 'expanded' / 'PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA_EXPANDED.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_PATTERNS_PROCESS_STEPS_SCHEMA.yaml',  # No expanded version yet
                base_dir / 'schemas' / 'source' / 'PFA_GLOSSARY_PROCESS_STEPS_SCHEMA.yaml',  # No expanded version yet
                base_dir / 'schemas' / 'expanded' / 'PFA_SSOT_PROCESS_STEPS_SCHEMA_EXPANDED.yaml',
                base_dir / 'schemas' / 'expanded' / 'PFA_PROCESS_STEPS_SCHEMA_EXPANDED.yaml'
            ]
        else:
            schema_files = [
                base_dir / 'schemas' / 'source' / 'PFA_MASTER_SPLINTER_PROCESS_STEPS_SCHEMA.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_PATTERNS_PROCESS_STEPS_SCHEMA.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_GLOSSARY_PROCESS_STEPS_SCHEMA.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_SSOT_PROCESS_STEPS_SCHEMA.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_PROCESS_STEPS_SCHEMA.yaml',
                base_dir / 'schemas' / 'source' / 'PFA_DIRECTORY_INTEGRATION_PROCESS_STEPS_SCHEMA.yaml'
            ]

        # Verify expanded schemas exist if requested
        if args.expanded:
            missing = [f for f in schema_files if not f.exists()]
            if missing:
                print("\n❌ ERROR: Expanded schemas not found:")
                for f in missing:
                    print(f"  • {f.name}")
                print("\nRun: python pfa_expand_substeps.py --all")
                return 1
    elif args.schemas:
        schema_files = [Path(s) for s in args.schemas]
    else:
        parser.error('Must specify --all or --schemas')

    # Verify files exist
    for f in schema_files:
        if not f.exists():
            print(f"Error: Schema file not found: {f}")
            return 1

    # Load configs - resolve relative to base directory
    phase_mappings_file = base_dir / 'config' / args.phase_mappings
    operation_taxonomy_file = base_dir / 'config' / args.operation_taxonomy

    if not phase_mappings_file.exists():
        print_error(f"Phase mappings file not found: {phase_mappings_file}")
        return 1
    if not operation_taxonomy_file.exists():
        print_error(f"Operation taxonomy file not found: {operation_taxonomy_file}")
        return 1

    # Initialize components
    phase_mapper = PhaseMapper(phase_mappings_file)
    operation_taxonomy = OperationTaxonomy(operation_taxonomy_file)
    duplicate_detector = DuplicateDetector()
    conflict_resolver = ConflictResolver()

    merger = SchemaMerger(
        phase_mapper,
        operation_taxonomy,
        duplicate_detector,
        conflict_resolver
    )

    # Perform merge
    print(f"Merging {len(schema_files)} schemas...")
    unified_steps, merge_stats = merger.merge_schemas(schema_files)

    print(f"✓ Merged {merge_stats['total_steps_loaded']} steps")
    print(f"✓ Unique steps after deduplication: {merge_stats['unique_steps_after_dedup']}")
    print(f"✓ Duplicates removed: {merge_stats['duplicates_removed']}")

    if args.dry_run:
        print("\n[DRY RUN] Would write output files:")
        print(f"  - {args.output}")
        if args.report:
            print(f"  - {args.report}")
        return 0

    # Build output document
    output_doc = {
        'meta': {
            'schema_id': 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA',
            'version': '1.0.0',
            'source_schemas': merge_stats['source_schemas'],
            'merge_statistics': merge_stats,
            'generated_at': None  # Would add timestamp
        },
        'universal_phases': list(phase_mapper.universal_phases.keys()),
        'unified_operation_kinds': list(operation_taxonomy.categories.keys()),
        'steps': [asdict(step) for step in unified_steps]
    }

    # Write unified schema
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_yaml(output_doc, output_path)
    print_success(f"Wrote unified schema: {output_path}")

    # Write merge report
    if args.report:
        report_path = Path(args.report)
        save_json(merge_stats, report_path)
        print_success(f"Wrote merge report: {report_path}")

    return 0


if __name__ == '__main__':
    exit(main())
