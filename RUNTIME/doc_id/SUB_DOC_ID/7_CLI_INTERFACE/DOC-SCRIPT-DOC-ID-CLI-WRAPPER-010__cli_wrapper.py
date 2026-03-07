#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-CLI-WRAPPER-010
"""
DOC_ID CLI Wrapper - Unified Command Interface

PATTERN: EXEC-006 Consolidated Entry Point
Ground Truth: All commands accessible via single CLI

USAGE (from repo root):
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py scan
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py cleanup --auto-approve
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py sync --auto-sync
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py alerts
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py report daily
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py install-hook
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py setup-scheduler
    python SUB_DOC_ID\\7_CLI_INTERFACE\\cli_wrapper.py watch --debounce 600
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT

CORE_DIR = MODULE_ROOT / "1_CORE_OPERATIONS"
VALIDATION_DIR = MODULE_ROOT / "2_VALIDATION_FIXING"
AUTOMATION_DIR = MODULE_ROOT / "3_AUTOMATION_HOOKS"
REPORTING_DIR = MODULE_ROOT / "4_REPORTING_MONITORING"
REGISTRY_DIR = MODULE_ROOT / "5_REGISTRY_DATA"


class DocIDCLI:
    """Unified CLI wrapper for all DOC_ID operations"""

    def __init__(self):
        self.commands = {
            'scan': {
                'script': CORE_DIR / 'doc_id_scanner.py',
                'default_args': ['scan'],
            },
            'cleanup': {
                'script': VALIDATION_DIR / 'cleanup_invalid_doc_ids.py',
                'default_args': ['scan'],
            },
            'sync': {
                'script': REGISTRY_DIR / 'sync_registries.py',
                'default_args': ['sync'],
            },
            'alerts': {
                'script': REPORTING_DIR / 'alert_monitor.py',
                'default_args': [],
            },
            'report': {
                'script': REPORTING_DIR / 'scheduled_report_generator.py',
                'default_args': ['daily'],
            },
            'install-hook': {
                'script': AUTOMATION_DIR / 'install_pre_commit_hook.py',
                'default_args': [],
            },
            'setup-scheduler': {
                'script': AUTOMATION_DIR / 'setup_scheduled_tasks.py',
                'default_args': [],
            },
            'watch': {
                'script': AUTOMATION_DIR / 'file_watcher.py',
                'default_args': [],
            },
        }

    def execute(self, command: str, args: list) -> int:
        """Execute a DOC_ID command"""
        entry = self.commands.get(command)

        if not entry:
            print(f"❌ Unknown command: {command}")
            print(f"Available: {', '.join(self.commands.keys())}")
            return 1

        script = entry['script']
        if not script.exists():
            print(f"❌ Missing script for '{command}': {script}")
            return 1

        default_args = entry.get('default_args', [])
        final_args = args if args else default_args

        cmd = [sys.executable, str(script)] + final_args

        print(f"Executing: {command} -> {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=REPO_ROOT)

        return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='DOC_ID CLI - Unified command interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  scan              Run DOC_ID scanner
  cleanup           Clean up invalid DOC_IDs
  sync              Synchronize registries
  alerts            Check alert thresholds
  report            Generate reports
  install-hook      Install pre-commit hook
  setup-scheduler   Setup scheduled tasks
  watch             Start file watcher

Examples:
  %(prog)s scan
  %(prog)s cleanup --auto-approve
  %(prog)s sync --auto-sync --max-drift 100
  %(prog)s alerts
  %(prog)s report daily
  %(prog)s install-hook
  %(prog)s setup-scheduler
  %(prog)s watch --debounce 300
        """
    )

    parser.add_argument('command',
                       choices=['scan', 'cleanup', 'sync', 'alerts', 'report',
                               'install-hook', 'setup-scheduler', 'watch'],
                       help='Command to execute')
    parser.add_argument('args', nargs='*', help='Arguments to pass to command')

    parsed_args = parser.parse_args()

    cli = DocIDCLI()
    exit_code = cli.execute(parsed_args.command, parsed_args.args)

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
