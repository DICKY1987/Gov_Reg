#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-ATTACH-IMPLEMENTATION-FILES-941
"""
Attach implementation files to unified E2E process steps.

Uses workspace classification data + component mappings to link each step
to its implementing files with confidence scores.

Usage:
    python pfa_attach_implementation_files.py \
        --unified-schema PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml \
        --classification workspace/classification_report_enhanced.json \
        --output PFA_E2E_WITH_FILES.yaml
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-ATTACH-IMPLEMENTATION-FILES-941

import argparse
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


# Component to folder mappings (from ENHANCED_CLASSIFICATION_KNOWLEDGE_BASE.md)
COMPONENT_TO_FOLDER = {
    # Phase components
    'bootstrap_engine': ['PHASE_0_BOOTSTRAP'],
    'preflight_checker': ['PHASE_0_BOOTSTRAP'],
    'config_loader': ['PHASE_0_BOOTSTRAP'],

    'gap_analyzer': ['PHASE_1_PLANNING'],
    'workstream_planner': ['PHASE_1_PLANNING'],
    'requirement_gatherer': ['PHASE_1_PLANNING'],

    'execution_request_builder': ['PHASE_2_REQUEST_BUILDING'],
    'dto_compiler': ['PHASE_2_REQUEST_BUILDING'],
    'contract_validator': ['PHASE_2_REQUEST_BUILDING', 'SUB_IO_CONTRACT_PIPELINE'],

    'dag_builder': ['PHASE_3_SCHEDULING'],
    'dependency_resolver': ['PHASE_3_SCHEDULING'],
    'ccpm_scheduler': ['PHASE_3_SCHEDULING'],
    'topological_sorter': ['PHASE_3_SCHEDULING'],

    'tool_router': ['PHASE_4_ROUTING'],
    'adapter_selector': ['PHASE_4_ROUTING', 'SUB_AIM'],
    'capability_matcher': ['PHASE_4_ROUTING'],

    'mini_pipe_orchestrator': ['PHASE_5_EXECUTION'],
    'mini_pipe_executor': ['PHASE_5_EXECUTION'],
    'mini_pipe_router': ['PHASE_5_EXECUTION', 'PHASE_4_ROUTING'],
    'mini_pipe_patch_ledger': ['PHASE_5_EXECUTION', 'PHASE_6_ERROR_RECOVERY'],
    'task_runner': ['PHASE_5_EXECUTION'],
    'state_machine': ['PHASE_5_EXECUTION'],

    'error_engine': ['PHASE_6_ERROR_RECOVERY'],
    'retry_handler': ['PHASE_6_ERROR_RECOVERY'],
    'circuit_breaker': ['PHASE_6_ERROR_RECOVERY'],
    'recovery_plugin': ['PHASE_6_ERROR_RECOVERY'],
    'multi_agent_workstream_coordinator': ['PHASE_6_ERROR_RECOVERY', 'PHASE_5_EXECUTION'],

    'telemetry_collector': ['PHASE_7_MONITORING'],
    'metrics_aggregator': ['PHASE_7_MONITORING'],
    'log_analyzer': ['PHASE_7_MONITORING', 'SUB_LOG_REVIEW'],
    'dashboard_generator': ['PHASE_7_MONITORING', 'SUB_GUI'],

    # Subsystem components
    'aim_adapter': ['SUB_AIM'],
    'aim_router': ['SUB_AIM'],
    'prompt_builder': ['SUB_AIM'],
    'model_selector': ['SUB_AIM'],

    'ccis_processor': ['SUB_CLP'],
    'uci_analyzer': ['SUB_CLP'],
    'psjp_builder': ['SUB_CLP'],
    'clp_validator': ['SUB_CLP'],

    'decision_eliminator': ['SUB_DECISION_ELIMINATION'],
    'game_board_analyzer': ['SUB_DECISION_ELIMINATION'],

    'doc_id_registry': ['SUB_DOC_ID'],
    'doc_lifecycle_manager': ['SUB_DOC_ID'],
    'doc_validator': ['SUB_DOC_ID'],

    'git_automation': ['SUB_GITHUB'],
    'worktree_manager': ['SUB_GITHUB'],
    'merge_automator': ['SUB_GITHUB'],

    'glossary_manager': ['SUB_GLOSSARY'],
    'term_validator': ['SUB_GLOSSARY'],
    'term_lifecycle': ['SUB_GLOSSARY'],

    'tui_panel': ['SUB_GUI'],
    'dashboard_ui': ['SUB_GUI'],
    'interactive_cli': ['SUB_GUI'],

    'contract_validator': ['SUB_IO_CONTRACT_PIPELINE'],
    'dto_builder': ['SUB_IO_CONTRACT_PIPELINE'],
    'schema_manager': ['SUB_IO_CONTRACT_PIPELINE'],

    'pattern_executor': ['SUB_PATTERNS'],
    'pattern_registry': ['SUB_PATTERNS'],
    'pattern_generator': ['SUB_PATTERNS'],

    'template_engine': ['SUB_TEMPLATES'],
    'scaffolder': ['SUB_TEMPLATES'],

    # Utilities
    'validation_tool': ['UTI_TOOLS'],
    'analyzer': ['UTI_TOOLS'],
    'converter': ['UTI_TOOLS'],
}


# Keywords to folder mappings
KEYWORD_TO_FOLDER = {
    # Phase keywords
    'bootstrap': ['PHASE_0_BOOTSTRAP'],
    'preflight': ['PHASE_0_BOOTSTRAP'],
    'initialization': ['PHASE_0_BOOTSTRAP'],

    'planning': ['PHASE_1_PLANNING'],
    'gap_analysis': ['PHASE_1_PLANNING'],
    'workstream': ['PHASE_1_PLANNING'],

    'execution_request': ['PHASE_2_REQUEST_BUILDING'],
    'dto': ['PHASE_2_REQUEST_BUILDING', 'SUB_IO_CONTRACT_PIPELINE'],
    'contract': ['PHASE_2_REQUEST_BUILDING', 'SUB_IO_CONTRACT_PIPELINE'],

    'scheduling': ['PHASE_3_SCHEDULING'],
    'dependency': ['PHASE_3_SCHEDULING'],
    'dag': ['PHASE_3_SCHEDULING'],
    'ccpm': ['PHASE_3_SCHEDULING'],

    'routing': ['PHASE_4_ROUTING'],
    'adapter': ['PHASE_4_ROUTING', 'SUB_AIM'],
    'tool_selection': ['PHASE_4_ROUTING'],

    'execution': ['PHASE_5_EXECUTION'],
    'orchestrator': ['PHASE_5_EXECUTION'],
    'executor': ['PHASE_5_EXECUTION'],
    'task_runner': ['PHASE_5_EXECUTION'],

    'error_recovery': ['PHASE_6_ERROR_RECOVERY'],
    'retry': ['PHASE_6_ERROR_RECOVERY'],
    'circuit_breaker': ['PHASE_6_ERROR_RECOVERY'],

    'monitoring': ['PHASE_7_MONITORING'],
    'telemetry': ['PHASE_7_MONITORING'],
    'metrics': ['PHASE_7_MONITORING'],

    # Subsystem keywords
    'ccis': ['SUB_CLP'],
    'uci': ['SUB_CLP'],
    'psjp': ['SUB_CLP'],
    'deterministic_debug': ['SUB_CLP'],

    'doc_id': ['SUB_DOC_ID'],
    'registry': ['SUB_DOC_ID', 'SUB_PATTERNS'],

    'pattern': ['SUB_PATTERNS'],
    'automation': ['SUB_PATTERNS'],

    'glossary': ['SUB_GLOSSARY'],
    'term': ['SUB_GLOSSARY'],

    'gui': ['SUB_GUI'],
    'tui': ['SUB_GUI'],
    'dashboard': ['SUB_GUI'],

    'git': ['SUB_GITHUB'],
    'worktree': ['SUB_GITHUB'],
}


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_yaml(data: dict, path: Path):
    """Save data as YAML."""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


def normalize_path(path: str) -> str:
    """Normalize path separators."""
    return path.replace('\\', '/')


def extract_component_from_step(step: dict) -> str:
    """Extract component name from step."""
    # Try responsible_component field
    if 'responsible_component' in step:
        comp = step['responsible_component']
        if '::' in comp:
            # Format: "namespace::component"
            return comp.split('::')[-1]
        return comp

    # Try component field
    if 'component' in step:
        return step['component']

    return None


def match_files_to_folders(
    classified_files: List[dict],
    target_folders: List[str],
    confidence_threshold: int = 20
) -> List[Tuple[str, int, str]]:
    """
    Match classified files to target folders.

    Returns list of (file_path, confidence, reason) tuples.
    """
    matches = []

    for entry in classified_files:
        file_path = normalize_path(entry['file'])
        destination = entry.get('destination', '')
        confidence = entry.get('confidence', 0)
        reason = entry.get('reason', '')

        if confidence < confidence_threshold:
            continue

        # Check if destination matches any target folder
        for folder in target_folders:
            if destination == folder or destination.startswith(folder + '/'):
                matches.append((file_path, confidence, reason))
                break

    return matches


def match_files_by_keywords(
    classified_files: List[dict],
    keywords: List[str],
    confidence_threshold: int = 20
) -> List[Tuple[str, int, str]]:
    """
    Match files by keywords in path or reason.

    Returns list of (file_path, confidence, reason) tuples.
    """
    matches = []

    for entry in classified_files:
        file_path = normalize_path(entry['file'])
        confidence = entry.get('confidence', 0)
        reason = entry.get('reason', '').lower()

        if confidence < confidence_threshold:
            continue

        # Check if any keyword appears in path or reason
        file_path_lower = file_path.lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in file_path_lower or keyword_lower in reason:
                matches.append((file_path, confidence, f'keyword:{keyword}'))
                break

    return matches


def attach_files_to_step(
    step: dict,
    classified_files: List[dict],
    confidence_threshold: int = 20
) -> dict:
    """
    Attach implementation files to a step based on component and keywords.
    """
    component = extract_component_from_step(step)
    step_name = step.get('name', '').lower()
    step_desc = step.get('description', '').lower()

    all_matches = []

    # Match by component mapping
    if component and component in COMPONENT_TO_FOLDER:
        folders = COMPONENT_TO_FOLDER[component]
        matches = match_files_to_folders(classified_files, folders, confidence_threshold)
        for file_path, conf, reason in matches:
            all_matches.append({
                'file': file_path,
                'confidence': conf,
                'reason': f'component:{component} -> {reason}'
            })

    # Match by keywords in step name/description
    keywords = []
    for keyword, folders in KEYWORD_TO_FOLDER.items():
        if keyword.lower() in step_name or keyword.lower() in step_desc:
            keywords.append(keyword)

    if keywords:
        for keyword in keywords:
            folders = KEYWORD_TO_FOLDER[keyword]
            matches = match_files_to_folders(classified_files, folders, confidence_threshold)
            for file_path, conf, reason in matches:
                all_matches.append({
                    'file': file_path,
                    'confidence': conf,
                    'reason': f'keyword:{keyword} -> {reason}'
                })

    # Deduplicate matches (keep highest confidence)
    file_map = {}
    for match in all_matches:
        file_path = match['file']
        if file_path not in file_map or match['confidence'] > file_map[file_path]['confidence']:
            file_map[file_path] = match

    # Sort by confidence descending
    sorted_matches = sorted(file_map.values(), key=lambda x: x['confidence'], reverse=True)

    # Add to step
    step['implementation_files'] = sorted_matches
    step['file_count'] = len(sorted_matches)

    return step


def main():
    parser = argparse.ArgumentParser(description='Attach implementation files to E2E process steps')
    parser.add_argument('--unified-schema', required=True, help='Path to unified schema YAML')
    parser.add_argument('--classification', required=True, help='Path to classification report JSON')
    parser.add_argument('--output', required=True, help='Output path for enriched schema')
    parser.add_argument('--confidence-threshold', type=int, default=20, help='Min confidence score')
    parser.add_argument('--report', help='Optional: output attachment report JSON')

    args = parser.parse_args()

    print("Loading unified schema...")
    unified_schema = load_yaml(Path(args.unified_schema))

    print("Loading classification data...")
    classification_data = load_json(Path(args.classification))

    # Extract classified files list
    if 'classifications' in classification_data:
        # Enhanced format with nested structure
        classified_files = []
        for folder, entries in classification_data['classifications'].items():
            for entry in entries:
                entry_copy = entry.copy()
                entry_copy['destination'] = folder
                classified_files.append(entry_copy)
    elif 'SUB_PATTERNS' in classification_data:
        # Enhanced format (flat)
        classified_files = []
        for folder, entries in classification_data.items():
            for entry in entries:
                entry_copy = entry.copy()
                entry_copy['destination'] = folder
                classified_files.append(entry_copy)
    else:
        # Simple format (list of files)
        classified_files = classification_data

    print(f"Processing {len(classified_files)} classified files...")

    # Process each step
    steps = unified_schema.get('steps', [])
    total_attachments = 0
    steps_with_files = 0

    for i, step in enumerate(steps):
        step_id = step.get('step_id', f'step_{i}')

        enriched_step = attach_files_to_step(
            step,
            classified_files,
            args.confidence_threshold
        )

        file_count = enriched_step.get('file_count', 0)
        if file_count > 0:
            steps_with_files += 1
            total_attachments += file_count
            print(f"  {step_id}: {file_count} files attached")

    # Update metadata
    if 'meta' not in unified_schema:
        unified_schema['meta'] = {}

    unified_schema['meta']['file_attachment_stats'] = {
        'total_steps': len(steps),
        'steps_with_files': steps_with_files,
        'total_file_attachments': total_attachments,
        'avg_files_per_step': round(total_attachments / max(steps_with_files, 1), 2),
        'confidence_threshold': args.confidence_threshold,
        'classification_source': args.classification
    }

    # Save enriched schema
    print(f"\nSaving enriched schema to {args.output}...")
    save_yaml(unified_schema, Path(args.output))

    # Generate report if requested
    if args.report:
        report = {
            'summary': unified_schema['meta']['file_attachment_stats'],
            'steps_by_file_count': defaultdict(list)
        }

        for step in steps:
            step_id = step.get('step_id', '')
            file_count = step.get('file_count', 0)
            report['steps_by_file_count'][file_count].append(step_id)

        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to {args.report}")

    print(f"\n✅ File attachment complete!")
    print(f"   Steps with files: {steps_with_files}/{len(steps)} ({steps_with_files/len(steps)*100:.1f}%)")
    print(f"   Total attachments: {total_attachments}")
    print(f"   Avg per step: {total_attachments/max(steps_with_files,1):.1f}")


if __name__ == '__main__':
    main()
