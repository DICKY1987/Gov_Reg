"""
Reconciliation - PFMS vs Reality Comparison

Compares planned state (PFMS) with actual filesystem state.

States per spec Section 4.2:
- EXACT_MATCH: All files match
- SUBSET_MATCH: Some files match, none diverged
- PARTIAL_OVERLAP: Some match, some diverged
- DIVERGED: Content differs but files exist
- NO_OVERLAP: Complete mismatch (CRITICAL)
"""

from enum import Enum
from typing import Dict, List, Set
from pathlib import Path
import logging

from .canonical_hash import hash_file_content
from .registry_schema_v3 import ReconciliationState

logger = logging.getLogger(__name__)


class Reconciliation:
    """Compare PFMS planned state with filesystem reality."""
    
    def reconcile_pfms_with_reality(self, pfms: Dict) -> Dict:
        """
        Compare PFMS planned state with actual filesystem state.
        
        Args:
            pfms: PFMS dict with mutations
        
        Returns:
            Reconciliation report dict
        """
        mutations = pfms.get('mutations', {})
        planned_paths = set()
        
        # Collect all planned paths
        for file_info in mutations.get('created_files', []):
            planned_paths.add(file_info['relative_path'])
        for file_info in mutations.get('modified_files', []):
            planned_paths.add(file_info['relative_path'])
        
        # Compare with filesystem
        exact_matches = 0
        content_diverged = 0
        missing_files = 0
        planned_hashes = {}
        actual_hashes = {}
        
        for path in planned_paths:
            file_path = Path(path)
            
            # Check file exists
            if not file_path.exists():
                missing_files += 1
                logger.warning(f"Planned file missing: {path}")
                continue
            
            # Get planned content_hash
            planned_hash = None
            for file_info in mutations.get('created_files', []) + mutations.get('modified_files', []):
                if file_info.get('relative_path') == path:
                    planned_hash = file_info.get('expected_content_hash')
                    break
            
            # Compute actual content_hash
            try:
                actual_hash = hash_file_content(file_path)
                actual_hashes[path] = actual_hash
            except Exception as e:
                logger.error(f"Failed to hash {path}: {e}")
                content_diverged += 1
                continue
            
            # Compare
            if planned_hash and planned_hash == actual_hash:
                exact_matches += 1
                logger.debug(f"Exact match: {path}")
            elif planned_hash:
                content_diverged += 1
                logger.warning(f"Content diverged: {path}")
                planned_hashes[path] = planned_hash
            else:
                # No expected hash provided - count as match if file exists
                exact_matches += 1
                logger.debug(f"File exists (no hash check): {path}")
        
        # Determine reconciliation state
        total_planned = len(planned_paths)
        
        if total_planned == 0:
            state = ReconciliationState.EXACT_MATCH
        elif exact_matches == total_planned:
            state = ReconciliationState.EXACT_MATCH
        elif exact_matches > 0 and missing_files == 0 and content_diverged == 0:
            state = ReconciliationState.SUBSET_MATCH
        elif exact_matches > 0:
            state = ReconciliationState.PARTIAL_OVERLAP
        elif missing_files == total_planned:
            state = ReconciliationState.NO_OVERLAP  # CRITICAL FAILURE
            logger.error(f"NO_OVERLAP detected for plan {pfms.get('plan_id')} - all files missing!")
        else:
            state = ReconciliationState.DIVERGED
        
        report = {
            'plan_id': pfms.get('plan_id'),
            'mutation_set_id': pfms.get('mutation_set_id'),
            'reconciliation_state': state.value,
            'exact_matches': exact_matches,
            'content_diverged': content_diverged,
            'missing_files': missing_files,
            'total_planned': total_planned,
            'diverged_files': list(planned_hashes.keys()) if content_diverged > 0 else []
        }
        
        logger.info(f"Reconciliation: {state.value} ({exact_matches}/{total_planned} exact)")
        
        return report


def reconcile_pfms(pfms: Dict) -> Dict:
    """Reconcile PFMS with reality (convenience wrapper)."""
    reconciliation = Reconciliation()
    return reconciliation.reconcile_pfms_with_reality(pfms)
