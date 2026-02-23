"""
Field Precedence - Per-Column Transition Rules

Handles field precedence for transitions, implementing:
- Immutable field validation
- Authoritative vs inferred scan data classification
- Field update policies per UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
"""
import json
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime

class ImmutableConflict(Exception):
    """Raised when immutable field conflicts with authoritative reality."""
    
    def __init__(self, field: str, planned_value, scan_value):
        self.field = field
        self.planned_value = planned_value
        self.scan_value = scan_value
        super().__init__(
            f"Immutable field {field} conflict: "
            f"planned={planned_value}, scan={scan_value}"
        )

def is_immutable(field: str) -> bool:
    """
    Check if field is immutable per write policy.
    
    Immutable fields never change after creation:
    - file_id: Unique identifier embedded in filename
    - record_id: Registry primary key
    - created_utc: Creation timestamp
    - original_doc_id: Historical identifier (legacy)
    """
    immutable_fields = {
        'file_id', 'record_id', 'created_utc', 'original_doc_id'
    }
    return field in immutable_fields

def emit_warning(category: str, field: str, planned_val, scan_val):
    """
    Write warning to evidence file (not CONFLICT state).
    
    Used for inferred field mismatches where planned value is preserved
    but scanner disagrees (e.g., artifact_kind inference differs).
    
    Output: .state/evidence/warnings.jsonl (append-only)
    """
    warning = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'category': category,
        'field': field,
        'planned_value': planned_val,
        'scan_value': scan_val,
        'severity': 'info'
    }
    
    warnings_file = Path('.state/evidence/warnings.jsonl')
    warnings_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(warnings_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(warning) + '\n')

def classify_scan_output(scan_fields: Dict) -> Tuple[Dict, Dict]:
    """
    Split scan data into authoritative (must overwrite) vs inferred (preserve).
    
    Authoritative: Measured facts from filesystem
    - size_bytes: File size in bytes
    - sha256: Content hash
    - mtime_utc: Last modification time
    - last_seen_utc: Scanner observation timestamp
    
    Inferred: Scanner's interpretation (can be wrong)
    - artifact_kind: Guessed file type
    - layer: Architectural layer classification
    - language: Detected programming language
    - framework: Detected framework
    
    Returns:
        (authoritative_dict, inferred_dict)
    """
    authoritative = {
        k: scan_fields[k]
        for k in ['size_bytes', 'sha256', 'mtime_utc', 'last_seen_utc']
        if k in scan_fields
    }
    inferred = {
        k: scan_fields[k]
        for k in ['artifact_kind', 'layer', 'language', 'framework']
        if k in scan_fields
    }
    return authoritative, inferred

class FieldPrecedence:
    """Applies field precedence rules during transitions."""
    
    def __init__(self, write_policy_path: Path = None):
        """Initialize with write policy (currently uses hardcoded rules)."""
        self.write_policy_path = write_policy_path
        # TODO: Load actual write policy YAML if needed
    
    def apply(self, planned_record: Dict, scan_data: Dict, transition_name: str) -> Dict:
        """
        Apply field precedence rules for transition.
        
        For PLANNED_to_PRESENT transition:
        1. Split scan_data into authoritative vs inferred
        2. Check ALL scan fields against immutability first
        3. Authoritative fields: OVERWRITE planned
        4. Inferred fields: PRESERVE planned, warn if mismatch
        5. Return mutated record
        
        Args:
            planned_record: Planned registry record
            scan_data: Observed scan data
            transition_name: Name of transition being applied
        
        Returns:
            Mutated record with field precedence applied
        
        Raises:
            ImmutableConflict: If immutable field conflicts with reality
        """
        result = planned_record.copy()
        
        if transition_name == 'PLANNED_to_PRESENT':
            # First check ALL scan_data fields against immutability
            for field, value in scan_data.items():
                if is_immutable(field):
                    if field in result and result[field] is not None and result[field] != value:
                        raise ImmutableConflict(field, result[field], value)
            
            authoritative, inferred = classify_scan_output(scan_data)
            
            # Authoritative fields: OVERWRITE planned
            for field, value in authoritative.items():
                result[field] = value
            
            # Inferred fields: PRESERVE planned, only warn if mismatch
            for field, value in inferred.items():
                if field not in result or result[field] is None:
                    # Fill null with inference
                    result[field] = value
                elif result[field] != value:
                    # Mismatch: preserve planned, emit warning
                    emit_warning('inference_mismatch', field, result[field], value)
        
        return result
