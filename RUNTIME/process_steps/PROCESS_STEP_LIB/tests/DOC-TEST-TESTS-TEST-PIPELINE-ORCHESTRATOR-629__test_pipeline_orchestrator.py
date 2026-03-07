#!/usr/bin/env python3
# DOC_LINK: DOC-TEST-TESTS-TEST-PIPELINE-ORCHESTRATOR-629
"""
Test Suite for Pipeline Orchestrator

Tests the pfa_run_pipeline.py orchestrator functionality including:
- Pipeline execution
- Incremental updates
- Dry-run mode
- Validation
- Error handling
DOC_ID: DOC-TEST-TESTS-TEST-PIPELINE-ORCHESTRATOR-629
"""

import unittest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

try:
    from pfa_run_pipeline import PipelineOrchestrator
except ImportError:
    import pytest
    pytest.skip("pfa_run_pipeline module not found", allow_module_level=True)


class TestPipelineOrchestrator(unittest.TestCase):
    """Test cases for Pipeline Orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())

        # Create required subdirectories
        (self.test_dir / 'schemas' / 'source').mkdir(parents=True)
        (self.test_dir / 'schemas' / 'unified').mkdir(parents=True)
        (self.test_dir / 'indices').mkdir(parents=True)
        (self.test_dir / 'guides').mkdir(parents=True)
        (self.test_dir / 'tools').mkdir(parents=True)

        # Create test source files
        for i in range(1, 6):
            schema_file = self.test_dir / 'schemas' / 'source' / f'test_schema_{i}.yaml'
            schema_file.write_text(f'# Test schema {i}\nversion: 1.0.0\n')

        # Create orchestrator
        self.orchestrator = PipelineOrchestrator(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init(self):
        """Test orchestrator initialization"""
        self.assertEqual(self.orchestrator.base_dir, self.test_dir)
        self.assertTrue(self.orchestrator.schemas_dir.exists())
        self.assertTrue(self.orchestrator.indices_dir.exists())
        self.assertTrue(self.orchestrator.guides_dir.exists())

    def test_check_if_rebuild_needed_no_unified(self):
        """Test rebuild detection when unified schema doesn't exist"""
        needs_rebuild, reason = self.orchestrator.check_if_rebuild_needed()

        self.assertTrue(needs_rebuild)
        self.assertIn("doesn't exist", reason)

    def test_check_if_rebuild_needed_source_newer(self):
        """Test rebuild detection when source is newer"""
        # Create unified schema
        unified = self.test_dir / 'schemas' / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        unified.write_text('# Unified\n')

        # Wait a moment then update source
        time.sleep(0.1)
        source = self.test_dir / 'schemas' / 'source' / 'test_schema_1.yaml'
        source.write_text('# Updated\n')

        needs_rebuild, reason = self.orchestrator.check_if_rebuild_needed()

        self.assertTrue(needs_rebuild)
        self.assertIn('was modified', reason)

    def test_check_if_rebuild_needed_up_to_date(self):
        """Test rebuild detection when everything is up-to-date"""
        # Create unified schema newer than sources
        unified = self.test_dir / 'schemas' / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'
        time.sleep(0.1)  # Ensure newer timestamp
        unified.write_text('# Unified\n')

        needs_rebuild, reason = self.orchestrator.check_if_rebuild_needed()

        self.assertFalse(needs_rebuild)
        self.assertIn('up-to-date', reason)

    def test_validate_sources(self):
        """Test source schema validation"""
        result = self.orchestrator.validate_sources(dry_run=False)
        self.assertTrue(result)

    def test_validate_sources_empty_file(self):
        """Test validation fails with empty source file"""
        # Create empty file
        empty = self.test_dir / 'schemas' / 'source' / 'PFA_EMPTY.yaml'
        empty.write_text('')

        result = self.orchestrator.validate_sources(dry_run=False)
        self.assertFalse(result)

    def test_run_tool_dry_run(self):
        """Test run_tool in dry-run mode"""
        result = self.orchestrator.run_tool(
            'test_script.py',
            ['--arg1', 'value1'],
            'Test description',
            dry_run=True
        )

        self.assertTrue(result)  # Dry-run always returns True

    @patch('tools.pfa_run_pipeline.subprocess.run')
    def test_run_tool_success(self, mock_run):
        """Test run_tool with successful execution"""
        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '✅ Success\n'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        # Create dummy script
        script = self.test_dir / 'tools' / 'test_script.py'
        script.write_text('print("test")')

        result = self.orchestrator.run_tool(
            'test_script.py',
            [],
            'Test',
            dry_run=False
        )

        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch('tools.pfa_run_pipeline.subprocess.run')
    def test_run_tool_failure(self, mock_run):
        """Test run_tool with failed execution"""
        # Mock failed subprocess
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Error occurred'
        mock_run.return_value = mock_result

        # Create dummy script
        script = self.test_dir / 'tools' / 'test_script.py'
        script.write_text('import sys; sys.exit(1)')

        result = self.orchestrator.run_tool(
            'test_script.py',
            [],
            'Test',
            dry_run=False
        )

        self.assertFalse(result)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for full pipeline execution"""

    @classmethod
    def setUpClass(cls):
        """Set up for integration tests"""
        cls.base_dir = Path(__file__).parent.parent
        cls.orchestrator = PipelineOrchestrator(cls.base_dir)

    def test_pipeline_files_exist(self):
        """Test that all required pipeline files exist"""
        tools = [
            'pfa_merge_schemas.py',
            'pfa_build_master_index.py',
            'pfa_validate_e2e_pipeline.py',
            'generate_explained_steps.py'
        ]

        for tool in tools:
            tool_path = self.base_dir / 'tools' / tool
            self.assertTrue(tool_path.exists(), f"{tool} should exist")

    def test_source_schemas_exist(self):
        """Test that source schemas exist"""
        source_dir = self.base_dir / 'schemas' / 'source'

        self.assertTrue(source_dir.exists(), "Source schema directory should exist")

        schemas = list(source_dir.glob('PFA_*.yaml'))
        self.assertGreaterEqual(len(schemas), 5, "Should have at least 5 source schemas")

    def test_config_files_exist(self):
        """Test that configuration files exist"""
        configs = [
            'config/phase_mappings.yaml',
            'config/operation_taxonomy.yaml',
            'config/pipeline_config.yaml'
        ]

        for config in configs:
            config_path = self.base_dir / config
            self.assertTrue(config_path.exists(), f"{config} should exist")

    def test_unified_schema_exists(self):
        """Test that unified schema exists"""
        unified = self.base_dir / 'schemas' / 'unified' / 'PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml'

        self.assertTrue(unified.exists(), "Unified schema should exist")
        self.assertGreater(unified.stat().st_size, 0, "Unified schema should not be empty")

    def test_master_index_exists(self):
        """Test that master index exists"""
        index = self.base_dir / 'indices' / 'master_index.json'

        self.assertTrue(index.exists(), "Master index should exist")
        self.assertGreater(index.stat().st_size, 0, "Master index should not be empty")


if __name__ == '__main__':
    unittest.main()
