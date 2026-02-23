"""
Column Population Compiler
P_01999000042260124550_population_compiler.py

Parses DERIVATIONS.yaml and WRITE_POLICY.yaml, builds dependency DAGs,
performs topological sort, and emits population_plan.json
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from pathlib import Path
import yaml
import json
from collections import defaultdict, deque
from datetime import datetime


@dataclass
class ColumnDerivation:
    """Represents a single column derivation"""
    name: str
    trigger: str  # on_create_only | recompute_on_scan | recompute_on_build
    depends_on: List[str] = field(default_factory=list)
    formula: str = ""
    type: str = "string"
    null_behavior: str = "allow"
    error_policy: str = "set_null"
    rationale: str = ""


class DependencyDAG:
    """Builds and analyzes dependency graphs for column derivations"""
    
    def __init__(self, trigger: str):
        self.trigger = trigger
        self.nodes: Dict[str, ColumnDerivation] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)
    
    def add_column(self, name: str, derivation: ColumnDerivation):
        """Add a column to the DAG"""
        self.nodes[name] = derivation
        depends_on = derivation.depends_on if derivation.depends_on is not None else []
        for dep in depends_on:
            self.edges[dep].add(name)
            self.reverse_edges[name].add(dep)
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles using Tarjan's algorithm"""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = set()
        cycles = []
        
        def strongconnect(node: str):
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack.add(node)
            
            for successor in self.edges.get(node, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif successor in on_stack:
                    lowlinks[node] = min(lowlinks[node], index[successor])
            
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    successor = stack.pop()
                    on_stack.remove(successor)
                    component.append(successor)
                    if successor == node:
                        break
                if len(component) > 1:
                    cycles.append(component)
                elif len(component) == 1:
                    only_node = component[0]
                    if only_node in self.edges.get(only_node, set()):
                        cycles.append(component)
        
        for node in self.nodes:
            if node not in index:
                strongconnect(node)
        
        return cycles
    
    def topological_sort(self) -> List[str]:
        """Topological sort using Kahn's algorithm (handles cross-DAG dependencies)"""
        # Only count in-degree from dependencies that are IN this DAG
        in_degree = {}
        for node in self.nodes:
            in_dag_deps = [dep for dep in self.reverse_edges.get(node, set()) if dep in self.nodes]
            in_degree[node] = len(in_dag_deps)
        
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            # Sort queue for deterministic ordering
            queue = deque(sorted(queue))
            node = queue.popleft()
            result.append(node)
            
            for successor in sorted(self.edges.get(node, [])):
                if successor in self.nodes:  # Only process if in this DAG
                    in_degree[successor] -= 1
                    if in_degree[successor] == 0:
                        queue.append(successor)
        
        if len(result) != len(self.nodes):
            raise ValueError(f"Cycle detected in {self.trigger} DAG")
        
        return result


class PopulationCompiler:
    """Main compiler class"""
    
    def __init__(self, derivations_path: Path, write_policy_path: Path):
        self.derivations_path = derivations_path
        self.write_policy_path = write_policy_path
        self.dags: Dict[str, DependencyDAG] = {}
        self.derivations: Dict[str, ColumnDerivation] = {}
        self.write_policies: Dict[str, str] = {}
    
    def load_files(self):
        """Load YAML files"""
        with open(self.derivations_path, 'r', encoding='utf-8') as f:
            derivations_data = yaml.safe_load(f)
        
        with open(self.write_policy_path, 'r', encoding='utf-8') as f:
            write_policy_data = yaml.safe_load(f)
        
        # Parse derivations
        if 'derived_columns' in derivations_data:
            for col_name, col_spec in derivations_data['derived_columns'].items():
                self.derivations[col_name] = ColumnDerivation(
                    name=col_name,
                    trigger=col_spec.get('trigger', 'recompute_on_scan'),
                    depends_on=col_spec.get('depends_on', []),
                    formula=col_spec.get('formula', ''),
                    type=col_spec.get('type', 'string'),
                    null_behavior=col_spec.get('null_behavior', 'allow'),
                    error_policy=col_spec.get('error_policy', 'set_null'),
                    rationale=col_spec.get('rationale', '')
                )
        
        # Parse write policies
        if 'columns' in write_policy_data:
            for col_name, col_spec in write_policy_data['columns'].items():
                self.write_policies[col_name] = col_spec.get('update_policy', 'unknown')
    
    def build_dags(self):
        """Build DAGs per trigger type"""
        trigger_types = ['on_create_only', 'recompute_on_scan', 'recompute_on_build']
        
        for trigger in trigger_types:
            self.dags[trigger] = DependencyDAG(trigger)
        
        for col_name, derivation in self.derivations.items():
            if derivation.trigger in self.dags:
                self.dags[derivation.trigger].add_column(col_name, derivation)
    
    def compile(self) -> Dict:
        """Compile full population plan"""
        self.load_files()
        self.build_dags()
        
        plan = {
            'version': '1.0.0',
            'generated_utc': datetime.utcnow().isoformat() + 'Z',
            'source_files': {
                'derivations': str(self.derivations_path),
                'write_policy': str(self.write_policy_path)
            },
            'trigger_plans': {},
            'validation_summary': {
                'all_valid': True,
                'cycle_count': 0,
                'missing_derivation_count': 0
            }
        }
        
        for trigger, dag in self.dags.items():
            cycles = dag.detect_cycles()
            if cycles:
                plan['validation_summary']['all_valid'] = False
                plan['validation_summary']['cycle_count'] += len(cycles)
                print(f"ERROR: Cycles detected in {trigger}: {cycles}")
                continue
            
            execution_order = dag.topological_sort()
            
            plan['trigger_plans'][trigger] = {
                'column_count': len(dag.nodes),
                'execution_order': execution_order,
                'dependency_graph': {
                    node: list(dag.edges.get(node, []))
                    for node in dag.nodes
                }
            }
        
        return plan
    
    def emit_plan(self, output_path: Path):
        """Emit plan to JSON file"""
        plan = self.compile()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2)
        print(f"Plan emitted to: {output_path}")
        return plan


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Column Population Compiler')
    parser.add_argument('command', choices=['compile'], help='Command to run')
    parser.add_argument('--derivations', required=True, help='Path to DERIVATIONS.yaml')
    parser.add_argument('--write-policy', required=True, help='Path to WRITE_POLICY.yaml')
    parser.add_argument('--output', required=True, help='Output path for population_plan.json')
    
    args = parser.parse_args()
    
    if args.command == 'compile':
        compiler = PopulationCompiler(
            Path(args.derivations),
            Path(args.write_policy)
        )
        plan = compiler.emit_plan(Path(args.output))
        
        if plan['validation_summary']['all_valid']:
            print("Compilation successful")
            print(f"cycle_count: {plan['validation_summary']['cycle_count']}")
            return 0
        else:
            print("Compilation failed")
            return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
