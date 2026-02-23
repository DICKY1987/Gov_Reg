"""
Test suite for Column Population Compiler
tests/test_population_compiler.py
"""

import pytest
import sys
from pathlib import Path
import tempfile
import yaml
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'validators'))

from P_01999000042260124550_population_compiler import (
    ColumnDerivation,
    DependencyDAG,
    PopulationCompiler
)
from P_01999000042260124551_validate_population_completeness import (
    PopulationCompletenessValidator,
    ValidationError
)


class TestDependencyDAG:
    """Test DAG building and analysis"""
    
    def test_empty_dag(self):
        """Empty DAG should work"""
        dag = DependencyDAG('test_trigger')
        assert len(dag.nodes) == 0
        assert dag.topological_sort() == []
    
    def test_linear_chain(self):
        """A→B→C should sort to [A, B, C]"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('A', ColumnDerivation('A', 'test_trigger', [], 'formula_A'))
        dag.add_column('B', ColumnDerivation('B', 'test_trigger', ['A'], 'formula_B'))
        dag.add_column('C', ColumnDerivation('C', 'test_trigger', ['B'], 'formula_C'))
        
        result = dag.topological_sort()
        assert result == ['A', 'B', 'C']
    
    def test_diamond_dependency(self):
        """A→(B,C)→D should work"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('A', ColumnDerivation('A', 'test_trigger', [], 'formula_A'))
        dag.add_column('B', ColumnDerivation('B', 'test_trigger', ['A'], 'formula_B'))
        dag.add_column('C', ColumnDerivation('C', 'test_trigger', ['A'], 'formula_C'))
        dag.add_column('D', ColumnDerivation('D', 'test_trigger', ['B', 'C'], 'formula_D'))
        
        result = dag.topological_sort()
        assert result[0] == 'A'
        assert result[-1] == 'D'
        assert 'B' in result and 'C' in result
    
    def test_cycle_detection(self):
        """A→B→C→A cycle should be detected"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('A', ColumnDerivation('A', 'test_trigger', ['C'], 'formula_A'))
        dag.add_column('B', ColumnDerivation('B', 'test_trigger', ['A'], 'formula_B'))
        dag.add_column('C', ColumnDerivation('C', 'test_trigger', ['B'], 'formula_C'))
        
        cycles = dag.detect_cycles()
        assert len(cycles) > 0
    
    def test_self_reference(self):
        """A→A self-reference should be detected"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('A', ColumnDerivation('A', 'test_trigger', ['A'], 'formula_A'))
        
        cycles = dag.detect_cycles()
        assert len(cycles) > 0


class TestTopologicalSort:
    """Test topological sort correctness"""
    
    def test_respects_dependencies(self):
        """Dependencies should always come before dependents"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('file_id', ColumnDerivation('file_id', 'test_trigger', [], 'GENERATE_FILE_ID()'))
        dag.add_column('absolute_path', ColumnDerivation('absolute_path', 'test_trigger', ['file_id'], 'GET_PATH()'))
        dag.add_column('extension', ColumnDerivation('extension', 'test_trigger', ['absolute_path'], 'EXTRACT_EXT()'))
        
        result = dag.topological_sort()
        
        assert result.index('file_id') < result.index('absolute_path')
        assert result.index('absolute_path') < result.index('extension')
    
    def test_deterministic_output(self):
        """Multiple runs should produce same order"""
        dag1 = DependencyDAG('test_trigger')
        dag2 = DependencyDAG('test_trigger')
        
        for dag in [dag1, dag2]:
            dag.add_column('A', ColumnDerivation('A', 'test_trigger', [], 'formula'))
            dag.add_column('B', ColumnDerivation('B', 'test_trigger', [], 'formula'))
            dag.add_column('C', ColumnDerivation('C', 'test_trigger', ['A', 'B'], 'formula'))
        
        result1 = dag1.topological_sort()
        result2 = dag2.topological_sort()
        
        assert result1 == result2
    
    def test_multiple_roots(self):
        """Multiple independent roots should work"""
        dag = DependencyDAG('test_trigger')
        
        dag.add_column('A', ColumnDerivation('A', 'test_trigger', [], 'formula'))
        dag.add_column('B', ColumnDerivation('B', 'test_trigger', [], 'formula'))
        dag.add_column('C', ColumnDerivation('C', 'test_trigger', [], 'formula'))
        
        result = dag.topological_sort()
        assert len(result) == 3
        assert set(result) == {'A', 'B', 'C'}


class TestPopulationCompiler:
    """Test compiler functionality"""
    
    def test_compile_minimal(self):
        """Compile minimal derivations file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            derivations_path = Path(tmpdir) / 'derivations.yaml'
            write_policy_path = Path(tmpdir) / 'write_policy.yaml'
            
            derivations = {
                'derived_columns': {
                    'file_id': {
                        'trigger': 'on_create_only',
                        'depends_on': [],
                        'formula': 'GENERATE_FILE_ID()',
                        'type': 'string'
                    }
                }
            }
            
            write_policy = {
                'columns': {
                    'file_id': {
                        'update_policy': 'immutable'
                    }
                }
            }
            
            with open(derivations_path, 'w') as f:
                yaml.dump(derivations, f)
            
            with open(write_policy_path, 'w') as f:
                yaml.dump(write_policy, f)
            
            compiler = PopulationCompiler(derivations_path, write_policy_path)
            plan = compiler.compile()
            
            assert plan['version'] == '1.0.0'
            assert 'trigger_plans' in plan
            assert plan['validation_summary']['all_valid'] == True
    
    def test_plan_structure(self):
        """Generated plan should have correct structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            derivations_path = Path(tmpdir) / 'derivations.yaml'
            write_policy_path = Path(tmpdir) / 'write_policy.yaml'
            output_path = Path(tmpdir) / 'plan.json'
            
            derivations = {'derived_columns': {}}
            write_policy = {'columns': {}}
            
            with open(derivations_path, 'w') as f:
                yaml.dump(derivations, f)
            
            with open(write_policy_path, 'w') as f:
                yaml.dump(write_policy, f)
            
            compiler = PopulationCompiler(derivations_path, write_policy_path)
            compiler.emit_plan(output_path)
            
            assert output_path.exists()
            
            with open(output_path) as f:
                plan = json.load(f)
            
            assert 'version' in plan
            assert 'generated_utc' in plan
            assert 'source_files' in plan
            assert 'trigger_plans' in plan
            assert 'validation_summary' in plan


class TestCompletenessValidator:
    """Test validation functionality"""
    
    def test_all_valid_passes(self):
        """Valid configuration should pass"""
        with tempfile.TemporaryDirectory() as tmpdir:
            derivations_path = Path(tmpdir) / 'derivations.yaml'
            write_policy_path = Path(tmpdir) / 'write_policy.yaml'
            
            derivations = {
                'derived_columns': {
                    'file_id': {
                        'trigger': 'on_create_only',
                        'depends_on': [],
                        'formula': 'GENERATE_FILE_ID()'
                    }
                }
            }
            
            write_policy = {
                'columns': {
                    'file_id': {
                        'update_policy': 'immutable'
                    }
                }
            }
            
            with open(derivations_path, 'w') as f:
                yaml.dump(derivations, f)
            
            with open(write_policy_path, 'w') as f:
                yaml.dump(write_policy, f)
            
            validator = PopulationCompletenessValidator(derivations_path, write_policy_path)
            is_valid = validator.validate()
            
            assert is_valid == True
            assert len(validator.errors) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
