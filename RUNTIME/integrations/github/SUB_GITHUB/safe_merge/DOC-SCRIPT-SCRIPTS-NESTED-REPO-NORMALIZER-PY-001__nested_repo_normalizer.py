#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-NESTED-REPO-NORMALIZER-PY-001
"""
MERGE-005: Nested Repo Normalizer

Normalizes stray nested repos before merge.
Options:
- keep_as_submodule: Register in .gitmodules
- absorb_as_folder: Remove .git and treat as regular files
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-NESTED-REPO-NORMALIZER-PY-001

import json
import subprocess
import shutil
from pathlib import Path
import argparse


def run_git_command(args, cwd=None):
    """Run git command and return result."""
    result = subprocess.run(
        ['git'] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


def normalize_as_submodule(repo_path, root_path):
    """Add stray repo as proper Git submodule."""

    rel_path = repo_path.relative_to(root_path)

    print(f"  🔧 Adding {rel_path} as submodule...")

    # Check if already has remote
    result = run_git_command(['remote', '-v'], cwd=repo_path)

    if result.returncode == 0 and result.stdout:
        # Has remote - can be proper submodule
        remote_url = result.stdout.split()[1]

        # Add to .gitmodules
        result = run_git_command([
            'submodule', 'add', '-f',
            remote_url, str(rel_path)
        ], cwd=root_path)

        if result.returncode == 0:
            print(f"    ✅ Added as submodule with remote: {remote_url}")
            return {
                'action': 'added_submodule',
                'path': str(rel_path),
                'remote': remote_url,
                'success': True
            }
        else:
            print(f"    ⚠️ Failed to add submodule: {result.stderr}")
            return {
                'action': 'failed',
                'path': str(rel_path),
                'error': result.stderr,
                'success': False
            }
    else:
        # No remote - can't be submodule
        print(f"    ⚠️ No remote URL - cannot add as submodule")
        return {
            'action': 'no_remote',
            'path': str(rel_path),
            'success': False,
            'reason': 'No remote URL configured'
        }


def normalize_as_folder(repo_path, root_path):
    """Remove .git and absorb as regular folder."""

    rel_path = repo_path.relative_to(root_path)
    git_dir = repo_path / '.git'

    print(f"  🔧 Absorbing {rel_path} as regular folder...")

    try:
        # Remove .git
        if git_dir.is_dir():
            shutil.rmtree(git_dir)
        elif git_dir.is_file():
            git_dir.unlink()

        # Stage changes
        result = run_git_command(['add', '-A', str(rel_path)], cwd=root_path)

        if result.returncode == 0:
            print(f"    ✅ Absorbed as regular folder")
            return {
                'action': 'absorbed',
                'path': str(rel_path),
                'success': True
            }
        else:
            print(f"    ⚠️ Failed to stage changes: {result.stderr}")
            return {
                'action': 'failed',
                'path': str(rel_path),
                'error': result.stderr,
                'success': False
            }
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return {
            'action': 'error',
            'path': str(rel_path),
            'error': str(e),
            'success': False
        }


def normalize_nested_repos(work_dir, policy, dry_run=False):
    """Normalize all stray nested repos."""

    work_path = Path(work_dir).resolve()

    # Read detection report
    report_path = work_path / 'nested_repos_report.json'
    if not report_path.exists():
        print("❌ nested_repos_report.json not found")
        print("   Run MERGE-003 first: python nested_repo_detector.py .")
        return {'actions': [], 'count': 0, 'error': 'No report found'}

    with open(report_path) as f:
        report = json.load(f)

    actions = []

    # Process each stray repo
    stray_repos = [r for r in report['nested_repos'] if r['type'] == 'stray_nested_repo']

    if not stray_repos:
        print("✅ No stray nested repos to normalize")
        return {'actions': [], 'count': 0}

    print(f"\n🔧 Found {len(stray_repos)} stray nested repo(s) to normalize")
    print(f"   Policy: {policy}")
    print(f"   Dry run: {dry_run}")
    print()

    for repo in stray_repos:
        repo_path = work_path / repo['path']

        if dry_run:
            print(f"  [DRY RUN] Would normalize: {repo['path']}")
            action = {
                'action': 'dry_run',
                'path': repo['path'],
                'policy': policy,
                'success': True
            }
        else:
            if policy == 'keep_as_submodule':
                action = normalize_as_submodule(repo_path, work_path)
            elif policy == 'absorb_as_folder':
                action = normalize_as_folder(repo_path, work_path)
            else:
                action = {
                    'action': 'unknown_policy',
                    'path': repo['path'],
                    'error': f'Unknown policy: {policy}',
                    'success': False
                }

        actions.append(action)

    # Commit changes if not dry run
    if not dry_run and any(a['success'] for a in actions):
        successful = [a for a in actions if a['success']]

        commit_msg = f"chore: normalize nested repos ({policy})\n\n"
        commit_msg += '\n'.join(f"- {a['action']}: {a['path']}" for a in successful)

        result = run_git_command(['commit', '-m', commit_msg], cwd=work_path)

        if result.returncode == 0:
            print(f"\n✅ Committed normalization changes")
        else:
            print(f"\n⚠️ No changes to commit or commit failed")

    return {
        'actions': actions,
        'count': len(actions),
        'successful': sum(1 for a in actions if a['success'])
    }


def main():
    parser = argparse.ArgumentParser(description='MERGE-005: Nested Repo Normalizer')
    parser.add_argument('work_dir', nargs='?', default='.', help='Repository root')
    parser.add_argument(
        '--policy',
        choices=['keep_as_submodule', 'absorb_as_folder'],
        default='absorb_as_folder',
        help='Normalization policy'
    )
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--output', default='nested_repo_normalization.json', help='Output file')

    args = parser.parse_args()

    print("🔧 MERGE-005: Nested Repo Normalizer")
    print("=" * 50)

    result = normalize_nested_repos(args.work_dir, args.policy, args.dry_run)

    # Save results
    with open(args.output, 'w') as f:
        json.dump({
            'pattern_id': 'MERGE-005',
            'policy': args.policy,
            'dry_run': args.dry_run,
            **result
        }, f, indent=2)

    print(f"\n📄 Results saved: {args.output}")
    print(f"\n📊 Summary:")
    print(f"   Total processed: {result['count']}")
    print(f"   Successful: {result.get('successful', 0)}")
    print(f"   Failed: {result['count'] - result.get('successful', 0)}")

    if result['count'] > 0 and result.get('successful', 0) == result['count']:
        print(f"\n✅ All nested repos normalized successfully")
        return 0
    elif result['count'] == 0:
        print(f"\n✅ No normalization needed")
        return 0
    else:
        print(f"\n⚠️ Some normalizations failed - check {args.output}")
        return 1


if __name__ == '__main__':
    exit(main())
