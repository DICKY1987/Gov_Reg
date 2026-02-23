"""
Policy Manager
Loads, validates, and manages planning policy snapshots.
"""
import json
import jsonschema
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4

from .hash_utils import compute_json_hash


class PolicyManager:
    """Manages planning policy snapshots"""
    
    def __init__(self, schema_dir: Path):
        self.schema_dir = Path(schema_dir)
        self._policy_schema = None
    
    def load_policy_schema(self) -> Dict:
        """Load planning_policy_snapshot.schema.json"""
        if self._policy_schema is None:
            schema_path = self.schema_dir / "planning_policy_snapshot.schema.json"
            with open(schema_path, 'r') as f:
                self._policy_schema = json.load(f)
        return self._policy_schema
    
    def load_policy(self, policy_path: Path) -> Dict:
        """Load and validate policy from file
        
        Args:
            policy_path: Path to policy JSON file
            
        Returns:
            Validated policy dictionary
            
        Raises:
            jsonschema.ValidationError: If policy is invalid
        """
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        schema = self.load_policy_schema()
        jsonschema.validate(policy, schema)
        
        return policy
    
    def create_policy_snapshot(self, base_policy: Dict, run_id: str) -> Dict:
        """Create immutable policy snapshot for a run
        
        Args:
            base_policy: Base policy configuration
            run_id: Planning run identifier
            
        Returns:
            Policy snapshot with metadata
        """
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        snapshot = {
            "policy_id": f"POLICY_{timestamp}_{short_uuid}",
            "version": base_policy.get("version", "1.0.0"),
            "required_plan_sections": base_policy["required_plan_sections"],
            "defect_taxonomy": base_policy["defect_taxonomy"],
            "rule_catalog": base_policy["rule_catalog"],
            "iteration_limits": base_policy["iteration_limits"],
            "critic_mode": base_policy.get("critic_mode", "DETERMINISTIC"),
            "forbidden_patterns": base_policy.get("forbidden_patterns", []),
            "allowed_patch_operations": base_policy.get(
                "allowed_patch_operations",
                ["add", "remove", "replace"]
            ),
            "snapshot_metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "planning_run_id": run_id,
                "base_policy_hash": compute_json_hash(base_policy)
            }
        }
        
        # Validate snapshot
        schema = self.load_policy_schema()
        jsonschema.validate(snapshot, schema)
        
        return snapshot
    
    def save_policy_snapshot(self, snapshot: Dict, output_path: Path):
        """Save policy snapshot to file
        
        Args:
            snapshot: Policy snapshot dictionary
            output_path: Path to save snapshot
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    def get_policy_hash(self, policy: Dict) -> str:
        """Compute hash of policy configuration
        
        Args:
            policy: Policy dictionary
            
        Returns:
            SHA256 hash of policy
        """
        return compute_json_hash(policy)
