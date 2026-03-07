#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-AUTO-ATTACH-FILES-942
"""
PFA Auto-Attach Implementation Files

Automatically discovers and attaches implementation files to process steps
based on keyword matching, component names, and semantic analysis.

This tool:
1. Scans the codebase for relevant implementation files
2. Matches files to process steps using multiple strategies
3. Updates the schema with high-confidence attachments
4. Generates a report of changes made

Usage:
    python pfa_auto_attach_files.py [schema_file] [--dry-run] [--confidence-threshold 60]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-AUTO-ATTACH-FILES-942

import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
import re


class FileAttacher:
    """Automatically attach implementation files to process steps."""

    def __init__(self, confidence_threshold: int = 60, dry_run: bool = False):
        self.confidence_threshold = confidence_threshold
        self.dry_run = dry_run
        self.repo_root = Path(__file__).parent.parent.parent
        self.process_lib = Path(__file__).parent.parent

    def scan_codebase(self) -> Dict[str, Path]:
        """Scan codebase for Python, PowerShell, and YAML files."""
        files = {}

        # Scan PROCESS_STEP_LIB
        for ext in ['*.py', '*.ps1', '*.yaml', '*.yml', '*.md']:
            for filepath in self.process_lib.rglob(ext):
                if '__pycache__' not in str(filepath) and '.git' not in str(filepath):
                    rel_path = filepath.relative_to(self.repo_root)
                    files[str(rel_path)] = filepath

        # Scan phase directories
        for phase_dir in self.repo_root.glob('PHASE_*'):
            if phase_dir.is_dir():
                for ext in ['*.py', '*.ps1', '*.yaml', '*.yml', '*.md']:
                    for filepath in phase_dir.rglob(ext):
                        if '__pycache__' not in str(filepath) and '.git' not in str(filepath):
                            rel_path = filepath.relative_to(self.repo_root)
                            files[str(rel_path)] = filepath

        return files

    def extract_keywords(self, step: Dict[str, Any]) -> Set[str]:
        """Extract keywords from step for matching."""
        keywords = set()

        # Step ID components
        step_id = step.get('step_id', '')
        keywords.update(step_id.lower().split('-'))

        # Name words
        name = step.get('name', '')
        keywords.update(re.findall(r'\w+', name.lower()))

        # Operation kind
        op_kind = step.get('operation_kind', '')
        if op_kind:
            keywords.add(op_kind.lower())

        # Component name
        component = step.get('responsible_component', '')
        if component:
            keywords.update(component.lower().split('::'))
            keywords.update(re.findall(r'\w+', component.lower()))

        # Artifact refs
        for ref in step.get('artifact_registry_refs', []):
            keywords.update(re.findall(r'\w+', ref.lower()))

        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = {k for k in keywords if len(k) > 2 and k not in stopwords}

        return keywords

    def calculate_match_score(self, step: Dict[str, Any], filepath: Path,
                              step_keywords: Set[str]) -> Tuple[int, List[str]]:
        """Calculate match confidence score between step and file."""
        score = 0
        reasons = []

        filename = filepath.name.lower()
        file_content = ""

        try:
            if filepath.suffix in ['.py', '.ps1', '.yaml', '.yml', '.md']:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read().lower()
        except Exception:
            pass

        # Exact step_id match in filename (very high confidence)
        step_id = step.get('step_id', '').lower()
        if step_id in filename:
            score += 50
            reasons.append(f"Step ID '{step_id}' in filename")

        # Component name match
        component = step.get('responsible_component', '').lower()
        if component:
            component_parts = component.split('::')
            for part in component_parts:
                if part in filename:
                    score += 30
                    reasons.append(f"Component '{part}' in filename")
                if part in file_content:
                    score += 10
                    reasons.append(f"Component '{part}' in file content")

        # Operation kind match
        op_kind = step.get('operation_kind', '').lower()
        if op_kind and op_kind in filename:
            score += 25
            reasons.append(f"Operation '{op_kind}' in filename")

        # Keyword matches
        keyword_matches = []
        for keyword in step_keywords:
            if keyword in filename:
                score += 5
                keyword_matches.append(keyword)
            elif keyword in file_content:
                score += 2

        if keyword_matches:
            reasons.append(f"Keywords matched: {', '.join(keyword_matches[:5])}")

        # Phase matching
        phase = step.get('universal_phase', '')
        if phase:
            phase_num = phase.split('_')[0] if '_' in phase else ''
            if phase_num and phase_num in str(filepath):
                score += 15
                reasons.append(f"Phase {phase_num} in path")

        # File type bonuses
        if filepath.suffix == '.py' and 'validation' in step.get('name', '').lower():
            score += 10
            reasons.append("Python file for validation step")

        if filepath.suffix == '.ps1' and 'script' in step.get('name', '').lower():
            score += 10
            reasons.append("PowerShell file for script step")

        return score, reasons

    def find_matches(self, steps: List[Dict[str, Any]],
                     files: Dict[str, Path]) -> Dict[str, List[Dict[str, Any]]]:
        """Find matching files for each step."""
        matches = {}

        for step in steps:
            # Skip if already has files
            if step.get('implementation_files'):
                continue

            step_id = step.get('step_id')
            step_keywords = self.extract_keywords(step)

            step_matches = []
            for file_path_str, filepath in files.items():
                score, reasons = self.calculate_match_score(step, filepath, step_keywords)

                if score >= self.confidence_threshold:
                    step_matches.append({
                        'file': file_path_str,
                        'confidence': score,
                        'reasons': reasons
                    })

            # Sort by confidence
            step_matches.sort(key=lambda x: x['confidence'], reverse=True)

            if step_matches:
                matches[step_id] = step_matches

        return matches

    def update_schema(self, schema: Dict[str, Any],
                      matches: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Update schema with matched files."""
        steps_updated = 0
        files_attached = 0

        for step in schema.get('steps', []):
            step_id = step.get('step_id')
            if step_id in matches and not step.get('implementation_files'):
                step['implementation_files'] = matches[step_id]
                steps_updated += 1
                files_attached += len(matches[step_id])

        # Update metadata
        if 'meta' not in schema:
            schema['meta'] = {}

        if 'file_attachment_stats' not in schema['meta']:
            schema['meta']['file_attachment_stats'] = {}

        stats = schema['meta']['file_attachment_stats']
        stats['last_auto_attachment'] = datetime.now().isoformat()
        stats['steps_updated_this_run'] = steps_updated
        stats['files_attached_this_run'] = files_attached
        stats['confidence_threshold'] = self.confidence_threshold

        return schema

    def generate_report(self, matches: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate markdown report of changes."""
        md = f"""# Auto-Attach Implementation Files Report

**Generated**: {datetime.now().isoformat()}
**Confidence Threshold**: {self.confidence_threshold}
**Dry Run**: {self.dry_run}

## Summary

- **Steps Matched**: {len(matches)}
- **Total Files Attached**: {sum(len(m) for m in matches.values())}

## Matches by Step

"""

        for step_id, file_matches in sorted(matches.items()):
            md += f"\n### {step_id}\n\n"
            for match in file_matches:
                md += f"- **{match['file']}** (confidence: {match['confidence']})\n"
                for reason in match['reasons']:
                    md += f"  - {reason}\n"

        return md


def main():
    schema_path = None
    dry_run = False
    confidence_threshold = 60

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == '--dry-run':
            dry_run = True
        elif arg.startswith('--confidence-threshold='):
            confidence_threshold = int(arg.split('=')[1])
        elif not arg.startswith('--'):
            schema_path = Path(arg)

    if schema_path is None:
        schema_path = Path(__file__).parent.parent / 'schemas' / 'unified' / 'PFA_E2E_WITH_FILES.yaml'

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)

    print(f"Loading schema: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    attacher = FileAttacher(confidence_threshold=confidence_threshold, dry_run=dry_run)

    print("Scanning codebase for implementation files...")
    files = attacher.scan_codebase()
    print(f"Found {len(files)} potential implementation files")

    print("Matching files to process steps...")
    matches = attacher.find_matches(schema.get('steps', []), files)
    print(f"Found matches for {len(matches)} steps")

    # Generate report
    workspace = Path(__file__).parent.parent / 'workspace'
    workspace.mkdir(exist_ok=True)

    report_file = workspace / 'auto_attach_report.md'
    report = attacher.generate_report(matches)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report written to: {report_file}")

    if not dry_run:
        print("Updating schema...")
        schema = attacher.update_schema(schema, matches)

        # Write updated schema
        output_path = schema_path.parent / f"{schema_path.stem}_auto_attached.yaml"
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"Updated schema written to: {output_path}")
    else:
        print("DRY RUN - No changes made to schema")

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
