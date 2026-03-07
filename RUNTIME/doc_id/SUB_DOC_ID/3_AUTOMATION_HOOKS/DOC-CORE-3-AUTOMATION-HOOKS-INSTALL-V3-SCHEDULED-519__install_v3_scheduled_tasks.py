# DOC_LINK: DOC-CORE-3-AUTOMATION-HOOKS-INSTALL-V3-SCHEDULED-519
# TRIGGER_ID: TRIGGER-SCHED-INSTALL-V3-SCHEDULED-TASKS-001
"""
Install V3 Scheduled Tasks
DOC_LINK: A-REGV3-SCHEDULER-010
Work ID: WORK-REGV3-002

Configures OS-level scheduled tasks for V3 nightly scans and health checks.
"""

import sys
import platform
import subprocess
from pathlib import Path


def install_windows_tasks(repo_root: Path):
    """Install Windows scheduled tasks using schtasks"""

    hooks_dir = repo_root / "SUB_DOC_ID" / "3_AUTOMATION_HOOKS"

    # Task 1: Nightly full scan (3:00 AM)
    nightly_bat = hooks_dir / "run_nightly_scan.bat"
    subprocess.run([
        'schtasks', '/create', '/tn', 'DOC_ID_V3_Nightly_Scan',
        '/tr', str(nightly_bat),
        '/sc', 'daily', '/st', '03:00',
        '/f'  # Force overwrite if exists
    ], check=True)

    # Task 2: Health check (4:00 AM)
    health_bat = hooks_dir / "run_health_check.bat"
    subprocess.run([
        'schtasks', '/create', '/tn', 'DOC_ID_V3_Health_Check',
        '/tr', str(health_bat),
        '/sc', 'daily', '/st', '04:00',
        '/f'
    ], check=True)

    # Task 3: Dashboard generation (4:30 AM)
    dashboard_bat = hooks_dir / "run_dashboard.bat"
    subprocess.run([
        'schtasks', '/create', '/tn', 'DOC_ID_V3_Dashboard',
        '/tr', str(dashboard_bat),
        '/sc', 'daily', '/st', '04:30',
        '/f'
    ], check=True)

    print("✓ Windows scheduled tasks installed successfully")


def install_linux_tasks(repo_root: Path):
    """Install Linux cron jobs"""

    python_exe = sys.executable
    backfill_script = repo_root / "SUB_DOC_ID" / "migration_v3" / "tools" / "backfill_tier2_tier3.py"
    health_script = repo_root / "SUB_DOC_ID" / "migration_v3" / "tools" / "v3_health_check.py"
    dashboard_script = repo_root / "SUB_DOC_ID" / "migration_v3" / "tools" / "v3_dashboard.py"
    db_path = repo_root / "SUB_DOC_ID" / "migration_v3" / "data" / "registry_v3.db"

    cron_entries = f"""
# Registry V3 Scheduled Tasks (WORK-REGV3-002)
0 3 * * * cd {repo_root}/SUB_DOC_ID/migration_v3 && {python_exe} {backfill_script} --db {db_path} --repo-root {repo_root} --batch-size 100 >> /var/log/v3_nightly_scan.log 2>&1
0 4 * * * cd {repo_root}/SUB_DOC_ID/migration_v3 && {python_exe} {health_script} --db {db_path} --fail-on-warning >> /var/log/v3_health_check.log 2>&1
30 4 * * * cd {repo_root}/SUB_DOC_ID/migration_v3 && {python_exe} {dashboard_script} --db {db_path} --output {repo_root}/SUB_DOC_ID/4_REPORTING_MONITORING/v3_dashboard.html >> /var/log/v3_dashboard.log 2>&1
"""

    # Add to crontab
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    existing_crontab = result.stdout if result.returncode == 0 else ""

    # Remove old V3 entries
    lines = [line for line in existing_crontab.split('\n') if 'WORK-REGV3-002' not in line]
    new_crontab = '\n'.join(lines) + cron_entries

    subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=True)

    print("✓ Linux cron jobs installed successfully")


def main():
    """Install scheduled tasks for current OS"""

    repo_root = Path(__file__).parent.parent.parent
    os_type = platform.system()

    print(f"Installing V3 scheduled tasks for {os_type}...")

    if os_type == "Windows":
        install_windows_tasks(repo_root)
    elif os_type == "Linux":
        install_linux_tasks(repo_root)
    elif os_type == "Darwin":  # macOS
        print("macOS support coming soon - use launchd")
        sys.exit(1)
    else:
        print(f"Unsupported OS: {os_type}")
        sys.exit(1)

    print("\n✅ Scheduled tasks installed successfully!")
    print("\nTasks configured:")
    print("  • Nightly Scan: 3:00 AM daily")
    print("  • Health Check: 4:00 AM daily")
    print("  • Dashboard: 4:30 AM daily")


if __name__ == "__main__":
    main()
