"""Installation script for automation gaps implementation.

FILE_ID: 01999000042260125114
PURPOSE: Quick setup for automation gaps implementation
USAGE: python install_automation.py
"""
from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path


def main():
    """Install automation gaps implementation."""
    print("=" * 60)
    print("Automation Gaps Implementation - Installation")
    print("=" * 60)
    print()
    
    # Detect project root
    project_root = Path(__file__).parent
    print(f"Project root: {project_root}")
    print()
    
    # Step 1: Install Git Hooks
    print("Step 1: Installing Git Hooks")
    print("-" * 60)
    
    git_hooks_dir = project_root / ".git" / "hooks"
    if not git_hooks_dir.exists():
        print("⚠️  Git hooks directory not found. Is this a git repository?")
        print("   Run: git init")
        return 1
    
    # Pre-commit hook
    pre_commit_src = project_root / "01260207201000001276_scripts" / "P_01999000042260125106_pre_commit_dir_id_check.py"
    pre_commit_dst = git_hooks_dir / "pre-commit"
    
    if pre_commit_src.exists():
        # Create wrapper script
        wrapper_content = f"""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from {pre_commit_src.stem} import main
sys.exit(main())
"""
        pre_commit_dst.write_text(wrapper_content, encoding='utf-8')
        
        # Make executable (Unix/Linux)
        if sys.platform != 'win32':
            os.chmod(pre_commit_dst, 0o755)
        
        print(f"✅ Installed pre-commit hook")
    else:
        print(f"⚠️  Pre-commit hook source not found: {pre_commit_src}")
    
    # Pre-push hook
    pre_push_src = project_root / "01260207201000001276_scripts" / "P_01999000042260125107_pre_push_governance_check.py"
    pre_push_dst = git_hooks_dir / "pre-push"
    
    if pre_push_src.exists():
        # Create wrapper script
        wrapper_content = f"""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from {pre_push_src.stem} import main
sys.exit(main())
"""
        pre_push_dst.write_text(wrapper_content, encoding='utf-8')
        
        # Make executable (Unix/Linux)
        if sys.platform != 'win32':
            os.chmod(pre_push_dst, 0o755)
        
        print(f"✅ Installed pre-push hook")
    else:
        print(f"⚠️  Pre-push hook source not found: {pre_push_src}")
    
    print()
    
    # Step 2: Create evidence directories
    print("Step 2: Creating Evidence Directories")
    print("-" * 60)
    
    evidence_dirs = [
        ".state/evidence/dir_id_repairs",
        ".state/evidence/watcher_events",
        ".state/evidence/reconciliation",
        ".state/evidence/reference_rewrites",
        ".state/evidence/coverage",
        ".state/evidence/orphan_purges",
        ".state/evidence/transactions",
        ".state/evidence/healthchecks",
    ]
    
    for dir_path in evidence_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    print()
    
    # Step 3: Create sample config
    print("Step 3: Creating Sample Configuration")
    print("-" * 60)
    
    config_path = project_root / "automation_config.json"
    if not config_path.exists():
        import json
        
        config = {
            "project_root": str(project_root),
            "project_root_id": "01260207201000000000",
            "registry_path": "01999000042260124503_governance_registry_unified.json",
            "watcher": {
                "enabled": False,
                "daemon": False
            },
            "healthcheck": {
                "schedule": "0 2 * * *",
                "fail_on_critical": True
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created sample config: {config_path}")
        print("   Edit this file to customize settings")
    else:
        print(f"ℹ️  Config already exists: {config_path}")
    
    print()
    
    # Step 4: Summary
    print("Step 4: Installation Complete")
    print("-" * 60)
    print()
    print("✅ Git hooks installed")
    print("✅ Evidence directories created")
    print("✅ Configuration file ready")
    print()
    print("Next Steps:")
    print("  1. Edit automation_config.json with your settings")
    print("  2. Run initial health check:")
    print(f"     python {project_root / '01260207201000001276_scripts' / 'P_01999000042260125113_healthcheck.py'} --config automation_config.json")
    print("  3. Run reconciliation:")
    print(f"     python {project_root / '01260207201000001173_govreg_core' / 'P_01999000042260125108_registry_fs_reconciler.py'}")
    print("  4. Start watcher (optional):")
    print(f"     python {project_root / '01260207201000001173_govreg_core' / 'P_01999000042260125105_dir_id_watcher.py'} --config automation_config.json")
    print()
    print("For detailed documentation, see:")
    print("  - AUTOMATION_GAPS_IMPLEMENTATION_COMPLETE.md")
    print("  - AUTOMATION_IMPLEMENTATION_QUICKSTART.md")
    print("  - README_PUSH_TO_GITHUB.md")
    print()
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
