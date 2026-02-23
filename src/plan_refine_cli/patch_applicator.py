"""
Patch Applicator
Applies RFC-6902 JSON patches to plan documents with validation.
"""
import json
import jsonpatch
from pathlib import Path
from typing import Dict, Tuple

from .hash_utils import compute_json_hash


class PatchApplicator:
    """Applies and validates JSON patches to plans"""
    
    def __init__(self):
        pass
    
    def apply_patch(self, plan: Dict, patch: Dict) -> Tuple[Dict, bool, str]:
        """Apply RFC-6902 patch to plan
        
        Args:
            plan: Source plan dictionary
            patch: Patch dictionary with metadata and operations
            
        Returns:
            Tuple of (patched_plan, success, error_message)
        """
        try:
            # Validate patch structure
            if "operations" not in patch:
                return plan, False, "Patch missing 'operations' field"
            
            # Verify target hash matches
            plan_hash = compute_json_hash(plan)
            if patch.get("target_plan_hash") != plan_hash:
                return plan, False, f"Hash mismatch: expected {patch.get('target_plan_hash')}, got {plan_hash}"
            
            # Apply RFC-6902 operations
            patch_obj = jsonpatch.JsonPatch(patch["operations"])
            patched_plan = patch_obj.apply(plan)
            
            return patched_plan, True, ""
            
        except jsonpatch.JsonPatchException as e:
            return plan, False, f"Patch application failed: {str(e)}"
        except Exception as e:
            return plan, False, f"Unexpected error: {str(e)}"
    
    def validate_patch(self, patch: Dict, plan_hash: str) -> Tuple[bool, str]:
        """Validate patch structure and target
        
        Args:
            patch: Patch dictionary
            plan_hash: Expected target plan hash
            
        Returns:
            Tuple of (valid, error_message)
        """
        # Check required fields
        required_fields = ["patch_id", "created_by", "target_plan_hash", 
                          "justification", "operations"]
        for field in required_fields:
            if field not in patch:
                return False, f"Missing required field: {field}"
        
        # Verify target hash
        if patch["target_plan_hash"] != plan_hash:
            return False, "Target plan hash mismatch"
        
        # Validate operations structure
        if not isinstance(patch["operations"], list):
            return False, "Operations must be an array"
        
        for op in patch["operations"]:
            if "op" not in op or "path" not in op:
                return False, "Each operation must have 'op' and 'path'"
            if op["op"] not in ["add", "remove", "replace", "move", "copy", "test"]:
                return False, f"Invalid operation: {op['op']}"
        
        return True, ""
    
    def generate_rollback_patch(self, original_plan: Dict, patched_plan: Dict) -> Dict:
        """Generate reverse patch to rollback changes
        
        Args:
            original_plan: Plan before patch
            patched_plan: Plan after patch
            
        Returns:
            Rollback patch dictionary
        """
        from datetime import datetime
        from uuid import uuid4
        
        # Generate reverse patch operations
        patch_ops = jsonpatch.make_patch(patched_plan, original_plan)
        
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        rollback_patch = {
            "patch_id": f"PATCH_{timestamp}_{short_uuid}",
            "created_by": "PATCH_APPLICATOR",
            "target_plan_hash": compute_json_hash(patched_plan),
            "justification": ["ROLLBACK"],
            "operations": list(patch_ops),
            "metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "rollback_for": compute_json_hash(original_plan)
            }
        }
        
        return rollback_patch
    
    def dry_run_patch(self, plan: Dict, patch: Dict) -> Tuple[bool, str, Dict]:
        """Test patch application without modifying plan
        
        Args:
            plan: Source plan dictionary
            patch: Patch to test
            
        Returns:
            Tuple of (will_succeed, error_message, preview_plan)
        """
        patched_plan, success, error_msg = self.apply_patch(plan.copy(), patch)
        return success, error_msg, patched_plan if success else {}
