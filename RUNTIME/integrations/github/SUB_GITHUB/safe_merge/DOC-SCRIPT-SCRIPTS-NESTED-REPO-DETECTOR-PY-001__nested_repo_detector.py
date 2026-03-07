#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-NESTED-REPO-DETECTOR-PY-001
"""
MERGE-003: Nested Repo Detector

Finds and classifies nested Git repos / submodules that can break merges.
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-NESTED-REPO-DETECTOR-PY-001

import json
from pathlib import Path
import argparse


def check_gitmodules(repo_root, subdir):
    """Check if subdir is registered in .gitmodules."""
    gitmodules = repo_root / '.gitmodules'
    if not gitmodules.exists():
        return False

    content = gitmodules.read_text()
    rel_path = subdir.relative_to(repo_root)

    # Check both Windows and Unix paths
    return (str(rel_path) in content or
            str(rel_path).replace('\\', '/') in content)


def detect_nested_repos(work_dir):
    """Recursively find .git directories."""

    work_path = Path(work_dir).resolve()
    root_git = work_path / '.git'

    git_dirs = []

    print(f"🔍 Scanning for nested repos in: {work_path}")

    # Find all .git directories (excluding root)
    for git_dir in work_path.rglob('.git'):
        if git_dir == root_git:
            continue  # Skip root .git

        parent = git_dir.parent
        is_submodule = check_gitmodules(work_path, parent)
        is_file = git_dir.is_file()  # .git can be file (submodule) or dir

        repo_type = 'submodule' if is_submodule else 'stray_nested_repo'

        git_dirs.append({
            'path': str(parent.relative_to(work_path)),
            'type': repo_type,
            'git_dir': str(git_dir.relative_to(work_path)),
            'is_file': is_file
        })

        icon = "📦" if is_submodule else "⚠️"
        print(f"  {icon} Found: {parent.relative_to(work_path)} ({repo_type})")

    # Generate report
    report = {
        'pattern_id': 'MERGE-003',
        'work_dir': str(work_path),
        'nested_repos': git_dirs,
        'summary': {
            'total': len(git_dirs),
            'submodule_count': sum(1 for r in git_dirs if r['type'] == 'submodule'),
            'stray_count': sum(1 for r in git_dirs if r['type'] == 'stray_nested_repo')
        }
    }

    return report


def main():
    parser = argparse.ArgumentParser(description='MERGE-003: Nested Repo Detector')
    parser.add_argument('work_dir', nargs='?', default='.', help='Repository root')
    parser.add_argument('--output', default='nested_repos_report.json', help='Output file')

    args = parser.parse_args()

    report = detect_nested_repos(args.work_dir)

    # Save JSON
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Report saved: {args.output}")
    print(f"\n📊 Summary:")
    print(f"   Total nested repos: {report['summary']['total']}")
    print(f"   Proper submodules: {report['summary']['submodule_count']}")
    print(f"   Stray nested repos: {report['summary']['stray_count']}")

    if report['summary']['stray_count'] > 0:
        print(f"\n⚠️  WARNING: Found {report['summary']['stray_count']} stray nested repo(s)")
        print(f"   These should be normalized before merge (see MERGE-005)")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
