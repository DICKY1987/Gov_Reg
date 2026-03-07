#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TRIGGER_ID: TRIGGER-SCHED-SETUP-SCHEDULED-TASKS-002
# DOC_LINK: DOC-SCRIPT-SETUP-SCHEDULED-TASKS-006
"""
Setup Scheduled Tasks for DOC_ID Automation

PATTERN: EXEC-003 Tool Availability Guards
Ground Truth: Scheduled task exists and is enabled

USAGE:
    python doc_id/setup_scheduled_tasks.py
    python doc_id/setup_scheduled_tasks.py --verify
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, MODULE_ROOT


def setup_windows_task():
    """Setup Windows Task Scheduler"""
    # PATTERN: Tool guard
    result = subprocess.run(['where', 'schtasks'],
                           capture_output=True)
    if result.returncode != 0:
        print("❌ schtasks not available")
        sys.exit(1)

    task_cmd = [
        'schtasks', '/create',
        '/tn', 'DOC_ID_Daily_Report',
        '/tr', f'python {REPO_ROOT}/doc_id/scheduled_report_generator.py daily',
        '/sc', 'daily',
        '/st', '02:00',
        '/f'  # Force overwrite
    ]

    result = subprocess.run(task_cmd, capture_output=True, text=True)

    # Ground Truth: Task created
    if result.returncode == 0:
        print("✅ Windows scheduled task created")
        return True
    else:
        print(f"❌ Failed: {result.stderr}")
        return False


def setup_linux_cron():
    """Setup Linux crontab"""
    cron_entry = f"0 2 * * * cd {REPO_ROOT} && python doc_id/scheduled_report_generator.py daily\n"

    # Read existing crontab
    result = subprocess.run(['crontab', '-l'],
                           capture_output=True, text=True)

    existing = result.stdout if result.returncode == 0 else ""

    # Check if already exists
    if 'scheduled_report_generator.py daily' in existing:
        print("✅ Cron entry already exists")
        return True

    # Add new entry
    new_crontab = existing + cron_entry

    process = subprocess.Popen(['crontab', '-'],
                               stdin=subprocess.PIPE,
                               text=True)
    process.communicate(input=new_crontab)

    # Ground Truth: Entry in crontab
    if process.returncode == 0:
        print("✅ Linux cron entry created")
        return True
    else:
        print("❌ Failed to create cron entry")
        return False


def verify_task():
    """Verify scheduled task exists"""
    system = platform.system()

    if system == 'Windows':
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'DOC_ID_Daily_Report'],
            capture_output=True
        )
        return result.returncode == 0
    else:
        result = subprocess.run(
            ['crontab', '-l'],
            capture_output=True, text=True
        )
        return 'scheduled_report_generator.py daily' in result.stdout


def main():
    parser = argparse.ArgumentParser(description="Setup Scheduled Tasks")
    parser.add_argument('--verify', action='store_true',
                       help='Verify task exists')
    args = parser.parse_args()

    if args.verify:
        if verify_task():
            print("✅ Scheduled task is active")
            sys.exit(0)
        else:
            print("❌ Scheduled task not found")
            sys.exit(1)

    # Setup based on platform
    system = platform.system()
    print(f"Setting up scheduled task for {system}...")

    if system == 'Windows':
        success = setup_windows_task()
    elif system in ('Linux', 'Darwin'):
        success = setup_linux_cron()
    else:
        print(f"❌ Unsupported platform: {system}")
        sys.exit(1)

    # Verification
    if verify_task():
        print("✅ Setup complete and verified")
        sys.exit(0)
    else:
        print("❌ Setup failed verification")
        sys.exit(1)


if __name__ == '__main__':
    main()
