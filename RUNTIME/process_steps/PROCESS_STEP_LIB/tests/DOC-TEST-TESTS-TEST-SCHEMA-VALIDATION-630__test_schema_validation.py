#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TESTS-TEST-SCHEMA-VALIDATION-630
"""
Test Suite for Schema Validation

Tests schema validation, merging, and consistency checks.
DOC_ID: DOC-TEST-TESTS-TEST-SCHEMA-VALIDATION-630
"""

import unittest
import sys
import yaml
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSchemaStructure(unittest.TestCase):
    """Test schema file structure and format"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.base_dir = Path(__file__).parent.parent
        cls.schemas_dir = cls.base_dir / 'schemas'

    def test_source_schemas_valid_yaml(self):
        """Test that all source schemas are valid YAML"""
        source_dir = self.schemas_dir / 'source'
        schemas = list(source_dir.glob('PFA_*.yaml'))

        self.assertGreater(len(schemas), 0, "Should have source schemas")

        for schema_file in schemas:
            with self.subTest(schema=schema_file.name):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    try:
                        data = yaml.safe_load(f)
                        self.assertIsNotNone(data, f"{schema_file.name} should parse")
                    except yaml.YAMLError as e:
                        self.fail(f"{schema_file.name} has YAML errors: {e}")

    def test_unified_schema_valid_yaml(self):
        """Test that unified schema is valid YAML"""
        unified = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        self.assertTrue(unified.exists(), "Unified schema should exist")

        with open(unified, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)
            except yaml.YAMLError as e:
                self.fail(f"Unified schema has YAML errors: {e}")

    def test_unified_schema_has_meta(self):
        """Test that unified schema has meta section"""
        unified = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        with open(unified, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.assertIn('meta', data, "Should have meta section")
        self.assertIn('schema_id', data['meta'])
        self.assertIn('version', data['meta'])

    def test_unified_schema_has_steps(self):
        """Test that unified schema has steps"""
        unified = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        with open(unified, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        self.assertIn('steps', data, "Should have steps section")
        self.assertIsInstance(data['steps'], list)
        self.assertGreater(len(data['steps']), 0, "Should have steps")

    def test_step_has_required_fields(self):
        """Test that steps have required fields"""
        unified = self.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        with open(unified, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        required_fields = ['step_id', 'name']

        for step in data['steps'][:10]:  # Check first 10 steps
            with self.subTest(step_id=step.get('step_id', 'unknown')):
                for field in required_fields:
                    self.assertIn(field, step, f"Step should have {field}")


class TestSchemaConsistency(unittest.TestCase):
    """Test schema consistency and relationships"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.base_dir = Path(__file__).parent.parent
        cls.schemas_dir = cls.base_dir / 'schemas'

        # Load unified schema
        unified_path = cls.schemas_dir / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        with open(unified_path, 'r', encoding='utf-8') as f:
            cls.unified_data = yaml.safe_load(f)

    def test_step_ids_unique(self):
        """Test that all step IDs are unique"""
        step_ids = [step['step_id'] for step in self.unified_data['steps']]

        self.assertEqual(len(step_ids), len(set(step_ids)),
                        "All step IDs should be unique")

    def test_step_count_matches_meta(self):
        """Test that step count matches metadata"""
        actual_count = len(self.unified_data['steps'])
        meta_count = self.unified_data['meta']['merge_statistics']['unique_steps_after_dedup']

        self.assertEqual(actual_count, meta_count,
                        f"Step count ({actual_count}) should match meta ({meta_count})")

    def test_phases_defined(self):
        """Test that universal phases are defined"""
        self.assertIn('universal_phases', self.unified_data)
        phases = self.unified_data['universal_phases']

        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0, "Should have phases defined")

    def test_operation_kinds_defined(self):
        """Test that operation kinds are defined"""
        self.assertIn('unified_operation_kinds', self.unified_data)
        operations = self.unified_data['unified_operation_kinds']

        self.assertIsInstance(operations, list)
        self.assertGreater(len(operations), 0, "Should have operation kinds")


class TestConfigurationFiles(unittest.TestCase):
    """Test configuration file validity"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.base_dir = Path(__file__).parent.parent
        cls.config_dir = cls.base_dir / 'config'

    def test_phase_mappings_valid(self):
        """Test phase_mappings.yaml is valid"""
        config_file = self.config_dir / 'phase_mappings.yaml'

        self.assertTrue(config_file.exists(), "phase_mappings.yaml should exist")

        with open(config_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)
            except yaml.YAMLError as e:
                self.fail(f"phase_mappings.yaml has errors: {e}")

    def test_operation_taxonomy_valid(self):
        """Test operation_taxonomy.yaml is valid"""
        config_file = self.config_dir / 'operation_taxonomy.yaml'

        self.assertTrue(config_file.exists(), "operation_taxonomy.yaml should exist")

        with open(config_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)
            except yaml.YAMLError as e:
                self.fail(f"operation_taxonomy.yaml has errors: {e}")

    def test_pipeline_config_valid(self):
        """Test pipeline_config.yaml is valid"""
        config_file = self.config_dir / 'pipeline_config.yaml'

        self.assertTrue(config_file.exists(), "pipeline_config.yaml should exist")

        with open(config_file, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)
                self.assertIn('version', data)
                self.assertIn('source_schemas', data)
                self.assertIn('outputs', data)
            except yaml.YAMLError as e:
                self.fail(f"pipeline_config.yaml has errors: {e}")


if __name__ == '__main__':
    unittest.main()
