#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-MULTI-CLONE-GUARD-PY-001
"""
MERGE-007: Multi-Clone Guard

Prevents multiple clones/tools from overwriting each other using distributed locking.
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-MULTI-CLONE-GUARD-PY-001

import os
import DOC-ERROR-UTILS-TIME-145__time
import json
from pathlib import Path
from contextlib import contextmanager
import argparse
import sys


class FileLockBackend:
    """Simple file-based distributed lock."""

    def __init__(self, lock_dir='.git/locks'):
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(exist_ok=True, parents=True)

    @contextmanager
    def acquire(self, resource_name, instance_id, timeout=30):
        """Acquire lock with timeout."""
        lock_file = self.lock_dir / f"{resource_name}.lock"
        start_time = time.time()
        acquired = False

        print(f"🔒 Acquiring lock on '{resource_name}' for {instance_id}...")

        while True:
            try:
                # Try to create lock file exclusively
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)

                # Write lock metadata
                lock_data = {
                    'instance_id': instance_id,
                    'timestamp': time.time(),
                    'resource': resource_name,
                    'pid': os.getpid()
                }
                os.write(fd, json.dumps(lock_data).encode())
                os.close(fd)

                acquired = True
                print(f"✅ Lock acquired for {instance_id}")

                try:
                    yield True
                finally:
                    # Release lock
                    if lock_file.exists():
                        lock_file.unlink()
                        print(f"🔓 Lock released for {instance_id}")

                    # Emit event
                    self._emit_event('lock_released', resource_name, instance_id)

                return

            except FileExistsError:
                # Lock already held - check if stale
                if lock_file.exists():
                    try:
                        age = time.time() - lock_file.stat().st_mtime
                        if age > timeout * 2:  # Stale lock
                            print(f"⚠️ Removing stale lock (age: {age:.1f}s)")
                            lock_file.unlink()
                            continue

                        # Read lock holder info
                        with open(lock_file) as f:
                            lock_info = json.load(f)

                        print(f"⏳ Lock held by {lock_info.get('instance_id', 'unknown')}, waiting...")
                    except:
                        pass

                # Wait and retry
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(
                        f"Could not acquire lock on '{resource_name}' after {timeout}s"
                    )

                time.sleep(0.5)

    def _emit_event(self, event_type, resource, instance_id):
        """Emit lock event to log."""
        event = {
            'pattern_id': 'MERGE-007',
            'timestamp': time.time(),
            'event': event_type,
            'resource': resource,
            'instance_id': instance_id
        }

        event_log = Path('multi_clone_guard_events.jsonl')
        with open(event_log, 'a') as f:
            f.write(json.dumps(event) + '\n')


def safe_push_with_guard(instance_id, branch, remote='origin', rebase_mode='rebase'):
    """Push with multi-clone guard."""

    lock_backend = FileLockBackend()
    resource_name = f"branch_{branch.replace('/', '_')}"

    try:
        with lock_backend.acquire(resource_name, instance_id, timeout=30):
            # Inside lock - safe to push
            print(f"\n📤 Executing safe push for branch: {branch}")

            # Determine script path
            script_dir = Path(__file__).parent
            safe_push_script = script_dir / 'safe_pull_and_push.ps1'

            if safe_push_script.exists():
                # Use PowerShell script
                import subprocess
                result = subprocess.run([
                    'powershell', '-ExecutionPolicy', 'Bypass',
                    '-File', str(safe_push_script),
                    '-Branch', branch,
                    '-RemoteName', remote,
                    '-RebaseMode', rebase_mode
                ])
                return result.returncode == 0
            else:
                print("⚠️ safe_pull_and_push.ps1 not found - falling back to manual push")
                print("   This is less safe than using the pattern!")

                import subprocess

                # Fetch
                subprocess.run(['git', 'fetch', remote])

                # Check divergence
                ahead = subprocess.check_output([
                    'git', 'rev-list', '--count', f'{remote}/{branch}..{branch}'
                ]).decode().strip()

                behind = subprocess.check_output([
                    'git', 'rev-list', '--count', f'{branch}..{remote}/{branch}'
                ]).decode().strip()

                print(f"   Ahead: {ahead}, Behind: {behind}")

                # Pull if behind
                if int(behind) > 0:
                    if rebase_mode == 'rebase':
                        result = subprocess.run(['git', 'pull', '--rebase', remote, branch])
                    else:
                        result = subprocess.run(['git', 'pull', '--ff-only', remote, branch])

                    if result.returncode != 0:
                        return False

                # Push
                result = subprocess.run(['git', 'push', remote, branch])
                return result.returncode == 0

    except TimeoutError as e:
        print(f"\n❌ {e}")
        print(f"   Another instance is holding the lock on {branch}")
        return False


def main():
    parser = argparse.ArgumentParser(description='MERGE-007: Multi-Clone Guard')
    parser.add_argument('--instance-id', required=True, help='Instance identifier (e.g., copilot_clone_1)')
    parser.add_argument('--branch', default='main', help='Branch to push')
    parser.add_argument('--remote', default='origin', help='Remote name')
    parser.add_argument('--rebase-mode', choices=['rebase', 'ff-only'], default='rebase')
    parser.add_argument('--timeout', type=int, default=30, help='Lock timeout in seconds')

    args = parser.parse_args()

    print("🔒 MERGE-007: Multi-Clone Guard")
    print("=" * 50)
    print(f"   Instance: {args.instance_id}")
    print(f"   Branch: {args.branch}")
    print(f"   Remote: {args.remote}")
    print()

    success = safe_push_with_guard(
        args.instance_id,
        args.branch,
        args.remote,
        args.rebase_mode
    )

    if success:
        print("\n✅ Safe push with guard completed successfully")
        return 0
    else:
        print("\n❌ Safe push with guard failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
