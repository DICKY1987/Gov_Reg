#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-PFA-EXTRACT-GLOSSARY-TERMS-001
"""
Extract Glossary Terms from Process Schemas

Automatically identifies new terminology in process schemas and generates
term proposals for glossary review.

Usage:
    python pfa_extract_glossary_terms.py --schema PFA_GLOSSARY_PROCESS_STEPS_SCHEMA.yaml
    python pfa_extract_glossary_terms.py --all-schemas
    python pfa_extract_glossary_terms.py --all-schemas --output proposals.yaml
"""
# DOC_ID: DOC-SCRIPT-PFA-EXTRACT-GLOSSARY-TERMS-001

import re
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

# Add parent to path
.parent.parent))

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
GLOSSARY_ROOT = REPO_ROOT / 'SUB_GLOSSARY'
GLOSSARY_METADATA = GLOSSARY_ROOT / '.glossary-metadata.yaml'
UPDATES_DIR = GLOSSARY_ROOT / 'updates'
SCHEMAS_DIR = Path(__file__).parent.parent / 'schemas' / 'source'


@dataclass
class TermCandidate:
    """Candidate term extracted from schema."""
    term: str
    context: str
    source_file: str
    source_step: str
    confidence: str  # high, medium, low
    suggested_category: str


class TermExtractor:
    """Extract glossary terms from process schemas."""

    def __init__(self):
        self.existing_terms: Set[str] = set()
        self.candidates: List[TermCandidate] = []
        self.load_existing_terms()

    def load_existing_terms(self):
        """Load existing glossary terms."""
        if not GLOSSARY_METADATA.exists():
            print(f"⚠️  No glossary metadata found at {GLOSSARY_METADATA}")
            return

        try:
            with open(GLOSSARY_METADATA, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}

            terms = metadata.get('terms', {})

            for term_id, term_data in terms.items():
                name = term_data.get('name', '').lower()
                self.existing_terms.add(name)

            print(f"✅ Loaded {len(self.existing_terms)} existing terms")
        except Exception as e:
            print(f"❌ Failed to load glossary metadata: {e}")

    def extract_from_schema(self, schema_path: Path):
        """Extract terms from a single schema."""
        print(f"\n📖 Extracting from {schema_path.name}...")

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f) or {}

            steps = schema.get('steps', [])

            for step in steps:
                self.extract_from_step(step, schema_path.name)

            print(f"   ✓ Found {len(self.candidates)} candidates")
        except Exception as e:
            print(f"   ❌ Failed to extract from {schema_path}: {e}")

    def extract_from_step(self, step: Dict, source_file: str):
        """Extract terms from a single step."""
        step_id = step.get('step_id', 'unknown')

        # Extract from operation_kind (high confidence)
        op_kind = step.get('operation_kind', '')
        if op_kind and '_' in op_kind:
            # Split compound terms: term_proposal → term, proposal
            parts = op_kind.split('_')
            for part in parts:
                if len(part) > 3 and self.is_new_term(part):
                    self.candidates.append(TermCandidate(
                        term=part.capitalize(),
                        context=f"Operation kind: {op_kind}",
                        source_file=source_file,
                        source_step=step_id,
                        confidence='high',
                        suggested_category='FRAME'
                    ))

        # Extract from responsible_component (high confidence)
        component = step.get('responsible_component', '')
        if component and '::' in component:
            # Extract component names: glossary::update_term → glossary, update_term
            parts = component.split('::')
            for part in parts:
                if len(part) > 3 and self.is_new_term(part):
                    self.candidates.append(TermCandidate(
                        term=part.capitalize(),
                        context=f"Component: {component}",
                        source_file=source_file,
                        source_step=step_id,
                        confidence='high',
                        suggested_category='ENGINE'
                    ))

        # Extract significant terms from step name (medium confidence)
        name = step.get('name', '')
        if len(name) > 10:  # Only substantial names
            name_terms = self.extract_significant_terms(name)
            for term in name_terms[:3]:  # Top 3 only
                if self.is_new_term(term):
                    self.candidates.append(TermCandidate(
                        term=term.capitalize(),
                        context=f"Step: {name[:50]}",
                        source_file=source_file,
                        source_step=step_id,
                        confidence='medium',
                        suggested_category='ENGINE'
                    ))

    def extract_significant_terms(self, text: str) -> List[str]:
        """Extract significant terms from text."""
        # Common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were',
            'this', 'that', 'these', 'those', 'into', 'onto', 'than', 'then'
        }

        # Split on spaces and punctuation
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        # Filter stopwords and short words
        significant = [w for w in words if w not in stopwords and len(w) > 4]

        # Group into bigrams for compound terms
        bigrams = []
        for i in range(len(significant) - 1):
            bigram = f"{significant[i]} {significant[i+1]}"
            bigrams.append(bigram)

        return list(set(significant + bigrams))[:10]  # Top 10

    def is_new_term(self, term: str) -> bool:
        """Check if term is new (not in glossary)."""
        normalized = term.lower().strip()
        return normalized not in self.existing_terms and len(normalized) > 3

    def generate_proposal(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Generate YAML patch spec for proposals."""
        if not self.candidates:
            print("\nℹ️  No new terms to propose")
            return None

        # Filter duplicates, prioritize high confidence
        unique_terms = {}
        for candidate in sorted(self.candidates,
                               key=lambda c: {'high': 3, 'medium': 2, 'low': 1}[c.confidence],
                               reverse=True):
            term_key = candidate.term.lower()
            if term_key not in unique_terms:
                unique_terms[term_key] = candidate

        # Generate patch spec
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        patch_id = f"AUTO-EXTRACT-{timestamp}"

        proposal_data = {
            'patch_id': patch_id,
            'description': f'Auto-extracted terms from process schemas ({len(unique_terms)} candidates)',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'author': 'pfa_extract_glossary_terms.py',
            'source': 'automated_extraction',
            'terms': []
        }

        for term_key, candidate in unique_terms.items():
            term_data = {
                'name': candidate.term,
                'category': candidate.suggested_category,
                'definition': f'[REVIEW NEEDED] {candidate.context}',
                'status': 'proposed',
                'source': {
                    'extraction_source': candidate.source_file,
                    'source_step': candidate.source_step,
                    'confidence': candidate.confidence,
                    'extracted_at': datetime.now().isoformat()
                }
            }
            proposal_data['terms'].append(term_data)

        # Save to updates directory
        if not output_path:
            UPDATES_DIR.mkdir(exist_ok=True)
            output_path = UPDATES_DIR / f'extracted-terms-{timestamp}.yaml'

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(proposal_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            print(f"\n✅ Generated proposal: {output_path}")
            print(f"   📊 {len(unique_terms)} unique terms proposed")
            print(f"   📝 Review and apply with:")
            print(f"      cd {GLOSSARY_ROOT}")
            print(f"      python glossary/update_term.py --spec updates/{output_path.name} --apply")

            return output_path
        except Exception as e:
            print(f"\n❌ Failed to save proposal: {e}")
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract glossary terms from process schemas")
    parser.add_argument('--schema', type=str, help='Single schema file to process')
    parser.add_argument('--all-schemas', action='store_true', help='Process all schemas')
    parser.add_argument('--output', type=str, help='Output proposal file path')

    args = parser.parse_args()

    print("="*70)
    print("  GLOSSARY TERM EXTRACTOR")
    print("="*70)

    extractor = TermExtractor()

    if args.all_schemas:
        schema_files = list(SCHEMAS_DIR.glob('PFA_*.yaml'))
        print(f"\n📁 Found {len(schema_files)} schema files")

        for schema_file in schema_files:
            extractor.extract_from_schema(schema_file)

    elif args.schema:
        schema_path = SCHEMAS_DIR / args.schema
        if not schema_path.exists():
            print(f"❌ Schema not found: {schema_path}")
            sys.exit(1)
        extractor.extract_from_schema(schema_path)

    else:
        print("❌ Specify --schema or --all-schemas")
        parser.print_help()
        sys.exit(1)

    # Generate proposal
    output_path = Path(args.output) if args.output else None
    result = extractor.generate_proposal(output_path)

    if result:
        print("\n" + "="*70)
        print("  ✅ EXTRACTION COMPLETE")
        print("="*70)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
