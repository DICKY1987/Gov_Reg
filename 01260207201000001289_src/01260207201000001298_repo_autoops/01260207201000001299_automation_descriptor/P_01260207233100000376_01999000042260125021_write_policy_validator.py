"""
FILE_ID: 01999000042260125021

Facade: delegates to src/registry_writer/write_policy_validator.py
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

_repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_repo_root))

from src.registry_writer.write_policy_validator import WritePolicyValidator as CanonicalValidator


class WritePolicyValidator:
    """Facade: delegates to src/registry_writer/write_policy_validator.py"""

    def __init__(self):
        self._canonical = CanonicalValidator()

    def load_policies(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return self._canonical.load_policies()

    def validate_patch(
        self,
        patch: Dict[str, Any],
        old_record: Optional[Dict[str, Any]] = None,
        actor: str = "manual"
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        return self._canonical.validate_patch(patch, old_record, actor)

    def check_tool_only(self, field: str, actor: str) -> Optional[Dict[str, Any]]:
        return self._canonical.check_tool_only(field, actor)

    def check_immutable(self, field: str, old_value: Any, new_value: Any) -> Optional[Dict[str, Any]]:
        return self._canonical.check_immutable(field, old_value, new_value)
