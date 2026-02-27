#!/usr/bin/env python3
"""
Integration Test Suite for Last Mile Orchestration

Tests script resolution, orchestrator functionality, and end-to-end pipeline.
"""
import pytest
import json
import sys
from pathlib import Path

# Add mapp_py to path
repo_root = Path(__file__).parents[1]
mapp_py_dir = repo_root / "01260207201000001250_REGISTRY" / "01260207201000001313_capability_mapping_system" / "01260207220000001318_mapp_py"
sys.path.insert(0, str(mapp_py_dir))

try:
    from script_name_resolver import (
        resolve_script_path,
        get_logical_name,
        list_all_scripts,
        validate_all_scripts,
        get_missing_scripts
    )
except ImportError:
    # Fallback if path resolution fails
    import importlib.util
    spec = importlib.util.spec_from_file_location("script_name_resolver", mapp_py_dir / "script_name_resolver.py")
    script_name_resolver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script_name_resolver)
    resolve_script_path = script_name_resolver.resolve_script_path
    get_logical_name = script_name_resolver.get_logical_name
    list_all_scripts = script_name_resolver.list_all_scripts
    validate_all_scripts = script_name_resolver.validate_all_scripts
    get_missing_scripts = script_name_resolver.get_missing_scripts


class TestScriptNameResolution:
    """Test script name resolution functionality."""
    
    def test_resolve_existing_script(self):
        """Verify existing scripts resolve correctly."""
        resolved = resolve_script_path('text_normalizer.py', mapp_py_dir)
        assert resolved.exists()
        assert resolved.name == 'P_01260202173939000060_text_normalizer.py'
    
    def test_resolve_all_phase_a_scripts(self):
        """Verify all Phase A scripts resolve."""
        phase_a = [
            'text_normalizer.py',
            'component_extractor.py',
            'component_id_generator.py',
            'dependency_analyzer.py',
            'io_surface_analyzer.py',
            'deliverable_analyzer.py',
            'capability_tagger.py',
        ]
        
        for script in phase_a:
            resolved = resolve_script_path(script, mapp_py_dir)
            assert resolved.exists(), f"{script} not found"
    
    def test_resolve_all_phase_b_scripts(self):
        """Verify all Phase B scripts resolve."""
        phase_b = [
            'test_runner.py',
            'linter_runner.py',
            'complexity_analyzer.py',
            'quality_scorer.py',
        ]
        
        for script in phase_b:
            resolved = resolve_script_path(script, mapp_py_dir)
            assert resolved.exists(), f"{script} not found"
    
    def test_resolve_phase_c_scripts(self):
        """Verify all Phase C scripts resolve."""
        phase_c = [
            'similarity_clusterer.py',
            'canonical_ranker.py',
        ]
        
        for script in phase_c:
            resolved = resolve_script_path(script, mapp_py_dir)
            assert resolved.exists(), f"{script} not found"
    
    def test_resolve_orchestrator(self):
        """Verify orchestrator resolves."""
        resolved = resolve_script_path('registry_integration_pipeline.py', mapp_py_dir)
        assert resolved.exists()
        assert resolved.name == 'P_01260202173939000084_registry_integration_pipeline.py'
    
    def test_validate_all_scripts_exist(self):
        """Verify all mapped scripts exist."""
        validation = validate_all_scripts(mapp_py_dir)
        missing = [name for name, exists in validation.items() if not exists]
        assert len(missing) == 0, f"Missing scripts: {missing}"
    
    def test_get_logical_name(self):
        """Test reverse lookup."""
        logical = get_logical_name('P_01260202173939000060_text_normalizer.py')
        assert logical == 'text_normalizer.py'
    
    def test_list_all_scripts(self):
        """Test listing all scripts."""
        scripts = list_all_scripts()
        assert len(scripts) > 0
        assert 'text_normalizer.py' in scripts
        assert 'registry_integration_pipeline.py' in scripts


class TestQualityScorer:
    """Test quality scorer functionality."""
    
    def test_perfect_quality_score(self):
        """Test perfect score calculation."""
        from P_01260202173939000085_quality_scorer import calculate_score
        
        metrics = {
            'py_tests_executed': True,
            'py_pytest_exit_code': 0,
            'py_coverage_percent': 100,
            'py_defs_public_api_hash': 'abc123',
            'py_defs_functions_count': 5,
            'py_static_issues_count': 0,
            'py_complexity_cyclomatic': 3,
        }
        
        score = calculate_score(metrics)
        assert score == 100
    
    def test_zero_quality_score(self):
        """Test minimum score calculation."""
        from P_01260202173939000085_quality_scorer import calculate_score
        
        metrics = {
            'py_tests_executed': False,
            'py_coverage_percent': 0,
            'py_static_issues_count': 50,
            'py_complexity_cyclomatic': 100,
        }
        
        score = calculate_score(metrics)
        assert 0 <= score <= 30  # Can still get some points
    
    def test_partial_quality_score(self):
        """Test realistic scenario."""
        from P_01260202173939000085_quality_scorer import calculate_score
        
        metrics = {
            'py_tests_executed': True,
            'py_pytest_exit_code': 0,
            'py_coverage_percent': 75,
            'py_defs_public_api_hash': 'abc123',
            'py_static_issues_count': 5,
            'py_complexity_cyclomatic': 8,
        }
        
        score = calculate_score(metrics)
        assert 70 <= score <= 95


class TestSimilarityClusterer:
    """Test similarity clustering functionality."""
    
    def test_cluster_by_exact_hash(self):
        """Test clustering by exact signature hash match."""
        from P_01260202173939000086_similarity_clusterer import cluster_by_hash
        
        records = [
            {'file_id': '12345678901234567890', 'py_deliverable_signature_hash': 'aaa'},
            {'file_id': '12345678901234567891', 'py_deliverable_signature_hash': 'aaa'},
            {'file_id': '12345678901234567892', 'py_deliverable_signature_hash': 'bbb'},
        ]
        
        clusters = cluster_by_hash(records)
        
        assert 'aaa' in clusters
        assert len(clusters['aaa']) == 2
        assert 'bbb' in clusters
        assert len(clusters['bbb']) == 1
    
    def test_singleton_clusters(self):
        """Test files without signature get singleton clusters."""
        from P_01260202173939000086_similarity_clusterer import cluster_by_hash
        
        records = [
            {'file_id': '12345678901234567890', 'py_deliverable_signature_hash': None},
        ]
        
        clusters = cluster_by_hash(records)
        
        assert len(clusters) == 1
        singleton_key = list(clusters.keys())[0]
        assert singleton_key.startswith('SINGLETON_')
    
    def test_assign_group_ids(self):
        """Test group ID assignment is deterministic."""
        from P_01260202173939000086_similarity_clusterer import assign_group_ids
        
        clusters = {
            'aaa': ['12345678901234567890', '12345678901234567891'],
            'bbb': ['12345678901234567892'],
        }
        
        result1 = assign_group_ids(clusters)
        result2 = assign_group_ids(clusters)
        
        # Deterministic
        assert result1 == result2
        
        # Same group for files in same cluster
        assert result1['12345678901234567890'] == result1['12345678901234567891']
        assert result1['12345678901234567890'] != result1['12345678901234567892']


class TestCanonicalRanker:
    """Test canonical ranking functionality."""
    
    def test_rank_single_file_group(self):
        """Test ranking with single file (no duplicates)."""
        from P_01260202173939000087_canonical_ranker import rank_group
        
        files = [
            {'file_id': '12345678901234567890', 'py_quality_score': 85}
        ]
        
        ranked = rank_group(files)
        
        assert len(ranked) == 1
        assert ranked[0]['py_canonical_candidate_score'] > 0
        assert ranked[0]['py_canonical_candidate_score'] <= 100
    
    def test_rank_multiple_files(self):
        """Test ranking with duplicates."""
        from P_01260202173939000087_canonical_ranker import rank_group
        
        files = [
            {
                'file_id': '12345678901234567890',
                'py_quality_score': 90,
                'py_coverage_percent': 95,
            },
            {
                'file_id': '12345678901234567891',
                'py_quality_score': 60,
                'py_coverage_percent': 50,
            },
        ]
        
        ranked = rank_group(files)
        
        assert len(ranked) == 2
        assert ranked[0]['file_id'] == '12345678901234567890'  # Higher quality first
        assert ranked[0]['py_canonical_candidate_score'] > ranked[1]['py_canonical_candidate_score']
    
    def test_select_canonical(self):
        """Test canonical selection."""
        from P_01260202173939000087_canonical_ranker import select_canonical
        
        ranked = [
            {'file_id': '12345678901234567890', 'py_canonical_candidate_score': 95},
            {'file_id': '12345678901234567891', 'py_canonical_candidate_score': 70},
        ]
        
        canonical = select_canonical(ranked)
        assert canonical == '12345678901234567890'


class TestOrchestratorDryRun:
    """Test orchestrator in dry-run mode."""
    
    @pytest.mark.skipif(not (mapp_py_dir / 'P_01260202173939000084_registry_integration_pipeline.py').exists(),
                       reason="Orchestrator not found")
    def test_orchestrator_imports(self):
        """Test orchestrator can be imported."""
        try:
            from P_01260202173939000084_registry_integration_pipeline import RegistryIntegrationPipeline
            assert RegistryIntegrationPipeline is not None
        except ImportError as e:
            pytest.fail(f"Failed to import orchestrator: {e}")
    
    @pytest.mark.skipif(not (mapp_py_dir / 'P_01260202173939000084_registry_integration_pipeline.py').exists(),
                       reason="Orchestrator not found")
    def test_generate_run_id(self):
        """Test run ID generation."""
        from P_01260202173939000084_registry_integration_pipeline import RegistryIntegrationPipeline
        
        registry_path = repo_root / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"
        
        pipeline = RegistryIntegrationPipeline(mapp_py_dir, registry_path)
        
        run_id = pipeline.run_id
        assert run_id.startswith('RUN-')
        assert len(run_id) >= 23  # RUN-YYYYMMDD-HHMMSS-{6hex}
        assert '-' in run_id
    
    @pytest.mark.skipif(not (mapp_py_dir / 'P_01260202173939000084_registry_integration_pipeline.py').exists(),
                       reason="Orchestrator not found")
    def test_collect_tool_versions(self):
        """Test tool version collection."""
        from P_01260202173939000084_registry_integration_pipeline import RegistryIntegrationPipeline
        
        registry_path = repo_root / "01260207201000001250_REGISTRY" / "01999000042260124503_REGISTRY_file.json"
        
        pipeline = RegistryIntegrationPipeline(mapp_py_dir, registry_path)
        
        versions = pipeline.tool_versions
        assert 'python' in versions
        assert versions['python'] is not None
        assert 'platform' in versions


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
