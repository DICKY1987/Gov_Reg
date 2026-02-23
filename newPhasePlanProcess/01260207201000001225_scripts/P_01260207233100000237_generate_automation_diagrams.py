#!/usr/bin/env python3
"""
GATE-008: Generate Automation Diagrams

Generates visual automation flow diagrams using Graphviz DOT format.

Exit Codes:
    0: Success
    1: Generation errors
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Generates automation flow diagrams"""

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}

    def generate(self, output_dir: Path) -> bool:
        logger.info(f"Generating diagrams: {self.plan_path}")

        if not self._load_plan():
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        self._generate_phase_dag(output_dir / 'phase_dag.dot')
        self._generate_gate_flow(output_dir / 'gate_flow.dot')

        logger.info(f"✅ Diagrams generated in {output_dir}")
        return True

    def _load_plan(self) -> bool:
        if not self.plan_path.exists():
            return False
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            return True
        except:
            return False

    def _generate_phase_dag(self, output_path: Path):
        """Generate phase dependency DAG"""
        phases = self.plan_data.get('plan', {}).get('phases_by_id', {})

        dot = ['digraph phase_dag {']
        dot.append('  rankdir=LR;')
        dot.append('  node [shape=box];')

        for phase_id, phase_data in phases.items():
            if isinstance(phase_data, dict):
                phase_name = phase_data.get('phase_name', phase_id)
                dot.append(f'  "{phase_id}" [label="{phase_name}"];')

                depends_on = phase_data.get('depends_on', [])
                for dep in depends_on:
                    dot.append(f'  "{dep}" -> "{phase_id}";')

        dot.append('}')

        with open(output_path, 'w') as f:
            f.write('\n'.join(dot))

    def _generate_gate_flow(self, output_path: Path):
        """Generate gate flow diagram"""
        gates = self.plan_data.get('plan', {}).get('gates_by_id', {})

        dot = ['digraph gate_flow {']
        dot.append('  rankdir=TB;')
        dot.append('  node [shape=diamond];')

        for gate_id, gate_data in gates.items():
            if isinstance(gate_data, dict):
                gate_name = gate_data.get('gate_name', gate_id)
                dot.append(f'  "{gate_id}" [label="{gate_name}"];')

                depends_on = gate_data.get('depends_on', [])
                for dep in depends_on:
                    dot.append(f'  "{dep}" -> "{gate_id}";')

        dot.append('}')

        with open(output_path, 'w') as f:
            f.write('\n'.join(dot))


def main():
    parser = argparse.ArgumentParser(description='GATE-008: Generate automation diagrams')
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output-dir', default='.state/evidence/GATE-008/diagrams')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')
    args = parser.parse_args()

    # Use flag if provided, otherwise positional
    plan_file = args.plan_file or args.plan_file_positional
    if not plan_file:
        parser.error("plan_file is required (as --plan-file or positional argument)")
    args.plan_file = plan_file

    generator = DiagramGenerator(args.plan_file)
    success = generator.generate(Path(args.output_dir))

    if success:
        print(f"\n✅ Diagrams generated in {args.output_dir}\n")
        print("To render: dot -Tsvg phase_dag.dot -o phase_dag.svg\n")
    else:
        print("\n❌ Failed to generate diagrams\n")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
