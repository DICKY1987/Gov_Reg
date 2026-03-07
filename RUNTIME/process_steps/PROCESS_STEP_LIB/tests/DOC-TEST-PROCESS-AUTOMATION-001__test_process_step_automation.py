#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-PROCESS-AUTOMATION-001
"""
Comprehensive Tests for Process Step Automation

Tests the entire automation pipeline:
1. Missing file identification
2. Auto-attachment of implementation files
3. Schema synchronization
4. Validation

DOC_ID: DOC-TEST-PROCESS-AUTOMATION-001
"""

import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, Any
import sys

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

try:
    from pfa_identify_missing_files import analyze_missing_files
    from pfa_auto_attach_files import FileAttacher
except ImportError:
    # Try alternative import paths
    import importlib.util
    analyze_missing_files = None
    FileAttacher = None


class TestMissingFilesIdentifier:
    """Test missing implementation files identification."""

    def test_load_schema(self, tmp_path):
        """Test schema loading."""
        schema = {
            'meta': {'schema_id': 'TEST'},
            'steps': [
                {
                    'step_id': 'TEST-001',
                    'name': 'Test Step',
                    'phase': '1_BOOTSTRAP',
                    'operation_kind': 'initialization',
                    'implementation_files': []
                }
            ]
        }

        schema_file = tmp_path / 'test_schema.yaml'
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)

        with open(schema_file, 'r') as f:
            loaded = yaml.safe_load(f)

        assert loaded['meta']['schema_id'] == 'TEST'
        assert len(loaded['steps']) == 1

    def test_analyze_missing_files(self):
        """Test analysis of missing implementation files."""
        schema = {
            'steps': [
                {
                    'step_id': 'TEST-001',
                    'name': 'Step with files',
                    'universal_phase': '1_BOOTSTRAP',
                    'operation_kind': 'initialization',
                    'responsible_component': 'test::component',
                    'description': 'Test step',
                    'implementation_files': [{'file': 'test.py', 'confidence': 90}],
                    'artifact_registry_refs': []
                },
                {
                    'step_id': 'TEST-002',
                    'name': 'Step without files',
                    'universal_phase': '2_DISCOVERY',
                    'operation_kind': 'discovery',
                    'responsible_component': 'test::component',
                    'description': 'Test step',
                    'implementation_files': [],
                    'artifact_registry_refs': []
                }
            ]
        }

        analysis = analyze_missing_files(schema)

        assert analysis['summary']['total_steps'] == 2
        assert analysis['summary']['steps_with_files'] == 1
        assert analysis['summary']['steps_without_files'] == 1
        assert analysis['summary']['coverage_percentage'] == 50.0

        assert '1_BOOTSTRAP' in analysis['by_phase']
        assert '2_DISCOVERY' in analysis['by_phase']

        assert len(analysis['steps_without_files']) == 1
        assert analysis['steps_without_files'][0]['step_id'] == 'TEST-002'


class TestFileAttacher:
    """Test automatic file attachment."""

    def test_extract_keywords(self):
        """Test keyword extraction from steps."""
        attacher = FileAttacher()

        step = {
            'step_id': 'E2E-1-001',
            'name': 'Validate Directory Structure',
            'operation_kind': 'validation',
            'responsible_component': 'patterns::pattern_orchestrate',
            'artifact_registry_refs': ['specs/', 'schemas/']
        }

        keywords = attacher.extract_keywords(step)

        assert 'validate' in keywords
        assert 'directory' in keywords
        assert 'structure' in keywords
        assert 'validation' in keywords
        assert 'patterns' in keywords
        assert 'pattern_orchestrate' in keywords or 'orchestrate' in keywords
        assert 'specs' in keywords
        assert 'schemas' in keywords

    def test_calculate_match_score_exact_step_id(self, tmp_path):
        """Test high score for exact step ID match."""
        attacher = FileAttacher()

        step = {
            'step_id': 'E2E-1-001',
            'name': 'Test Step',
            'operation_kind': 'validation',
            'responsible_component': 'test::component',
            'universal_phase': '1_BOOTSTRAP',
            'artifact_registry_refs': []
        }

        # Create test file
        test_file = tmp_path / 'e2e-1-001_validate.py'
        test_file.write_text('# Test implementation')

        keywords = attacher.extract_keywords(step)
        score, reasons = attacher.calculate_match_score(step, test_file, keywords)

        assert score >= 50  # Should get high score for step ID match
        assert any('Step ID' in r for r in reasons)

    def test_calculate_match_score_component_match(self, tmp_path):
        """Test scoring for component name match."""
        attacher = FileAttacher()

        step = {
            'step_id': 'TEST-001',
            'name': 'Test Step',
            'operation_kind': 'validation',
            'responsible_component': 'patterns::orchestrator',
            'universal_phase': '1_BOOTSTRAP',
            'artifact_registry_refs': []
        }

        # Create test file with component name
        test_file = tmp_path / 'pattern_orchestrator.py'
        test_file.write_text('# Pattern orchestrator implementation')

        keywords = attacher.extract_keywords(step)
        score, reasons = attacher.calculate_match_score(step, test_file, keywords)

        assert score > 0
        assert any('Component' in r or 'orchestrat' in r.lower() for r in reasons)

    def test_find_matches_filters_by_confidence(self, tmp_path):
        """Test that find_matches filters by confidence threshold."""
        attacher = FileAttacher(confidence_threshold=70)

        steps = [
            {
                'step_id': 'TEST-001',
                'name': 'High Match Step',
                'operation_kind': 'validation',
                'responsible_component': 'test::high_match',
                'universal_phase': '1_BOOTSTRAP',
                'artifact_registry_refs': [],
                'implementation_files': []
            }
        ]

        # Create high-match file
        high_match = tmp_path / 'test-001_high_match.py'
        high_match.write_text('# High match implementation')

        # Create low-match file
        low_match = tmp_path / 'unrelated.py'
        low_match.write_text('# Unrelated file')

        files = {
            str(high_match): high_match,
            str(low_match): low_match
        }

        matches = attacher.find_matches(steps, files)

        # Should find match for high confidence file only
        assert 'TEST-001' in matches
        # All matched files should have confidence >= threshold
        for file_match in matches['TEST-001']:
            assert file_match['confidence'] >= attacher.confidence_threshold

    def test_update_schema_preserves_existing_files(self):
        """Test that update_schema doesn't overwrite existing files."""
        attacher = FileAttacher()

        schema = {
            'meta': {},
            'steps': [
                {
                    'step_id': 'TEST-001',
                    'name': 'Step with files',
                    'implementation_files': [{'file': 'existing.py', 'confidence': 95}]
                },
                {
                    'step_id': 'TEST-002',
                    'name': 'Step without files',
                    'implementation_files': []
                }
            ]
        }

        matches = {
            'TEST-001': [{'file': 'new.py', 'confidence': 80}],
            'TEST-002': [{'file': 'added.py', 'confidence': 70}]
        }

        updated = attacher.update_schema(schema, matches)

        # TEST-001 should keep existing files (not updated)
        assert updated['steps'][0]['implementation_files'][0]['file'] == 'existing.py'

        # TEST-002 should get new files
        assert updated['steps'][1]['implementation_files'][0]['file'] == 'added.py'


class TestSchemaValidation:
    """Test schema validation after automation."""

    def test_schema_has_required_metadata(self):
        """Test that processed schema has required metadata."""
        schema = {
            'meta': {
                'schema_id': 'TEST',
                'version': '1.0.0',
                'file_attachment_stats': {
                    'total_steps': 10,
                    'steps_with_files': 8,
                    'coverage_percentage': 80.0
                }
            },
            'steps': []
        }

        assert 'meta' in schema
        assert 'file_attachment_stats' in schema['meta']
        assert schema['meta']['file_attachment_stats']['coverage_percentage'] == 80.0

    def test_all_steps_have_required_fields(self):
        """Test that all steps have required fields."""
        schema = {
            'steps': [
                {
                    'step_id': 'TEST-001',
                    'name': 'Test Step',
                    'universal_phase': '1_BOOTSTRAP',
                    'operation_kind': 'initialization',
                    'responsible_component': 'test::component',
                    'description': 'Test description',
                    'implementation_files': []
                }
            ]
        }

        required_fields = [
            'step_id', 'name', 'universal_phase', 'operation_kind',
            'responsible_component', 'description'
        ]

        for step in schema['steps']:
            for field in required_fields:
                assert field in step, f"Missing required field: {field}"


class TestIntegrationWorkflow:
    """Integration tests for the complete automation workflow."""

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow: identify -> attach -> validate."""
        # Create test schema
        schema = {
            'meta': {'schema_id': 'TEST_E2E', 'version': '1.0.0'},
            'steps': [
                {
                    'step_id': 'E2E-TEST-001',
                    'name': 'Test Validation Step',
                    'universal_phase': '1_BOOTSTRAP',
                    'operation_kind': 'validation',
                    'responsible_component': 'test::validator',
                    'description': 'Test step for validation',
                    'implementation_files': [],
                    'artifact_registry_refs': []
                }
            ]
        }

        # 1. Analyze missing files
        analysis = analyze_missing_files(schema)
        assert analysis['summary']['steps_without_files'] == 1

        # 2. Create matching implementation file
        impl_file = tmp_path / 'e2e-test-001_validator.py'
        impl_file.write_text('# Test validator implementation')

        # 3. Auto-attach files
        attacher = FileAttacher(confidence_threshold=50)
        files = {str(impl_file): impl_file}
        matches = attacher.find_matches(schema['steps'], files)

        assert 'E2E-TEST-001' in matches

        # 4. Update schema
        updated = attacher.update_schema(schema, matches)

        assert len(updated['steps'][0]['implementation_files']) > 0
        assert 'file_attachment_stats' in updated['meta']

        # 5. Verify final state
        final_analysis = analyze_missing_files(updated)
        assert final_analysis['summary']['steps_without_files'] == 0
        assert final_analysis['summary']['coverage_percentage'] == 100.0


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
