"""
Registry Patch Generator

Generates RFC-6902 JSON Patch operations to update the SSOT file registry
with capability mapping information derived from FILE_PURPOSE_REGISTRY.json.

This module bridges the gap between derived analysis (capability discovery)
and authoritative state (SSOT registry). It ensures NO parallel registry exists -
all durable truth lives in REGISTRY/*.json files.

Usage:
    from src.capability_mapping.P_*_registry_patch_generator import RegistryPatchGenerator
    
    generator = RegistryPatchGenerator(registry_path, purpose_registry_path)
    patches = generator.generate_patches()
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib


class RegistryPatchGenerator:
    """
    Generates RFC-6902 patches to update SSOT registry with capability mappings.
    
    Key principle: FILE_PURPOSE_REGISTRY.json is evidence, not SSOT.
    This class transforms that evidence into patches applied to the real registry.
    """
    
    def __init__(self, registry_path: Path, purpose_registry_path: Path):
        """
        Initialize generator.
        
        Args:
            registry_path: Path to SSOT file registry JSON
            purpose_registry_path: Path to derived PURPOSE_REGISTRY.json
        """
        self.registry_path = registry_path
        self.purpose_registry_path = purpose_registry_path
        
        # Load data
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)
        
        with open(purpose_registry_path, 'r', encoding='utf-8') as f:
            self.purpose_registry = json.load(f)
        
        # Build index: relative_path -> entity index
        self.path_to_index = {}
        entities = self.registry.get('entities', [])
        for i, entity in enumerate(entities):
            if entity.get('entity_kind') == 'file':
                rel_path = entity.get('relative_path')
                if rel_path:
                    self.path_to_index[rel_path] = i
    
    def resolve_entity_index(self, mapping: Dict[str, Any]) -> Optional[int]:
        """
        Resolve a mapping to its entity index in the registry.
        
        Args:
            mapping: Mapping dict from FILE_PURPOSE_REGISTRY
            
        Returns:
            Entity index, or None if not found
        """
        # Try file_id first (if present)
        file_id = mapping.get('file_id')
        if file_id:
            entities = self.registry.get('entities', [])
            for i, entity in enumerate(entities):
                if entity.get('file_id') == file_id:
                    return i
        
        # Fall back to relative_path
        rel_path = mapping.get('file')
        if rel_path in self.path_to_index:
            return self.path_to_index[rel_path]
        
        return None
    
    def generate_patches(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate RFC-6902 patch operations for registry update.
        
        Returns:
            Tuple of (patch_operations, metadata)
        """
        patches = []
        stats = {
            'mapped_files': 0,
            'unmapped_files': 0,
            'patches_generated': 0,
            'unmapped_file_list': []
        }
        
        mappings = self.purpose_registry.get('mappings', [])
        
        for mapping in mappings:
            entity_idx = self.resolve_entity_index(mapping)
            
            if entity_idx is None:
                # File not found in registry - blocking error
                stats['unmapped_files'] += 1
                stats['unmapped_file_list'].append(mapping.get('file'))
                continue
            
            stats['mapped_files'] += 1
            
            # Generate patches for this entity
            entity_patches = self._generate_entity_patches(entity_idx, mapping)
            patches.extend(entity_patches)
            stats['patches_generated'] += len(entity_patches)
        
        return patches, stats
    
    def _generate_entity_patches(self, entity_idx: int, mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate patch operations for a single entity.
        
        Args:
            entity_idx: Index in registry entities array
            mapping: Mapping dict from PURPOSE_REGISTRY
            
        Returns:
            List of RFC-6902 patch operations
        """
        patches = []
        base_path = f"/entities/{entity_idx}"
        
        # 1. Add one_line_purpose (if mapping has purpose info)
        purpose = self._extract_purpose(mapping)
        if purpose:
            patches.append({
                "op": "add",
                "path": f"{base_path}/one_line_purpose",
                "value": purpose
            })
        
        # 2. Add py_capability_tags (array of capability IDs)
        capability_ids = []
        if mapping.get('primary_capability_id'):
            capability_ids.append(mapping['primary_capability_id'])
        if mapping.get('secondary_capability_ids'):
            capability_ids.extend(mapping['secondary_capability_ids'])
        
        if capability_ids:
            patches.append({
                "op": "add",
                "path": f"{base_path}/py_capability_tags",
                "value": capability_ids
            })
        
        # 3. Add py_capability_facts_hash (deterministic hash of capability facts)
        facts_hash = self._compute_capability_facts_hash(mapping)
        patches.append({
            "op": "add",
            "path": f"{base_path}/py_capability_facts_hash",
            "value": facts_hash
        })
        
        return patches
    
    def _extract_purpose(self, mapping: Dict[str, Any]) -> Optional[str]:
        """
        Extract one-line purpose from mapping.
        
        Args:
            mapping: Mapping dict
            
        Returns:
            Purpose string or None
        """
        # Check if justification provides purpose
        justification = mapping.get('justification', '')
        if justification and len(justification) < 200:
            return justification
        
        # Try to construct from classification and capability
        classification = mapping.get('classification', '')
        primary_cap = mapping.get('primary_capability_id', '')
        
        if classification and primary_cap:
            # Convert CAP-CLI-VALIDATE_SCHEMA -> "CLI validate schema"
            cap_parts = primary_cap.replace('CAP-', '').replace('_', ' ').lower()
            return f"{classification}: {cap_parts}"
        
        return None
    
    def _compute_capability_facts_hash(self, mapping: Dict[str, Any]) -> str:
        """
        Compute deterministic hash of capability facts.
        
        Args:
            mapping: Mapping dict
            
        Returns:
            SHA256 hash (first 16 chars)
        """
        # Extract relevant facts (exclude non-deterministic fields)
        facts = {
            'primary_capability_id': mapping.get('primary_capability_id'),
            'secondary_capability_ids': sorted(mapping.get('secondary_capability_ids', [])),
            'classification': mapping.get('classification'),
            'exports': sorted(mapping.get('exports', [])),
            'called_by_observed': sorted(mapping.get('called_by_observed', []))
        }
        
        # Sort keys for determinism
        canonical = json.dumps(facts, sort_keys=True)
        hash_obj = hashlib.sha256(canonical.encode())
        
        return hash_obj.hexdigest()[:16]
    
    def generate_column_dictionary_patches(self, column_dict_path: Path) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Generate patches for column dictionary if new headers needed.
        
        Args:
            column_dict_path: Path to column dictionary JSON
            
        Returns:
            Tuple of (patch_operations, headers_already_exist)
        """
        with open(column_dict_path, 'r', encoding='utf-8') as f:
            col_dict = json.load(f)
        
        # Check if required headers exist
        required_headers = ['one_line_purpose', 'py_capability_tags', 'py_capability_facts_hash']
        existing_headers = [col.get('column_name') for col in col_dict.get('columns', [])]
        
        headers_to_add = [h for h in required_headers if h not in existing_headers]
        
        if not headers_to_add:
            return [], True  # All headers exist
        
        # Generate patches to add missing headers
        patches = []
        columns = col_dict.get('columns', [])
        next_index = len(columns)
        
        header_definitions = {
            'one_line_purpose': {
                'column_name': 'one_line_purpose',
                'description': 'One-line purpose/description of file',
                'data_type': 'string',
                'presence': 'OPTIONAL',
                'ownership': 'tool',
                'derivation_mode': 'extracted_from_capability_mapping'
            },
            'py_capability_tags': {
                'column_name': 'py_capability_tags',
                'description': 'Array of capability IDs (Python-specific)',
                'data_type': 'array[string]',
                'presence': 'OPTIONAL',
                'ownership': 'tool',
                'applicability': 'artifact_kind == python_module OR artifact_kind == python_entrypoint'
            },
            'py_capability_facts_hash': {
                'column_name': 'py_capability_facts_hash',
                'description': 'Deterministic hash of capability facts',
                'data_type': 'string',
                'presence': 'OPTIONAL',
                'ownership': 'tool'
            }
        }
        
        for header in headers_to_add:
            patches.append({
                "op": "add",
                "path": f"/columns/{next_index}",
                "value": header_definitions[header]
            })
            next_index += 1
        
        return patches, False


def generate_registry_patches(
    registry_path: Path,
    purpose_registry_path: Path,
    column_dict_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Main entry point: generate all patches needed for registry integration.
    
    Args:
        registry_path: Path to SSOT file registry
        purpose_registry_path: Path to derived PURPOSE_REGISTRY.json
        column_dict_path: Path to column dictionary
        output_dir: Directory to write patch files
        
    Returns:
        Result dict with patch file paths and metadata
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = RegistryPatchGenerator(registry_path, purpose_registry_path)
    
    # Generate registry patches
    registry_patches, stats = generator.generate_patches()
    
    # Check for unmapped files (blocking error)
    if stats['unmapped_files'] > 0:
        raise ValueError(
            f"Blocking error: {stats['unmapped_files']} mapped files not found in registry. "
            f"Files: {stats['unmapped_file_list']}"
        )
    
    # Write registry patch
    registry_patch_path = output_dir / "patch_file_registry.json"
    with open(registry_patch_path, 'w', encoding='utf-8') as f:
        json.dump(registry_patches, f, indent=2, ensure_ascii=False)
    
    # Generate column dictionary patches (if needed)
    col_patches, headers_exist = generator.generate_column_dictionary_patches(column_dict_path)
    
    col_patch_path = None
    if col_patches:
        col_patch_path = output_dir / "patch_column_dictionary.json"
        with open(col_patch_path, 'w', encoding='utf-8') as f:
            json.dump(col_patches, f, indent=2, ensure_ascii=False)
    
    return {
        'success': True,
        'registry_patch': str(registry_patch_path),
        'column_patch': str(col_patch_path) if col_patch_path else None,
        'stats': stats,
        'headers_already_exist': headers_exist
    }
