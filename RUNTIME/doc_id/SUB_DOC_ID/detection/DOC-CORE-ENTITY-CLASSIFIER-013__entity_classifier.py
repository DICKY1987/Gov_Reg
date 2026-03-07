# DOC_LINK: DOC-CORE-ENTITY-CLASSIFIER-013
"""Entity Classifier for ID System

Classifies file changes into entity types based on rules.
Implements Section 3.2 Flow 2 from DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638.

DOC_ID: DOC-CORE-ENTITY-CLASSIFIER-013
"""

import fnmatch
import re
import yaml
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from .change_detector import Change, ChangeType


class EntityType(Enum):
    """Entity types"""
    DOC = "DOC"
    SCHEMA = "SCHEMA"
    CONTRACT = "CONTRACT"
    CONFIG = "CONFIG"
    SCRIPT = "SCRIPT"
    TEST = "TEST"
    CORE = "CORE"
    WORKFLOW = "WORKFLOW"
    HOOK = "HOOK"
    PHASE = "PHASE"
    FILE = "FILE"


@dataclass
class Entity:
    """Represents a classified entity"""
    entity_type: EntityType
    path: str
    change_type: ChangeType
    requires_id: bool
    id_prefix: str
    old_path: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'entity_type': self.entity_type.value,
            'path': self.path,
            'change_type': self.change_type.value,
            'requires_id': self.requires_id,
            'id_prefix': self.id_prefix,
            'old_path': self.old_path,
            'metadata': self.metadata or {}
        }


class EntityClassifier:
    """Classifies file changes into entity types

    Loads classification rules from entity_rules.yaml.
    Applies pattern matching and priority-based selection.

    Deterministic: Same changes + same rules → same entities
    """

    def __init__(self, rules_file: Optional[Path] = None, repo_root: Optional[Path] = None):
        """Initialize entity classifier

        Args:
            rules_file: Path to entity_rules.yaml (defaults to config/entity_rules.yaml)
            repo_root: Repository root directory
        """
        self.repo_root = repo_root or Path.cwd()

        if rules_file is None:
            rules_file = self.repo_root / 'RUNTIME' / 'doc_id' / 'SUB_DOC_ID' / 'config' / 'entity_rules.yaml'

        self.rules = self._load_rules(rules_file)
        self.entity_type_rules = self.rules.get('entity_types', [])
        self.validation_rules = self.rules.get('validation_rules', {})
        self.global_excludes = self.rules.get('global_excludes', [])

    def _load_rules(self, rules_file: Path) -> dict:
        """Load classification rules from YAML file

        Args:
            rules_file: Path to rules file

        Returns:
            Rules dictionary
        """
        if not rules_file.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_file}")

        with open(rules_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def classify(self, changes: List[Change]) -> List[Entity]:
        """Classify changes into entities

        Args:
            changes: List of detected changes

        Returns:
            List of classified entities
        """
        entities = []

        for change in changes:
            # Check global exclusions
            if self._is_excluded(change.path):
                continue

            # Classify the change
            entity = self._classify_single(change)

            if entity:
                entities.append(entity)

        return entities

    def _classify_single(self, change: Change) -> Optional[Entity]:
        """Classify a single change

        Args:
            change: Change to classify

        Returns:
            Entity or None if excluded
        """
        # Find matching entity types (sorted by priority)
        matches = []

        for rule in self.entity_type_rules:
            if self._matches_rule(change.path, rule):
                matches.append(rule)

        if not matches:
            return None

        # Sort by priority (lower number = higher priority)
        matches.sort(key=lambda r: r.get('priority', 999))

        # Use highest priority match
        best_match = matches[0]

        # Additional validation checks
        metadata = {}
        if 'additional_checks' in best_match:
            for check_name in best_match['additional_checks']:
                check_result = self._run_validation_check(change.path, check_name)
                metadata[check_name] = check_result

        # Create entity
        entity_type_str = best_match['entity_type']

        try:
            entity_type = EntityType[entity_type_str]
        except KeyError:
            entity_type = EntityType.FILE

        return Entity(
            entity_type=entity_type,
            path=change.path,
            change_type=change.event_type,
            requires_id=best_match.get('requires_id', False),
            id_prefix=best_match.get('id_prefix', 'FIL-'),
            old_path=change.old_path,
            metadata=metadata
        )

    def _matches_rule(self, filepath: str, rule: dict) -> bool:
        """Check if filepath matches rule patterns

        Args:
            filepath: File path to check
            rule: Rule dictionary

        Returns:
            True if matches
        """
        patterns = rule.get('patterns', [])
        exclude_patterns = rule.get('exclude_patterns', [])

        # Check exclusions first
        for exclude_pattern in exclude_patterns:
            if fnmatch.fnmatch(filepath, exclude_pattern):
                return False

        # Check includes
        for pattern in patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True

        return False

    def _is_excluded(self, filepath: str) -> bool:
        """Check if filepath is globally excluded

        Args:
            filepath: File path to check

        Returns:
            True if excluded
        """
        for pattern in self.global_excludes:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False

    def _run_validation_check(self, filepath: str, check_name: str) -> bool:
        """Run validation check on file

        Args:
            filepath: File path to check
            check_name: Name of validation check

        Returns:
            True if check passes
        """
        if check_name not in self.validation_rules:
            return False

        check = self.validation_rules[check_name]
        pattern = check.get('pattern')

        if not pattern:
            return False

        # Read file content
        full_path = self.repo_root / filepath

        if not full_path.exists():
            return False

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check pattern
            return bool(re.search(pattern, content, re.MULTILINE))
        except Exception:
            return False

    def save_entities(self, entities: List[Entity], output_file: Path):
        """Save entities to JSON file

        Args:
            entities: List of entities
            output_file: Output file path
        """
        import json
        from datetime import datetime, timezone

        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'entities': [e.to_dict() for e in entities],
            'total': len(entities),
            'classified_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


__doc_id__ = 'DOC-CORE-ENTITY-CLASSIFIER-013'
