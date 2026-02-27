#!/usr/bin/env python3
"""
Script Name Resolver
Maps logical script names to actual file IDs in the mapp_py directory.

Purpose: Bridge between Column to Script Mapping JSON (logical names) 
         and actual file system (P_*_*.py files).
"""
from pathlib import Path
from typing import Dict, Optional, List

# Authoritative mapping from logical → actual file names
SCRIPT_NAME_MAP: Dict[str, str] = {
    # Phase A: Static Analysis
    'text_normalizer.py': 'P_01260202173939000060_text_normalizer.py',
    'python_ast_parser.py': 'P_01260202173939000061_component_extractor.py',
    'component_extractor.py': 'P_01260202173939000061_component_extractor.py',
    'component_id_generator.py': 'P_01260202173939000062_generate_component_signature.py',
    'dependency_analyzer.py': 'P_01260202173939000063_dependency_analyzer.py',
    'io_surface_analyzer.py': 'P_01260202173939000064_i_o_surface_visitor.py',
    'io_surface_visitor.py': 'P_01260202173939000064_i_o_surface_visitor.py',
    'deliverable_analyzer.py': 'P_01260202173939000065_deliverable_analyzer.py',
    'structural_feature_extractor.py': 'P_01260202173939000066_structural_feature_extractor.py',
    'extract_semantic_features.py': 'P_01260202173939000067_extract_semantic_features.py',
    'semantic_similarity.py': 'P_01260202173939000067_extract_semantic_features.py',
    'file_comparator.py': 'P_01260202173939000068_file_comparator.py',
    'capability_tagger.py': 'P_01260202173939000076_capability_detector.py',
    'capability_detector.py': 'P_01260202173939000076_capability_detector.py',
    'compute_sha256_hash_of_evidence.py': 'P_01260202173939000077_compute_sha_256_hash_of_evidence.py',
    'analyze_file.py': 'P_01260202173939000079_analyze_file.py',
    
    # Phase B: Quality Metrics
    'test_runner.py': 'P_01260202173939000069_analyze_tests.py',
    'analyze_tests.py': 'P_01260202173939000069_analyze_tests.py',
    'linter_runner.py': 'P_01260202173939000070_run_pylint_on_file.py',
    'run_pylint_on_file.py': 'P_01260202173939000070_run_pylint_on_file.py',
    'complexity_analyzer.py': 'P_01260202173939000071_complexity_visitor.py',
    'complexity_visitor.py': 'P_01260202173939000071_complexity_visitor.py',
    
    # Phase C: Similarity (new scripts to be created)
    'quality_scorer.py': 'P_01260202173939000085_quality_scorer.py',
    'similarity_clusterer.py': 'P_01260202173939000086_similarity_clusterer.py',
    'canonical_ranker.py': 'P_01260202173939000087_canonical_ranker.py',
    
    # Orchestrator (new script to be created)
    'registry_integration_pipeline.py': 'P_01260202173939000084_registry_integration_pipeline.py',
    
    # Alternate versions (duplicates)
    'component_extractor_v2.py': 'P_01260202173939000080_component_extractor.py',
    'dependency_analyzer_v2.py': 'P_01260202173939000082_dependency_analyzer.py',
    'io_surface_analyzer_v2.py': 'P_01260202173939000083_i_o_surface_analyzer.py',
}

# Reverse map for discovery
ACTUAL_TO_LOGICAL: Dict[str, str] = {v: k for k, v in SCRIPT_NAME_MAP.items()}


def resolve_script_path(logical_name: str, base_dir: Path) -> Path:
    """
    Resolve logical script name to actual file path.
    
    Args:
        logical_name: Logical script name (e.g., 'text_normalizer.py')
        base_dir: Base directory containing scripts
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If script not found
    """
    # Try direct mapping first
    actual_name = SCRIPT_NAME_MAP.get(logical_name, logical_name)
    script_path = base_dir / actual_name
    
    if script_path.exists():
        return script_path
    
    # Try legacy DOC-SCRIPT pattern
    doc_pattern = f"DOC-SCRIPT-*__{logical_name}"
    matches = list(base_dir.glob(doc_pattern))
    if matches:
        return matches[0]
    
    # Try without P_ prefix (if logical name has prefix)
    if logical_name.startswith('P_'):
        bare_name = logical_name.split('_', 2)[-1] if logical_name.count('_') >= 2 else logical_name
        return resolve_script_path(bare_name, base_dir)
    
    raise FileNotFoundError(
        f"Script not found: {logical_name}\n"
        f"  Expected: {actual_name}\n"
        f"  In directory: {base_dir}\n"
        f"  Tried patterns: {doc_pattern}"
    )


def get_logical_name(actual_name: str) -> Optional[str]:
    """
    Get logical name from actual filename.
    
    Args:
        actual_name: Actual filename (e.g., 'P_01260202173939000060_text_normalizer.py')
        
    Returns:
        Logical name or None if not in map
    """
    return ACTUAL_TO_LOGICAL.get(actual_name)


def list_all_scripts() -> Dict[str, str]:
    """
    Return complete mapping of logical → actual names.
    
    Returns:
        Copy of SCRIPT_NAME_MAP
    """
    return SCRIPT_NAME_MAP.copy()


def validate_all_scripts(base_dir: Path) -> Dict[str, bool]:
    """
    Validate that all mapped scripts exist.
    
    Args:
        base_dir: Base directory containing scripts
        
    Returns:
        Dict mapping logical_name → exists (bool)
    """
    results = {}
    for logical_name, actual_name in SCRIPT_NAME_MAP.items():
        script_path = base_dir / actual_name
        results[logical_name] = script_path.exists()
    return results


def get_missing_scripts(base_dir: Path) -> List[str]:
    """
    Get list of scripts that are mapped but don't exist.
    
    Args:
        base_dir: Base directory containing scripts
        
    Returns:
        List of logical names for missing scripts
    """
    validation = validate_all_scripts(base_dir)
    return [name for name, exists in validation.items() if not exists]


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Script Name Resolver Utility')
    parser.add_argument('--list', action='store_true', help='List all mappings')
    parser.add_argument('--validate', action='store_true', help='Validate all scripts exist')
    parser.add_argument('--resolve', help='Resolve a logical name to actual path')
    parser.add_argument('--base-dir', help='Base directory (default: current dir)')
    
    args = parser.parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    if args.list:
        print("Logical Name → Actual File Name")
        print("=" * 80)
        for logical, actual in sorted(SCRIPT_NAME_MAP.items()):
            exists = "✓" if (base_dir / actual).exists() else "✗"
            print(f"{exists} {logical:40} → {actual}")
    
    elif args.validate:
        validation = validate_all_scripts(base_dir)
        missing = [name for name, exists in validation.items() if not exists]
        
        print(f"Validation Results: {len(validation)} scripts")
        print(f"  Existing: {len(validation) - len(missing)}")
        print(f"  Missing: {len(missing)}")
        
        if missing:
            print("\nMissing Scripts:")
            for name in sorted(missing):
                print(f"  ✗ {name} → {SCRIPT_NAME_MAP[name]}")
            sys.exit(1)
        else:
            print("\n✅ All scripts exist!")
            sys.exit(0)
    
    elif args.resolve:
        try:
            resolved = resolve_script_path(args.resolve, base_dir)
            print(f"Resolved: {args.resolve} → {resolved}")
            print(f"Exists: {resolved.exists()}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()
