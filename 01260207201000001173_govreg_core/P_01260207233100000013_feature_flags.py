"""
Feature Flag Infrastructure - Safe Migration Rollout

Enables gradual migration through phases with runtime flags.

Phases:
- Phase 0: Preparation
- Phase 1: Foundation
- Phase 2: Core Components
- Phase 3: Registry Extension
- Phase 4: Legacy Deprecation
- Phase 5: Production Cutover
"""

from enum import Enum
from typing import Dict, Optional
import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MigrationPhase(Enum):
    """Migration phases in sequential order."""

    PHASE_0_PREP = "phase_0_preparation"
    PHASE_1_FOUNDATION = "phase_1_foundation"
    PHASE_2_CORE = "phase_2_core_components"
    PHASE_3_REGISTRY = "phase_3_registry_extension"
    PHASE_4_DEPRECATION = "phase_4_legacy_deprecation"
    PHASE_5_CUTOVER = "phase_5_production_cutover"
    PLANNING_RESERVATIONS = "planning_reservations"


class FeatureFlags:
    """
    Feature flag manager for migration phases.

    Loads flags from config file and provides runtime evaluation.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize feature flags.

        Args:
            config_path: Path to feature_flags.json (default: .state/feature_flags.json)
        """
        if config_path is None:
            config_path = ".state/feature_flags.json"

        self.config_path = Path(config_path)
        self.flags = self._load_flags()

    def _load_flags(self) -> Dict:
        """Load flags from config file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    flags = json.load(f)
                    logger.info(f"Loaded feature flags from {self.config_path}")
                    return flags
            except Exception as e:
                logger.warning(f"Failed to load flags from {self.config_path}: {e}")
                return self._default_flags()
        else:
            logger.info(f"No config file found, using defaults")
            return self._default_flags()

    def _default_flags(self) -> Dict:
        """Default feature flags (all disabled)."""
        return {
            "migration_phase": "phase_0_preparation",
            "enable_content_hash": False,
            "enable_conflict_validator": False,
            "enable_drift_detection": False,
            "enable_v3_registry_writer": False,
            "legacy_writer_enabled": True,
            "enable_planning_reservations": False,
        }

    def is_phase_active(self, phase: MigrationPhase) -> bool:
        """
        Check if given phase is active.

        Args:
            phase: Phase to check

        Returns:
            True if current phase >= given phase
        """
        current_phase = self.flags.get("migration_phase")
        phases_order = [p.value for p in MigrationPhase]

        try:
            current_idx = phases_order.index(current_phase)
            target_idx = phases_order.index(phase.value)
            return current_idx >= target_idx
        except ValueError:
            logger.error(f"Invalid phase: {current_phase}")
            return False

    def get_flag(self, flag_name: str) -> bool:
        """
        Get boolean flag value.

        Args:
            flag_name: Name of flag

        Returns:
            Flag value (False if not found)
        """
        return self.flags.get(flag_name, False)

    def set_phase(self, phase: MigrationPhase) -> None:
        """
        Set current migration phase.

        Args:
            phase: Phase to activate
        """
        self.flags["migration_phase"] = phase.value
        self._save_flags()
        logger.info(f"Migration phase set to: {phase.value}")

    def set_flag(self, flag_name: str, value: bool) -> None:
        """
        Set boolean flag value.

        Args:
            flag_name: Name of flag
            value: New value
        """
        self.flags[flag_name] = value
        self._save_flags()
        logger.info(f"Flag {flag_name} set to: {value}")

    def _save_flags(self) -> None:
        """Save flags to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(self.flags, f, indent=2)

    def get_all_flags(self) -> Dict:
        """Get all flags as dict."""
        return self.flags.copy()


# Global instance (singleton pattern)
_global_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance."""
    global _global_flags
    if _global_flags is None:
        _global_flags = FeatureFlags()
    return _global_flags
