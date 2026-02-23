#!/usr/bin/env python3
"""DAG Generator - Generates directed acyclic graph of phase dependencies"""
import argparse, json, sys
from pathlib import Path

class DAGGenerator:
    def __init__(self, plan_path):
        self.plan_path = Path(plan_path)

    def generate(self):
        with open(self.plan_path) as f:
            data = json.load(f)

        phases = data.get('plan', {}).get('phases_by_id', {})
        dag = {'nodes': [], 'edges': [], 'execution_order': []}

        for phase_id, phase_data in phases.items():
            dag['nodes'].append({'id': phase_id, 'name': phase_data.get('phase_name', phase_id)})
            for dep in phase_data.get('depends_on', []):
                dag['edges'].append({'from': dep, 'to': phase_id})

        # Simple topological sort
        visited, temp = set(), set()
        order = []

        def visit(node):
            if node in temp:
                return False  # Cycle detected
            if node not in visited:
                temp.add(node)
                for edge in dag['edges']:
                    if edge['from'] == node:
                        if not visit(edge['to']):
                            return False
                temp.remove(node)
                visited.add(node)
                order.insert(0, node)
            return True

        for phase_id in phases.keys():
            if phase_id not in visited:
                if not visit(phase_id):
                    return False, {'error': 'Circular dependency detected'}

        dag['execution_order'] = order
        return True, dag

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-file', required=True, help='Path to plan JSON file')
    parser.add_argument('--output', default='phase_dag.json')
    args = parser.parse_args()

    generator = DAGGenerator(args.plan_file)
    is_valid, result = generator.generate()

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"{'✅ PASSED' if is_valid else '❌ FAILED'}: DAG Generation")
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()
