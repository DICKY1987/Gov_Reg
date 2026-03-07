# DOC_LINK: DOC-ERROR-ENGINE-AGENT-ADAPTERS-113
"""AI Agent Adapters for Error Remediation.

This module provides adapters for integrating AI agents (Aider, Codex, Claude)
into the error pipeline for automated code fixing.
"""

# DOC_ID: DOC-ERROR-ENGINE-AGENT-ADAPTERS-113
from __future__ import annotations

import shutil
import subprocess
import DOC-ERROR-UTILS-TIME-145__time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentInvocation:
    """Request to invoke an AI agent for error fixing."""

    agent_name: str
    files: List[str]
    error_report: Dict[str, Any]
    prompt_template: Optional[str] = None
    timeout_seconds: int = 300
    working_dir: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from AI agent invocation."""

    success: bool
    files_modified: List[str]
    stdout: str
    stderr: str
    duration_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class AgentAdapter:
    """Base class for AI agent adapters."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    def check_available(self) -> bool:
        """Check if the agent tool is available."""
        raise NotImplementedError

    def invoke(self, invocation: AgentInvocation) -> AgentResult:
        """Invoke the agent to fix errors."""
        raise NotImplementedError

    def _format_error_prompt(self, error_report: Dict[str, Any]) -> str:
        """Format error report into a prompt for the agent."""
        issues = error_report.get("issues", [])
        if not issues:
            return "No issues found."

        prompt_parts = ["Please fix the following issues:\n"]

        # Group by file
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for issue in issues:
            path = issue.get("path", "unknown")
            by_file.setdefault(path, []).append(issue)

        for file_path, file_issues in by_file.items():
            prompt_parts.append(f"\n## {file_path}")
            for issue in file_issues:
                line = issue.get("line", "?")
                code = issue.get("code", "")
                msg = issue.get("message", "")
                category = issue.get("category", "")
                prompt_parts.append(f"- Line {line} [{category}] {code}: {msg}")

        return "\n".join(prompt_parts)


class AiderAdapter(AgentAdapter):
    """Adapter for Aider CLI."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("aider", config)

    def check_available(self) -> bool:
        """Check if aider is installed."""
        return shutil.which("aider") is not None

    def invoke(self, invocation: AgentInvocation) -> AgentResult:
        """Invoke Aider to fix errors."""
        start_time = time.time()

        if not self.check_available():
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr="Aider not found in PATH",
                duration_ms=0,
                error_message="Aider CLI not installed",
            )

        # Format error report into prompt
        prompt = invocation.prompt_template or self._format_error_prompt(
            invocation.error_report
        )

        # Build aider command
        cmd = ["aider"]

        # Add files to edit
        for file_path in invocation.files:
            cmd.extend(["--file", str(file_path)])

        # Add prompt
        cmd.extend(["--message", prompt])

        # Auto-commit changes
        cmd.append("--yes")

        # Use environment model if specified
        model = self.config.get("model", "gpt-4")
        cmd.extend(["--model", model])

        # Execute aider
        working_dir = invocation.working_dir or Path.cwd()

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(working_dir),
                capture_output=True,
                text=True,
                timeout=invocation.timeout_seconds,
                env={**subprocess.os.environ, **invocation.env_vars},
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Parse output to determine success and modified files
            success = proc.returncode == 0
            files_modified = self._extract_modified_files(proc.stdout, invocation.files)

            return AgentResult(
                success=success,
                files_modified=files_modified,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                metadata={
                    "returncode": proc.returncode,
                    "model": model,
                    "prompt_length": len(prompt),
                },
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr=f"Timeout after {invocation.timeout_seconds}s",
                duration_ms=duration_ms,
                error_message="Agent invocation timed out",
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                error_message=f"Agent invocation failed: {e}",
            )

    def _extract_modified_files(
        self, stdout: str, candidate_files: List[str]
    ) -> List[str]:
        """Extract list of files that were modified from aider output."""
        # Simple heuristic: check for "Applied edit to" or similar patterns
        modified = []
        for file_path in candidate_files:
            file_name = Path(file_path).name
            if file_name in stdout or f"edit to {file_path}" in stdout.lower():
                modified.append(file_path)
        return modified


class CodexAdapter(AgentAdapter):
    """Adapter for GitHub Copilot CLI."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("codex", config)

    def check_available(self) -> bool:
        """Check if GitHub Copilot CLI is installed."""
        # Check for 'gh copilot' command
        try:
            result = subprocess.run(
                ["gh", "copilot", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def invoke(self, invocation: AgentInvocation) -> AgentResult:
        """Invoke GitHub Copilot CLI to fix errors."""
        start_time = time.time()

        if not self.check_available():
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr="GitHub Copilot CLI not found",
                duration_ms=0,
                error_message="GitHub Copilot CLI not installed or not configured",
            )

        # Format error report
        prompt = invocation.prompt_template or self._format_error_prompt(
            invocation.error_report
        )

        # Build GitHub Copilot suggest command
        cmd = ["gh", "copilot", "suggest"]

        # Add the prompt as input
        cmd.extend(["-t", "shell"])

        working_dir = invocation.working_dir or Path.cwd()

        try:
            # Use gh copilot suggest to get suggestions
            proc = subprocess.run(
                cmd,
                input=prompt,
                cwd=str(working_dir),
                capture_output=True,
                text=True,
                timeout=invocation.timeout_seconds,
                env={**subprocess.os.environ, **invocation.env_vars},
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # GitHub Copilot CLI is interactive, so we treat suggestions as success
            # In production, this would need additional parsing and application logic
            success = proc.returncode == 0

            return AgentResult(
                success=success,
                files_modified=[],  # Codex provides suggestions, not direct edits
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                metadata={
                    "returncode": proc.returncode,
                    "mode": "suggestion",
                    "prompt_length": len(prompt),
                },
                error_message=None if success else "GitHub Copilot suggestion failed",
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr=f"Timeout after {invocation.timeout_seconds}s",
                duration_ms=duration_ms,
                error_message="Agent invocation timed out",
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                error_message=f"Agent invocation failed: {e}",
            )


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("claude", config)

    def check_available(self) -> bool:
        """Check if Claude API key is configured."""
        import os

        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def invoke(self, invocation: AgentInvocation) -> AgentResult:
        """Invoke Claude API to fix errors."""
        start_time = time.time()

        if not self.check_available():
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr="ANTHROPIC_API_KEY not set",
                duration_ms=0,
                metadata={"status": "not_configured"},
                error_message="Claude API key not configured",
            )

        # Format error report
        prompt = invocation.prompt_template or self._format_error_prompt(
            invocation.error_report
        )

        try:
            import os

            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            # Read file contents
            file_contents = []
            for file_path in invocation.files:
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        file_contents.append(
                            f"File: {file_path}\n```\n{content}\n```\n"
                        )
                except Exception as e:
                    file_contents.append(f"File: {file_path} (error reading: {e})\n")

            # Build full prompt
            full_prompt = f"""You are a code fixer. Please fix the following errors in these files.

{chr(10).join(file_contents)}

{prompt}

Please provide the complete fixed code for each file."""

            # Call Claude API
            message = client.messages.create(
                model=self.config.get("model", "claude-3-5-sonnet-20241022"),
                max_tokens=self.config.get("max_tokens", 4096),
                messages=[{"role": "user", "content": full_prompt}],
                timeout=invocation.timeout_seconds,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract response
            response_text = message.content[0].text if message.content else ""

            # In production, parse response and apply fixes
            # For now, return success if we got a response
            success = bool(response_text)

            return AgentResult(
                success=success,
                files_modified=[],  # Would need to parse and apply fixes
                stdout=response_text,
                stderr="",
                duration_ms=duration_ms,
                metadata={
                    "model": message.model,
                    "usage": {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens,
                    },
                    "stop_reason": message.stop_reason,
                },
                error_message=None if success else "Claude returned empty response",
            )

        except ImportError:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr="anthropic package not installed (pip install anthropic)",
                duration_ms=duration_ms,
                metadata={"status": "missing_dependency"},
                error_message="Anthropic SDK not installed",
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                success=False,
                files_modified=[],
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                error_message=f"Claude API invocation failed: {e}",
            )


def get_agent_adapter(
    agent_name: str, config: Optional[Dict[str, Any]] = None
) -> AgentAdapter:
    """Factory function to get an agent adapter by name.

    Args:
        agent_name: Name of the agent ("aider", "codex", "claude")
        config: Optional configuration dictionary

    Returns:
        AgentAdapter instance

    Raises:
        ValueError: If agent_name is not recognized
    """
    adapters = {
        "aider": AiderAdapter,
        "codex": CodexAdapter,
        "claude": ClaudeAdapter,
    }

    adapter_class = adapters.get(agent_name.lower())
    if not adapter_class:
        raise ValueError(
            f"Unknown agent: {agent_name}. "
            f"Available agents: {', '.join(adapters.keys())}"
        )

    return adapter_class(config)


def check_agent_availability() -> Dict[str, bool]:
    """Check which agents are available on this system.

    Returns:
        Dictionary mapping agent name to availability status
    """
    return {
        "aider": AiderAdapter().check_available(),
        "codex": CodexAdapter().check_available(),
        "claude": ClaudeAdapter().check_available(),
    }
