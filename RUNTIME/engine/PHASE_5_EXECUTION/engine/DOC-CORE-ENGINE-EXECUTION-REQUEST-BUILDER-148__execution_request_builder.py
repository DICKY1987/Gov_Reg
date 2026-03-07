# DOC_LINK: DOC-CORE-ENGINE-EXECUTION-REQUEST-BUILDER-148
"""Execution Request Builder - WS-03-01B

Builds ExecutionRequest objects for tool invocation.
"""

# DOC_ID: DOC-CORE-ENGINE-EXECUTION-REQUEST-BUILDER-148

import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Optional


def generate_ulid() -> str:
    """Generate a ULID-compatible ID"""
    return uuid.uuid4().hex.upper()[:26]


def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(UTC).isoformat() + "Z"


class ExecutionRequestBuilder:
    """Builds execution requests for tool invocation"""

    def __init__(self):
        self.request = {}

    def with_task(self, task_kind: str, description: str) -> "ExecutionRequestBuilder":
        """Set task information"""
        self.request["task_kind"] = task_kind
        self.request["description"] = description
        return self

    def with_tool(self, tool_id: str, command: str) -> "ExecutionRequestBuilder":
        """Set tool to execute"""
        self.request["tool_id"] = tool_id
        self.request["command"] = command
        return self

    def with_input(
        self, prompt: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> "ExecutionRequestBuilder":
        """Set input data"""
        if prompt:
            self.request["prompt"] = prompt
        if context:
            self.request["context"] = context
        return self

    def with_constraints(
        self, constraints: Dict[str, Any]
    ) -> "ExecutionRequestBuilder":
        """Set execution constraints"""
        self.request["constraints"] = constraints
        return self

    def with_metadata(self, **kwargs) -> "ExecutionRequestBuilder":
        """Set metadata fields"""
        if "metadata" not in self.request:
            self.request["metadata"] = {}
        self.request["metadata"].update(kwargs)
        return self

    def with_limits(
        self, timeout_seconds: int, max_retries: int = 3
    ) -> "ExecutionRequestBuilder":
        """Set execution limits"""
        self.request["timeout_seconds"] = timeout_seconds
        self.request["max_retries"] = max_retries
        return self

    def build(self) -> Dict[str, Any]:
        """Build the execution request"""
        # Generate request ID if not present
        if "request_id" not in self.request:
            self.request["request_id"] = generate_ulid()

        # Add timestamp
        if "created_at" not in self.request:
            self.request["created_at"] = now_iso()

        # Validate required fields
        required = ["task_kind", "tool_id"]
        for field in required:
            if field not in self.request:
                raise ValueError(f"Missing required field: {field}")

        return self.request.copy()

    @classmethod
    def from_task(
        cls, task_kind: str, tool_id: str, description: str = ""
    ) -> "ExecutionRequestBuilder":
        """Create builder from basic task info"""
        builder = cls()
        builder.request["task_kind"] = task_kind
        builder.request["tool_id"] = tool_id
        if description:
            builder.request["description"] = description
        return builder


def create_execution_request(
    task_kind: str, tool_id: str, prompt: Optional[str] = None, **kwargs
) -> Dict[str, Any]:
    """
    Quick helper to create an execution request.

    Args:
        task_kind: Type of task (e.g., 'code_edit')
        tool_id: Tool to execute (e.g., 'aider')
        prompt: Optional input prompt
        **kwargs: Additional fields

    Returns:
        Complete execution request dictionary
    """
    builder = ExecutionRequestBuilder.from_task(task_kind, tool_id)

    if prompt:
        builder.with_input(prompt=prompt)

    for key, value in kwargs.items():
        builder.request[key] = value

    return builder.build()
