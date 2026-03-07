# DOC_LINK: DOC-CORE-SUB-GUI-CLI-ADAPTER-771
"""Centralized CLI subprocess execution wrapper with retry logic."""
# DOC_ID: DOC-CORE-SUB-GUI-CLI-ADAPTER-771
import subprocess
import sys
import DOC-ERROR-UTILS-TIME-145__time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class CLIAdapter:
    """Wrapper for subprocess execution with retry, timeout, and logging."""

    def __init__(self, logger=None):
        self.logger = logger or print
        self.execution_history: List[Dict[str, Any]] = []

    def run_script(
        self,
        script_path: Path,
        args: List[str] = None,
        timeout: int = 600,
        cwd: Path = None,
        retries: int = 0,
        retry_delay: int = 5,
        env: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Execute a script with comprehensive error handling.

        Args:
            script_path: Path to script to execute
            args: Command-line arguments
            timeout: Timeout in seconds
            cwd: Working directory
            retries: Number of retry attempts
            retry_delay: Delay between retries
            env: Environment variables

        Returns:
            Dict with success, stdout, stderr, returncode, duration
        """
        start_time = datetime.now()
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)

        last_error = None
        for attempt in range(retries + 1):
            try:
                self.logger(f"Executing: {' '.join(cmd)} (attempt {attempt + 1}/{retries + 1})")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd,
                    env=env
                )

                duration = (datetime.now() - start_time).total_seconds()

                execution_record = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "duration_seconds": duration,
                    "attempts": attempt + 1,
                    "command": cmd,
                    "timestamp": start_time.isoformat()
                }

                self.execution_history.append(execution_record)

                if result.returncode == 0:
                    self.logger(f"✅ Success in {duration:.1f}s")
                    return execution_record
                else:
                    last_error = f"Exit code {result.returncode}: {result.stderr}"
                    if attempt < retries:
                        self.logger(f"⚠️ Failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    continue

            except subprocess.TimeoutExpired:
                last_error = f"Timeout after {timeout}s"
                self.logger(f"⏱️ {last_error}")
                if attempt < retries:
                    time.sleep(retry_delay)
                continue

            except Exception as e:
                last_error = str(e)
                self.logger(f"❌ Error: {e}")
                if attempt < retries:
                    time.sleep(retry_delay)
                continue

        # All retries exhausted
        failure_record = {
            "success": False,
            "error": last_error,
            "attempts": retries + 1,
            "command": cmd,
            "timestamp": start_time.isoformat()
        }
        self.execution_history.append(failure_record)
        return failure_record

    def run_command(
        self,
        command: str,
        shell: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                **kwargs
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions."""
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.get("success"))

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }
