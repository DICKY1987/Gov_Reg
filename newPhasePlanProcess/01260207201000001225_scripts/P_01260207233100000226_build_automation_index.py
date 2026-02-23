#!/usr/bin/env python3
"""
GATE-007: Build Automation Index

Builds searchable index of all automation commands for quick lookup.

Exit Codes:
    0: Success
    1: Build errors
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutomationIndexBuilder:
    """Builds automation command index"""

    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_data: Dict[str, Any] = {}
        self.index: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        logger.info(f"Building automation index: {self.plan_path}")

        if not self._load_plan():
            return {}

        self._build_command_index()
        self._build_dependency_graph()
        self._generate_search_index()

        logger.info(f"✅ Built index with {len(self.index.get('commands', {}))} commands")
        return self.index

    def _load_plan(self) -> bool:
        if not self.plan_path.exists():
            return False
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
            return True
        except:
            return False

    def _build_command_index(self):
        """Index all commands"""
        commands = self.plan_data.get('plan', {}).get('commands', {})

        indexed_commands = {}
        for cmd_id, cmd_data in commands.items():
            if isinstance(cmd_data, dict):
                indexed_commands[cmd_id] = {
                    'command': cmd_data.get('command', ''),
                    'description': cmd_data.get('description', ''),
                    'phase_id': cmd_data.get('phase_id', ''),
                    'execution_order': cmd_data.get('execution_order', 0)
                }

        self.index['commands'] = indexed_commands

    def _build_dependency_graph(self):
        """Build command dependency graph"""
        phases = self.plan_data.get('plan', {}).get('phases_by_id', {})

        graph = {}
        for phase_id, phase_data in phases.items():
            if isinstance(phase_data, dict):
                graph[phase_id] = phase_data.get('depends_on', [])

        self.index['dependency_graph'] = graph

    def _generate_search_index(self):
        """Generate search metadata"""
        self.index['metadata'] = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'plan_file': str(self.plan_path),
            'total_commands': len(self.index.get('commands', {})),
            'total_phases': len(self.plan_data.get('plan', {}).get('phases_by_id', {}))
        }


def main():
    parser = argparse.ArgumentParser(description='GATE-007: Build automation index')
    parser.add_argument('--plan-file', dest='plan_file', required=False)
    parser.add_argument('plan_file_positional', nargs='?')  # Accept positional too
    parser.add_argument('--output', default='.state/evidence/GATE-007/automation_index.json')
    parser.add_argument('--evidence-dir', help='Evidence output directory (optional)', default='.state/evidence')

    args = parser.parse_args()



    # Use flag if provided, otherwise positional

    plan_file = args.plan_file or args.plan_file_positional

    if not plan_file:

        parser.error("plan_file is required (as --plan-file or positional argument)")

    args.plan_file = plan_file

    builder = AutomationIndexBuilder(args.plan_file)
    index = builder.build()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"\n✅ Automation index built: {output_path}\n")
    sys.exit(0)


if __name__ == '__main__':
    main()
