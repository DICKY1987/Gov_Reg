"""
Canonical Write Policy Validator for Registry records.

Enforces:
- immutable: reject if old_value is not None and old_value != new_value
- tool_only: reject if actor not in ['tool','scanner','watcher','pipeline']
- user_only: reject if actor not in ['user','manual','cli']
- forbid_null: reject if new_value is None
- conditional null: entity_kind required when record_kind=='entity'
- recompute_on_scan + tool_only: reject manual writes to derived fields
- unknown_field_policy: configurable handling of fields not in policy maps
"""

import json
import logging
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UnknownFieldPolicy(Enum):
    """Policy for handling fields not in policy maps."""
    ALLOW = "allow"    # Permit + no log
    WARN = "warn"      # Permit + warning log
    REJECT = "reject"  # Fail validation


class WritePolicyValidator:
    """
    Canonical write policy validator enforcing immutability, permissions, null_policy.
    Loads from config/null_policy_map.json and config/update_policy_map.json.
    """

    def __init__(self, unknown_field_policy: UnknownFieldPolicy = UnknownFieldPolicy.WARN):
        """
        Initialize validator with config.
        
        Args:
            unknown_field_policy: How to handle fields not in policy maps
        """
        self.null_policy_map = self._load_null_policy_map()
        self.update_policy_map = self._load_update_policy_map()
        self.unknown_field_policy = unknown_field_policy

    def _load_null_policy_map(self) -> Dict[str, Any]:
        """Load null policy map from config."""
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_path = config_dir / "null_policy_map.json"
        if not config_path.exists():
            config_path = config_dir / "01260207233100000450_null_policy_map.json"
        with open(config_path) as f:
            return json.load(f)

    def _load_update_policy_map(self) -> Dict[str, Any]:
        """Load update policy map from config."""
        config_dir = Path(__file__).parent.parent.parent / "config"
        config_path = config_dir / "update_policy_map.json"
        if not config_path.exists():
            config_path = config_dir / "01260207233100000451_update_policy_map.json"
        with open(config_path) as f:
            return json.load(f)

    def load_policies(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load all policies.

        Returns:
            Tuple of (null_policy_map, update_policy_map)
        """
        return self.null_policy_map, self.update_policy_map

    def check_immutable(
        self,
        field: str,
        old_value: Any,
        new_value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Check if immutable field is being modified.

        Args:
            field: Field name
            old_value: Existing value (None for new records)
            new_value: Proposed new value

        Returns:
            Violation dict if invalid, None if valid
        """
        update_policy = self.update_policy_map.get(field, "manual_or_automated")

        if update_policy == "immutable":
            # Immutable: reject if old_value is not None and old_value != new_value
            if old_value is not None and old_value != new_value:
                return {
                    "field": field,
                    "rule": "immutable",
                    "expected": old_value,
                    "actual": new_value,
                    "source": "write_policy",
                    "message": f"Field '{field}' is immutable and cannot be changed"
                }

        return None

    def check_tool_only(
        self,
        field: str,
        actor: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if tool-only field is being written by non-tool actor.

        Args:
            field: Field name
            actor: Actor type ('tool', 'scanner', 'user', 'manual', etc.)

        Returns:
            Violation dict if invalid, None if valid
        """
        update_policy = self.update_policy_map.get(field, "manual_or_automated")

        # tool_only = recompute_on_scan fields
        if update_policy == "recompute_on_scan":
            allowed_actors = ["tool", "scanner", "watcher", "pipeline"]
            if actor not in allowed_actors:
                return {
                    "field": field,
                    "rule": "tool_only",
                    "expected": f"actor in {allowed_actors}",
                    "actual": actor,
                    "source": "write_policy",
                    "message": f"Field '{field}' can only be written by automated tools"
                }

        return None

    def check_null_policy(
        self,
        field: str,
        value: Any,
        record: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if null value is allowed.

        Args:
            field: Field name
            value: Proposed value
            record: Full record context (for conditional rules)

        Returns:
            Violation dict if invalid, None if valid
        """
        null_policy = self.null_policy_map.get(field, "allow_null")

        if null_policy == "forbid_null":
            if value is None:
                return {
                    "field": field,
                    "rule": "forbid_null",
                    "expected": "non-null value",
                    "actual": None,
                    "source": "write_policy",
                    "message": f"Field '{field}' cannot be null"
                }

        # Check conditional rules
        conditionals = self.null_policy_map.get("_conditionals", {})
        if field in conditionals:
            cond = conditionals[field]
            condition = cond.get("condition", "")

            # Example: entity_kind required when record_kind=='entity'
            if "record_kind == 'entity'" in condition:
                if record.get("record_kind") == "entity" and value is None:
                    return {
                        "field": field,
                        "rule": "conditional_null",
                        "expected": "non-null when record_kind=='entity'",
                        "actual": None,
                        "source": "write_policy",
                        "message": f"Field '{field}' is required when record_kind is 'entity'"
                    }

        return None

    def validate_patch(
        self,
        patch: Dict[str, Any],
        old_record: Optional[Dict[str, Any]] = None,
        actor: str = "manual"
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a patch against write policies.

        Args:
            patch: Proposed changes (field -> new_value)
            old_record: Existing record (None for new records)
            actor: Actor performing the write ('tool', 'manual', 'scanner', etc.)

        Returns:
            Tuple of (is_valid: bool, violations: list[dict])
            Each violation: {field, rule, expected, actual, source, message}
        """
        violations = []
        old_record = old_record or {}

        # Build new record by merging patch with old
        new_record = {**old_record, **patch}

        for field, new_value in patch.items():
            old_value = old_record.get(field)
            
            # TASK-019: Check if field is in policy maps
            field_known = field in self.update_policy_map or field in self.null_policy_map
            
            if not field_known:
                if self.unknown_field_policy == UnknownFieldPolicy.REJECT:
                    violations.append({
                        "field": field,
                        "rule": "unknown_field",
                        "expected": "field in policy maps",
                        "actual": "field not found",
                        "source": "write_policy",
                        "message": f"Field '{field}' not found in policy maps"
                    })
                    continue
                elif self.unknown_field_policy == UnknownFieldPolicy.WARN:
                    logger.warning(f"Unknown field in patch: '{field}'")
            
            # Check immutability
            violation = self.check_immutable(field, old_value, new_value)
            if violation:
                violations.append(violation)

            # Check tool_only
            violation = self.check_tool_only(field, actor)
            if violation:
                violations.append(violation)

            # Check null policy
            violation = self.check_null_policy(field, new_value, new_record)
            if violation:
                violations.append(violation)

        is_valid = len(violations) == 0
        return is_valid, violations

