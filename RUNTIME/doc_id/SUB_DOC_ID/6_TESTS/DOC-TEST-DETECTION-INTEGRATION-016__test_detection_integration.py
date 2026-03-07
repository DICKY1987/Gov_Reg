# DOC_LINK: DOC-TEST-DETECTION-INTEGRATION-016
"""Integration tests for Detection Pipeline

Tests end-to-end detection: changes → entities.

DOC_ID: DOC-TEST-DETECTION-INTEGRATION-016
"""

import pytest
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from RUNTIME.doc_id.SUB_DOC_ID.detection.change_detector import ChangeDetector, ChangeType
from RUNTIME.doc_id.SUB_DOC_ID.detection.entity_classifier import EntityClassifier, EntityType


class TestDetectionPipeline:
    """Integration tests for detection pipeline"""

    def _setup_git_repo(self, repo_root: Path):
        """Initialize git repository"""
        subprocess.run(['git', 'init'], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_root, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_root, check=True)

    def _create_rules_file(self, tmpdir: Path) -> Path:
        """Create entity rules file"""
        rules_content = """
entity_types:
  - entity_type: DOC
    patterns: ["**/*.md"]
    requires_id: true
    id_prefix: "DOC-"
    priority: 1
  - entity_type: SCRIPT
    patterns: ["**/*.py"]
    requires_id: true
    id_prefix: "DOC-SCRIPT-"
    priority: 2
  - entity_type: FILE
    patterns: ["**/*"]
    requires_id: false
    id_prefix: "FIL-"
    priority: 100
global_excludes: ["**/__pycache__/**"]
validation_rules: {}
"""
        rules_file = tmpdir / 'entity_rules.yaml'
        rules_file.write_text(rules_content)
        return rules_file

    def test_detect_and_classify_added_files(self):
        """Test complete pipeline: detect added files and classify"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # Create files
            (repo_root / 'readme.md').write_text('# Readme')
            (repo_root / 'script.py').write_text('print("hello")')

            # Stage files
            subprocess.run(['git', 'add', '.'], cwd=repo_root, check=True)

            # Detect changes
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert len(changes) == 2

            # Classify entities
            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            assert len(entities) == 2

            # Verify classifications
            doc_entity = next(e for e in entities if e.entity_type == EntityType.DOC)
            assert doc_entity.path == 'readme.md'
            assert doc_entity.requires_id is True

            script_entity = next(e for e in entities if e.entity_type == EntityType.SCRIPT)
            assert script_entity.path == 'script.py'
            assert script_entity.requires_id is True

    def test_detect_and_classify_modified_files(self):
        """Test pipeline with modified files"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # Create initial commit
            test_file = repo_root / 'doc.md'
            test_file.write_text('original')
            subprocess.run(['git', 'add', 'doc.md'], cwd=repo_root, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_root, check=True)

            # Modify file
            test_file.write_text('modified')
            subprocess.run(['git', 'add', 'doc.md'], cwd=repo_root, check=True)

            # Detect and classify
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].change_type == ChangeType.FILE_MODIFIED
            assert entities[0].entity_type == EntityType.DOC

    def test_detect_and_classify_deleted_files(self):
        """Test pipeline with deleted files"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # Create initial commit
            test_file = repo_root / 'old.py'
            test_file.write_text('code')
            subprocess.run(['git', 'add', 'old.py'], cwd=repo_root, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_root, check=True)

            # Delete file
            test_file.unlink()
            subprocess.run(['git', 'add', 'old.py'], cwd=repo_root, check=True)

            # Detect and classify
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            assert len(entities) == 1
            assert entities[0].change_type == ChangeType.FILE_DELETED
            assert entities[0].path == 'old.py'

    def test_pipeline_excludes_pycache(self):
        """Test that pipeline excludes __pycache__ files"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # Create files including pycache
            (repo_root / 'script.py').write_text('code')
            pycache_dir = repo_root / '__pycache__'
            pycache_dir.mkdir()
            (pycache_dir / 'module.pyc').write_text('bytecode')

            subprocess.run(['git', 'add', '.'], cwd=repo_root, check=True)

            # Detect and classify
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            # Should only have script.py, not pycache file
            assert len(entities) == 1
            assert entities[0].path == 'script.py'

    def test_pipeline_persists_outputs(self):
        """Test that pipeline can persist changes and entities"""
        import json

        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # Create and stage file
            (repo_root / 'test.md').write_text('content')
            subprocess.run(['git', 'add', 'test.md'], cwd=repo_root, check=True)

            # Detect
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            # Save changes
            changes_file = repo_root / 'changes.json'
            detector.save_changes(changes, changes_file)

            assert changes_file.exists()

            # Classify
            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            # Save entities
            entities_file = repo_root / 'entities.json'
            classifier.save_entities(entities, entities_file)

            assert entities_file.exists()

            # Verify both files have correct structure
            with open(changes_file, 'r') as f:
                changes_data = json.load(f)
            assert 'changes' in changes_data
            assert 'total' in changes_data

            with open(entities_file, 'r') as f:
                entities_data = json.load(f)
            assert 'entities' in entities_data
            assert 'total' in entities_data

    def test_pipeline_empty_changes(self):
        """Test pipeline handles no changes gracefully"""
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._setup_git_repo(repo_root)

            # No staged changes
            detector = ChangeDetector(repo_root=repo_root)
            changes = detector.detect(mode='staged')

            assert changes == []

            # Classify empty changes
            rules_file = self._create_rules_file(repo_root)
            classifier = EntityClassifier(rules_file=rules_file, repo_root=repo_root)
            entities = classifier.classify(changes)

            assert entities == []


__doc_id__ = 'DOC-TEST-DETECTION-INTEGRATION-016'
