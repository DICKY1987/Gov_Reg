#!/usr/bin/env python
# DOC_LINK: DOC-SCRIPT-ADD-GITHUB-ACTIONS-CACHE-001
"""
Add caching to GitHub Actions workflows.

PATTERN: EXEC-001 (Batch File Transformation)
DOC_ID: DOC-SCRIPT-ADD-GITHUB-ACTIONS-CACHE-001

Purpose: Quick Win #3 - Add pip/pre-commit caching to speed up CI
Time: 1 hour | Saves: 3h/month (faster CI runs)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class GitHubActionsCacheAdder:
    """Add caching steps to GitHub Actions workflows."""

    def __init__(self):
        self.files_modified = []
        self.changes_made = 0
        
        self.pip_cache = """
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
"""

        self.precommit_cache = """
      - name: Cache pre-commit hooks
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: ${{ runner.os }}-precommit-${{ hashFiles('.pre-commit-config.yaml') }}
          restore-keys: |
            ${{ runner.os }}-precommit-
"""

    def process_workflow(self, filepath: Path) -> Tuple[bool, str]:
        """Add caching to a workflow file.
        
        Returns:
            (modified: bool, reason: str)
        """
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Check if already has caching
            if 'actions/cache@' in content:
                return False, "already has cache"
            
            modified = False
            reason_parts = []
            
            # Add pip caching after "Set up Python" step
            if 'setup-python@' in content and 'requirements.txt' in content:
                # Find the setup-python step
                pattern = r'(      - name: Set up Python\n.*?python-version:.*?\n)'
                replacement = r'\1' + self.pip_cache
                
                new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                if new_content != content:
                    content = new_content
                    modified = True
                    reason_parts.append("pip cache")
            
            # Add pre-commit caching before "Install pre-commit" or "Run pre-commit" step
            if 'pre-commit' in content.lower():
                pattern = r'(      - name: Set up Python\n.*?python-version:.*?\n)'
                
                # Check if we're in a pre-commit job
                if 'pre-commit' in content.lower():
                    new_content = re.sub(pattern, replacement + self.precommit_cache, content, flags=re.DOTALL, count=1)
                    if new_content != content:
                        content = new_content
                        modified = True
                        reason_parts.append("pre-commit cache")
            
            if modified:
                filepath.write_text(content, encoding='utf-8')
                return True, " + ".join(reason_parts)
            
            return False, "no caching opportunities found"
            
        except Exception as e:
            return False, f"error: {e}"

    def process_batch(self, filepaths: List[Path], batch_num: int, total_batches: int):
        """Process a batch of workflow files."""
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(filepaths)} files)")
        
        for filepath in filepaths:
            try:
                relative_path = filepath.relative_to(Path.cwd())
            except ValueError:
                relative_path = filepath
            modified, reason = self.process_workflow(filepath)
            
            if modified:
                self.files_modified.append(filepath)
                self.changes_made += 1
                print(f"  ✅ {relative_path} ({reason})")
            else:
                print(f"  ⏭️  {relative_path} ({reason})")

    def verify(self) -> dict:
        """Verify changes."""
        verified = 0
        for filepath in self.files_modified:
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                if 'actions/cache@v4' in content:
                    verified += 1
        
        return {
            'total_files_processed': len(self.files_modified),
            'verified': verified,
            'success': verified == len(self.files_modified),
            'changes_made': self.changes_made
        }


def main():
    """Execute EXEC-001 pattern: Batch File Transformation."""
    
    print("=" * 60)
    print("QUICK WIN #3: Add GitHub Actions Caching")
    print("=" * 60)
    print("Pattern: EXEC-001 (Batch File Transformation)")
    print("Purpose: Speed up CI runs with pip/pre-commit caching")
    print()
    
    # Find all workflow files
    print("🔍 Discovery: Finding GitHub Actions workflows...")
    
    workflows_dir = Path('.github/workflows')
    if not workflows_dir.exists():
        print("❌ No .github/workflows directory found")
        return 1
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    print(f"Found {len(workflow_files)} workflow files")
    print()
    
    if not workflow_files:
        print("✅ No workflows to process!")
        return 0
    
    # Process workflows
    adder = GitHubActionsCacheAdder()
    batch_size = 10
    
    batches = [workflow_files[i:i+batch_size] for i in range(0, len(workflow_files), batch_size)]
    
    for batch_num, batch in enumerate(batches, 1):
        adder.process_batch(batch, batch_num, len(batches))
    
    # Verify
    print("\n🔍 Verification...")
    result = adder.verify()
    
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Workflows modified: {result['total_files_processed']}")
    print(f"Cache steps added: {result['changes_made']}")
    print(f"Verified: {result['verified']}/{result['total_files_processed']}")
    print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print()
    
    if result['success'] and result['total_files_processed'] > 0:
        print("✨ Benefits:")
        print("  • Faster CI runs (pip packages cached)")
        print("  • Faster pre-commit checks (hooks cached)")
        print("  • Reduced GitHub Actions minutes usage")
        print("  • Estimated savings: 30-60 seconds per workflow run")
        print()
    
    print("Next steps:")
    print("1. Review changes: git diff .github/workflows/")
    print("2. Test: Push commit and watch Actions tab")
    print("3. Commit: git commit -m 'feat: add GitHub Actions caching'")
    print()
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
