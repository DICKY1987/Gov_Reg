#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-CONVERT-TO-CANONICAL-945
"""
PFA Convert to Canonical Schema Tool

Converts E2E unified schema to canonical format by stripping E2E-specific
extension fields and reverting to original phase/operation taxonomy.

Usage:
    python pfa_convert_to_canonical.py --input unified.yaml --output canonical.yaml
    python pfa_convert_to_canonical.py --all  # Convert current unified schema
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-CONVERT-TO-CANONICAL-945

import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class CanonicalConverter:
    """Converts unified E2E schema to canonical format"""
    
    # Canonical schema fields (34 total)
    CANONICAL_FIELDS = {
        # Core identification
        'step_id',
        'phase',
        'name',
        'description',
        
        # Component & operation
        'responsible_component',
        'operation_kind',
        
        # I/O & validation
        'inputs',
        'expected_outputs',
        'requires_human_confirmation',
        
        # Sequencing
        'order',
        
        # Metadata
        'lens',
        'automation_level',
        'pattern_ids',
        'artifact_registry_refs',
        'guardrail_checkpoint',
        'guardrail_checkpoint_id',
        
        # Implementation
        'implementation_files',
        'artifacts_created',
        'artifacts_updated',
        'metrics_emitted',
        
        # Conditions
        'preconditions',
        'postconditions',
        'error_handling',
        'state_transition',
        'anti_pattern_ids',
        
        # System
        '_content_hash',
    }
    
    # E2E extension fields to strip
    EXTENSION_FIELDS = {
        'original_step_id',
        'source_schema',
        'universal_phase',
        'original_phase',
        'substage',
        'unified_operation_category',
        'original_operation_kind',
        'merge_metadata',
    }
    
    def __init__(self, preserve_e2e_ids: bool = False, include_provenance: bool = False):
        """
        Initialize converter
        
        Args:
            preserve_e2e_ids: Keep E2E-xxx step IDs instead of reverting to originals
            include_provenance: Add comment with E2E provenance data
        """
        self.preserve_e2e_ids = preserve_e2e_ids
        self.include_provenance = include_provenance
        self.stats = {
            'steps_converted': 0,
            'fields_stripped': 0,
            'phases_reverted': 0,
            'operations_reverted': 0,
        }
    
    def convert_schema(self, unified_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert unified schema to canonical format
        
        Args:
            unified_schema: Unified E2E schema dict
            
        Returns:
            Canonical schema dict
        """
        canonical = {
            'meta': self._convert_meta(unified_schema.get('meta', {})),
            'steps': []
        }
        
        for step in unified_schema.get('steps', []):
            canonical_step = self._convert_step(step)
            canonical['steps'].append(canonical_step)
            self.stats['steps_converted'] += 1
        
        return canonical
    
    def _convert_meta(self, unified_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Convert meta section to canonical format"""
        canonical_meta = {
            'process_id': 'PFA-E2E-CANONICAL',
            'source_file': 'PROCESS_STEP_LIB\\PFA_E2E_CANONICAL_PROCESS_STEPS_SCHEMA.yaml',
            'normalized_by': 'pfa_convert_to_canonical.py',
        }
        
        if self.include_provenance:
            canonical_meta['converted_from'] = {
                'schema_id': unified_meta.get('schema_id'),
                'version': unified_meta.get('version'),
                'source_schemas': unified_meta.get('source_schemas', []),
                'conversion_date': datetime.utcnow().isoformat() + 'Z',
            }
        
        return canonical_meta
    
    def _convert_step(self, unified_step: Dict[str, Any]) -> Dict[str, Any]:
        """Convert single step to canonical format"""
        canonical_step = {}
        
        # 1. Handle step_id
        if self.preserve_e2e_ids:
            canonical_step['step_id'] = unified_step.get('step_id')
        else:
            # Revert to original step ID
            canonical_step['step_id'] = unified_step.get('original_step_id', unified_step.get('step_id'))
            if unified_step.get('original_step_id'):
                self.stats['phases_reverted'] += 1
        
        # 2. Handle phase (revert to original)
        if 'original_phase' in unified_step:
            canonical_step['phase'] = unified_step['original_phase']
            self.stats['phases_reverted'] += 1
        else:
            canonical_step['phase'] = unified_step.get('phase', unified_step.get('universal_phase'))
        
        # 3. Handle operation_kind (revert to original)
        if 'original_operation_kind' in unified_step:
            canonical_step['operation_kind'] = unified_step['original_operation_kind']
            self.stats['operations_reverted'] += 1
        else:
            canonical_step['operation_kind'] = unified_step.get('operation_kind')
        
        # 4. Copy all canonical fields
        for field in self.CANONICAL_FIELDS:
            if field in ['step_id', 'phase', 'operation_kind']:
                continue  # Already handled above
            
            if field in unified_step:
                canonical_step[field] = unified_step[field]
            else:
                # Set default values for missing fields
                canonical_step[field] = self._get_default_value(field)
        
        # 5. Count stripped fields
        for field in unified_step:
            if field in self.EXTENSION_FIELDS:
                self.stats['fields_stripped'] += 1
        
        # 6. Optional: Add provenance comment
        if self.include_provenance and 'source_schema' in unified_step:
            canonical_step['_provenance'] = {
                'source_schema': unified_step['source_schema'],
                'universal_phase': unified_step.get('universal_phase'),
                'e2e_step_id': unified_step.get('step_id'),
            }
        
        return canonical_step
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for canonical field"""
        # Array fields default to empty list
        if field in ['inputs', 'expected_outputs', 'pattern_ids', 'artifact_registry_refs',
                     'implementation_files', 'artifacts_created', 'artifacts_updated',
                     'metrics_emitted', 'preconditions', 'postconditions', 'anti_pattern_ids']:
            return []
        
        # Boolean fields default to False
        if field in ['requires_human_confirmation', 'guardrail_checkpoint']:
            return False
        
        # Nullable fields default to None
        if field in ['order', 'lens', 'automation_level', 'guardrail_checkpoint_id',
                     'error_handling', 'state_transition', '_content_hash']:
            return None
        
        # String fields default to empty string or None
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        return self.stats.copy()


def load_yaml(filepath: Path) -> Dict[str, Any]:
    """Load YAML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], filepath: Path):
    """Save YAML file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(
        description='Convert E2E unified schema to canonical format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert specific file
  python pfa_convert_to_canonical.py --input unified.yaml --output canonical.yaml
  
  # Convert current unified schema
  python pfa_convert_to_canonical.py --all
  
  # Keep E2E step IDs
  python pfa_convert_to_canonical.py --all --preserve-e2e-ids
  
  # Include provenance metadata
  python pfa_convert_to_canonical.py --all --include-provenance
"""
    )
    
    parser.add_argument('--input', type=str, help='Input unified schema YAML file')
    parser.add_argument('--output', type=str, help='Output canonical schema YAML file')
    parser.add_argument('--all', action='store_true', 
                       help='Convert PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml')
    parser.add_argument('--preserve-e2e-ids', action='store_true',
                       help='Keep E2E-xxx step IDs instead of reverting to originals')
    parser.add_argument('--include-provenance', action='store_true',
                       help='Include E2E provenance metadata in converted schema')
    parser.add_argument('--stats', action='store_true',
                       help='Print detailed conversion statistics')
    
    args = parser.parse_args()
    
    # Determine input/output files
    if args.all:
        input_file = Path('PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml')
        output_file = Path('PFA_E2E_CANONICAL_PROCESS_STEPS_SCHEMA.yaml')
    elif args.input and args.output:
        input_file = Path(args.input)
        output_file = Path(args.output)
    else:
        parser.print_help()
        print("\nError: Either --all or both --input and --output are required")
        sys.exit(1)
    
    # Validate input exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print("━" * 70)
    print("PFA CANONICAL CONVERTER")
    print("━" * 70)
    print()
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print(f"Preserve E2E IDs: {args.preserve_e2e_ids}")
    print(f"Include Provenance: {args.include_provenance}")
    print()
    
    # Load unified schema
    print("Loading unified schema...")
    unified_schema = load_yaml(input_file)
    
    steps_count = len(unified_schema.get('steps', []))
    print(f"  ✓ Loaded {steps_count} steps")
    print()
    
    # Convert to canonical
    print("Converting to canonical format...")
    converter = CanonicalConverter(
        preserve_e2e_ids=args.preserve_e2e_ids,
        include_provenance=args.include_provenance
    )
    canonical_schema = converter.convert_schema(unified_schema)
    
    # Get statistics
    stats = converter.get_statistics()
    print(f"  ✓ Converted {stats['steps_converted']} steps")
    print(f"  ✓ Stripped {stats['fields_stripped']} extension fields")
    print(f"  ✓ Reverted {stats['phases_reverted']} phases to original")
    print(f"  ✓ Reverted {stats['operations_reverted']} operations to original")
    print()
    
    # Save canonical schema
    print("Saving canonical schema...")
    save_yaml(canonical_schema, output_file)
    
    output_size = output_file.stat().st_size / 1024
    print(f"  ✓ Saved to {output_file} ({output_size:.1f} KB)")
    print()
    
    # Print detailed statistics
    if args.stats:
        print("━" * 70)
        print("DETAILED STATISTICS")
        print("━" * 70)
        print()
        print(f"Steps converted:       {stats['steps_converted']}")
        print(f"Fields stripped:       {stats['fields_stripped']}")
        print(f"Phases reverted:       {stats['phases_reverted']}")
        print(f"Operations reverted:   {stats['operations_reverted']}")
        print()
        
        # Calculate reduction
        input_size = input_file.stat().st_size / 1024
        reduction = ((input_size - output_size) / input_size) * 100
        print(f"File size reduction:   {reduction:.1f}%")
        print(f"  Before: {input_size:.1f} KB")
        print(f"  After:  {output_size:.1f} KB")
        print()
    
    print("━" * 70)
    print("✓ CONVERSION COMPLETE")
    print("━" * 70)
    print()
    print("Generated files:")
    print(f"  • {output_file} (canonical format)")
    print()
    print("Next steps:")
    print(f"  • Validate: python PFA_validate_process_steps_schema.py --schema {output_file}")
    print(f"  • View: code {output_file}")
    print()


if __name__ == '__main__':
    main()
