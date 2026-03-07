# DOC_LINK: DOC-TEST-ENTITY-CLASSIFIER-015
"""Unit tests for EntityClassifier

Tests entity classification with rules.

DOC_ID: DOC-TEST-ENTITY-CLASSIFIER-015
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.detection.entity_classifier import (
    EntityClassifier,
    Entity,
    EntityType
)
from RUNTIME.doc_id.SUB_DOC_ID.detection.change_detector import (
    Change,
    ChangeType
)


class TestEntityType:
    """Test EntityType enum"""

    def test_entity_types(self):
        """Test entity type enum values"""
        assert EntityType.DOC.value == "DOC"
        assert EntityType.SCHEMA.value == "SCHEMA"
        assert EntityType.TEST.value == "TEST"
        assert EntityType.FILE.value == "FILE"


class TestEntity:
    """Test Entity dataclass"""

    def test_entity_creation(self):
        """Test creating an entity"""
        entity = Entity(
            entity_type=EntityType.DOC,
            path="docs/test.md",
            change_type=ChangeType.FILE_ADDED,
            requires_id=True,
            id_prefix="DOC-"
        )

        assert entity.entity_type == EntityType.DOC
        assert entity.path == "docs/test.md"
        assert entity.requires_id is True

    def test_entity_to_dict(self):
        """Test converting entity to dict"""
        entity = Entity(
            entity_type=EntityType.SCRIPT,
            path="scripts/test.py",
            change_type=ChangeType.FILE_MODIFIED,
            requires_id=True,
            id_prefix="DOC-SCRIPT-",
            metadata={'check': True}
        )

        result = entity.to_dict()

        assert result['entity_type'] == "SCRIPT"
        assert result['path'] == "scripts/test.py"
        assert result['requires_id'] is True
        assert result['metadata']['check'] is True


class TestEntityClassifier:
    """Test EntityClassifier"""

    def _create_rules_file(self, tmpdir: Path) -> Path:
        """Create a test rules file"""
        rules_content = """
entity_types:
  - entity_type: DOC
    patterns:
      - "**/*.md"
    requires_id: true
    id_prefix: "DOC-"
    priority: 1

  - entity_type: TEST
    patterns:
      - "**/test_*.py"
      - "**/*_test.py"
    requires_id: true
    id_prefix: "DOC-TEST-"
    priority: 2

  - entity_type: SCRIPT
    patterns:
      - "**/*.py"
    requires_id: true
    id_prefix: "DOC-SCRIPT-"
    exclude_patterns:
      - "**/test_*.py"
    priority: 3

  - entity_type: FILE
    patterns:
      - "**/*"
    requires_id: false
    id_prefix: "FIL-"
    priority: 100

global_excludes:
  - "**/__pycache__/**"
  - "**/*.pyc"

validation_rules: {}
"""
        rules_file = tmpdir / 'entity_rules.yaml'
        rules_file.write_text(rules_content)
        return rules_file

    def test_initialization(self):
        """Test classifier initialization"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            assert len(classifier.entity_type_rules) == 4

    def test_load_rules_file_not_found(self):
        """Test loading nonexistent rules file raises error"""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                EntityClassifier(rules_file=Path(tmpdir) / 'nonexistent.yaml')

    def test_classify_markdown_as_doc(self):
        """Test classifying markdown file as DOC"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="docs/readme.md")
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].entity_type == EntityType.DOC
            assert entities[0].requires_id is True
            assert entities[0].id_prefix == "DOC-"

    def test_classify_test_file(self):
        """Test classifying test file as TEST (not SCRIPT)"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="tests/test_something.py")
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 1
            # Should match TEST (priority 2) not SCRIPT (priority 3)
            assert entities[0].entity_type == EntityType.TEST
            assert entities[0].id_prefix == "DOC-TEST-"

    def test_classify_python_script(self):
        """Test classifying regular Python file as SCRIPT"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="scripts/process.py")
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].entity_type == EntityType.SCRIPT
            assert entities[0].id_prefix == "DOC-SCRIPT-"

    def test_classify_excluded_file(self):
        """Test that globally excluded files are not classified"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="__pycache__/module.pyc")
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 0

    def test_classify_with_exclude_pattern(self):
        """Test exclude patterns in rules"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            # test_*.py should match TEST, not SCRIPT (due to exclude pattern)
            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="test_example.py")
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].entity_type == EntityType.TEST

    def test_classify_multiple_changes(self):
        """Test classifying multiple changes"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="docs/guide.md"),
                Change(event_type=ChangeType.FILE_ADDED, path="script.py"),
                Change(event_type=ChangeType.FILE_ADDED, path="test_unit.py"),
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 3
            assert entities[0].entity_type == EntityType.DOC
            assert entities[1].entity_type == EntityType.SCRIPT
            assert entities[2].entity_type == EntityType.TEST

    def test_classify_renamed_file(self):
        """Test classifying renamed file preserves old_path"""
        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(
                    event_type=ChangeType.FILE_RENAMED,
                    path="docs/new.md",
                    old_path="docs/old.md"
                )
            ]

            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].path == "docs/new.md"
            assert entities[0].old_path == "docs/old.md"
            assert entities[0].change_type == ChangeType.FILE_RENAMED

    def test_priority_system(self):
        """Test that priority system works (lower number = higher priority)"""
        with TemporaryDirectory() as tmpdir:
            # Create rules where multiple patterns could match
            rules_content = """
entity_types:
  - entity_type: SPECIFIC
    patterns:
      - "**/special/*.py"
    requires_id: true
    id_prefix: "SPEC-"
    priority: 1

  - entity_type: GENERAL
    patterns:
      - "**/*.py"
    requires_id: true
    id_prefix: "GEN-"
    priority: 10

global_excludes: []
validation_rules: {}
"""
            rules_file = Path(tmpdir) / 'rules.yaml'
            rules_file.write_text(rules_content)

            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            changes = [
                Change(event_type=ChangeType.FILE_ADDED, path="special/file.py")
            ]

            entities = classifier.classify(changes)

            # Should match SPECIFIC (priority 1) not GENERAL (priority 10)
            assert len(entities) == 1
            assert entities[0].id_prefix == "SPEC-"

    def test_save_entities(self):
        """Test saving entities to JSON file"""
        import json

        with TemporaryDirectory() as tmpdir:
            rules_file = self._create_rules_file(Path(tmpdir))
            classifier = EntityClassifier(rules_file=rules_file, repo_root=Path(tmpdir))

            entities = [
                Entity(
                    entity_type=EntityType.DOC,
                    path="test.md",
                    change_type=ChangeType.FILE_ADDED,
                    requires_id=True,
                    id_prefix="DOC-"
                )
            ]

            output_file = Path(tmpdir) / 'entities.json'
            classifier.save_entities(entities, output_file)

            assert output_file.exists()

            # Verify content
            with open(output_file, 'r') as f:
                data = json.load(f)

            assert data['total'] == 1
            assert len(data['entities']) == 1
            assert data['entities'][0]['entity_type'] == 'DOC'


__doc_id__ = 'DOC-TEST-ENTITY-CLASSIFIER-015'
