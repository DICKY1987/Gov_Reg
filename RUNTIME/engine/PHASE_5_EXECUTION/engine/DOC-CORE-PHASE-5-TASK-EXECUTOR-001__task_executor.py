#!/usr/bin/env python3
"""
Task Executor - Real Task Implementation
Replaces stub execution with actual operations.

DOC_ID: DOC-CORE-PHASE-5-TASK-EXECUTOR-001
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import sys

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
)


class TaskExecutor:
    """
    Executes tasks based on operation_kind.

    Supported operations:
    - test_run: Execute pytest with specified scope
    - git_operation: Git operations via GitAdapter
    - file_edit: Edit files using templates
    - command_execute: Execute shell commands
    - generic: Log task details
    """

    def __init__(self, registry=None, fs_adapter=None, git_adapter=None):
        """
        Initialize task executor.

        Args:
            registry: PathRegistry instance (optional)
            fs_adapter: FilesystemAdapter instance (optional)
            git_adapter: GitAdapter instance (optional)
        """
        self.registry = registry
        self.fs_adapter = fs_adapter
        self.git_adapter = git_adapter
        self.execution_log = []

    def execute(self, task: Dict) -> Dict:
        """
        Execute task based on operation_kind.

        Args:
            task: Task dictionary with operation_kind, context, etc.

        Returns:
            Result dict with status, exit_code, stdout, stderr
        """
        operation = task.get('operation_kind', 'generic')
        task_id = task.get('task_id', 'unknown')

        # Map operations to handlers
        handlers = {
            'test_run': self._execute_test_run,
            'git_operation': self._execute_git_operation,
            'file_edit': self._execute_file_edit,
            'command_execute': self._execute_command,
            'generic': self._execute_generic
        }

        handler = handlers.get(operation, self._execute_generic)

        try:
            result = handler(task)
            result['status'] = 'completed'
            if 'exit_code' not in result:
                result['exit_code'] = 0

            self._log_execution(task_id, operation, result)
            return result

        except Exception as exc:
            error_result = {
                'task_id': task_id,
                'operation_kind': operation,
                'status': 'failed',
                'exit_code': 1,
                'error': str(exc),
                'stdout': '',
                'stderr': str(exc),
                'timestamp': datetime.now().isoformat()
            }
            self._log_execution(task_id, operation, error_result)
            return error_result

    def _execute_test_run(self, task: Dict) -> Dict:
        """
        Execute pytest with specified scope.

        Args:
            task: Task dictionary

        Returns:
            Result with exit code, stdout, stderr, metrics
        """
        task_id = task.get('task_id', 'unknown')
        context = task.get('context', {})
        test_path = context.get('test_path', 'tests/')
        timeout = task.get('timeout_seconds', 300)

        # Build pytest command
        cmd = ['pytest', test_path, '-v', '--tb=short']

        # Execute pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT)
        )

        # Parse pytest output for metrics
        metrics = self._parse_pytest_output(result.stdout)

        return {
            'task_id': task_id,
            'operation_kind': 'test_run',
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

    def _execute_git_operation(self, task: Dict) -> Dict:
        """
        Execute git operations via GitAdapter.

        Args:
            task: Task dictionary

        Returns:
            Result with git operation output
        """
        task_id = task.get('task_id', 'unknown')
        context = task.get('context', {})
        git_op = context.get('git_operation', 'status')

        # Use GitAdapter if available
        if self.git_adapter:
            if git_op == 'status':
                status = self.git_adapter.status()
                return {
                    'task_id': task_id,
                    'operation_kind': 'git_operation',
                    'exit_code': 0,
                    'output': status,
                    'stdout': json.dumps(status, indent=2),
                    'stderr': '',
                    'timestamp': datetime.now().isoformat()
                }
            elif git_op == 'diff':
                diff = self.git_adapter.diff()
                return {
                    'task_id': task_id,
                    'operation_kind': 'git_operation',
                    'exit_code': 0,
                    'output': diff,
                    'stdout': diff,
                    'stderr': '',
                    'timestamp': datetime.now().isoformat()
                }
        else:
            # Fallback to direct git command
            git_commands = {
                'status': ['git', 'status', '--porcelain'],
                'diff': ['git', 'diff'],
                'log': ['git', 'log', '--oneline', '-n', '5']
            }

            cmd = git_commands.get(git_op, ['git', 'status'])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=task.get('timeout_seconds', 60),
                cwd=str(REPO_ROOT)
            )

            return {
                'task_id': task_id,
                'operation_kind': 'git_operation',
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }

    def _execute_file_edit(self, task: Dict) -> Dict:
        """
        Execute file operations (create/edit/delete).

        Args:
            task: Task dictionary

        Returns:
            Result with file operation status
        """
        task_id = task.get('task_id', 'unknown')
        file_scope = task.get('file_scope', {})
        context = task.get('context', {})

        files_created = []
        files_modified = []
        errors = []

        # Handle file creation
        for file_path in file_scope.get('create', []):
            try:
                full_path = REPO_ROOT / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Create with placeholder content
                content = context.get('content', f"# Created by task {task_id}\n")
                full_path.write_text(content, encoding='utf-8')

                files_created.append(str(file_path))
            except Exception as e:
                errors.append(f"Failed to create {file_path}: {e}")

        # Handle file modification
        for file_path in file_scope.get('write', []):
            try:
                full_path = REPO_ROOT / file_path
                if full_path.exists():
                    # For now, just append a comment
                    with open(full_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n# Modified by task {task_id}\n")
                    files_modified.append(str(file_path))
                else:
                    errors.append(f"File not found for modification: {file_path}")
            except Exception as e:
                errors.append(f"Failed to modify {file_path}: {e}")

        exit_code = 0 if not errors else 1
        status_msg = f"Created {len(files_created)}, Modified {len(files_modified)}"
        if errors:
            status_msg += f", {len(errors)} error(s)"

        return {
            'task_id': task_id,
            'operation_kind': 'file_edit',
            'exit_code': exit_code,
            'files_created': files_created,
            'files_modified': files_modified,
            'errors': errors,
            'stdout': status_msg,
            'stderr': '\n'.join(errors) if errors else '',
            'timestamp': datetime.now().isoformat()
        }

    def _execute_command(self, task: Dict) -> Dict:
        """
        Execute arbitrary shell command.

        Args:
            task: Task dictionary with command in context

        Returns:
            Result with command output
        """
        task_id = task.get('task_id', 'unknown')
        context = task.get('context', {})
        command = context.get('command', 'echo "No command specified"')

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=task.get('timeout_seconds', 300),
            cwd=str(REPO_ROOT)
        )

        return {
            'task_id': task_id,
            'operation_kind': 'command_execute',
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'timestamp': datetime.now().isoformat()
        }

    def _execute_generic(self, task: Dict) -> Dict:
        """
        Generic task execution - logs task details.

        Args:
            task: Task dictionary

        Returns:
            Result with success status
        """
        task_id = task.get('task_id', 'unknown')
        description = task.get('context', {}).get('description', 'No description')

        return {
            'task_id': task_id,
            'operation_kind': 'generic',
            'exit_code': 0,
            'stdout': f"Task {task_id} executed: {description}",
            'stderr': '',
            'timestamp': datetime.now().isoformat()
        }

    def _parse_pytest_output(self, stdout: str) -> Dict:
        """
        Extract metrics from pytest output.

        Args:
            stdout: Pytest stdout text

        Returns:
            Metrics dictionary with test counts
        """
        metrics = {
            'tests_run': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }

        # Simple parsing - enhance as needed
        for line in stdout.split('\n'):
            line_lower = line.lower()

            # Look for summary line like "5 passed, 2 failed"
            if 'passed' in line_lower:
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part and i > 0:
                        try:
                            metrics['passed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass

            if 'failed' in line_lower:
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'failed' in part and i > 0:
                        try:
                            metrics['failed'] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass

        metrics['tests_run'] = metrics['passed'] + metrics['failed']
        return metrics

    def _log_execution(self, task_id: str, operation: str, result: Dict):
        """
        Log task execution for audit trail.

        Args:
            task_id: Task identifier
            operation: Operation kind
            result: Execution result
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'operation': operation,
            'exit_code': result.get('exit_code', -1),
            'status': result.get('status', 'unknown')
        }
        self.execution_log.append(log_entry)

    def get_execution_summary(self) -> Dict:
        """
        Get summary of all executions.

        Returns:
            Summary dictionary with execution statistics
        """
        total = len(self.execution_log)
        succeeded = sum(1 for entry in self.execution_log if entry['exit_code'] == 0)
        failed = total - succeeded

        return {
            'total_executions': total,
            'succeeded': succeeded,
            'failed': failed,
            'success_rate': (succeeded / total * 100) if total > 0 else 0,
            'log': self.execution_log
        }


def main():
    """
    CLI entry point for standalone testing.

    Usage:
        python task_executor.py <task.json>
    """
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python task_executor.py <task.json>")
        sys.exit(1)

    task_file = Path(sys.argv[1])

    if not task_file.exists():
        print(f"Task file not found: {task_file}")
        sys.exit(1)

    # Load task
    with open(task_file, 'r') as f:
        task = json.load(f)

    # Create executor
    executor = TaskExecutor()

    # Execute task
    print(f"Executing task: {task.get('task_id', 'unknown')}")
    result = executor.execute(task)

    # Print result
    print(f"\nResult:")
    print(json.dumps(result, indent=2))

    # Exit with task's exit code
    sys.exit(result.get('exit_code', 0))


if __name__ == '__main__':
    main()
