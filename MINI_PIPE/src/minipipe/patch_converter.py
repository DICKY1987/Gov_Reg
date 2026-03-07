"""
Patch Converter - Convert Tool Outputs to Unified Diff Format
Standardizes patches from different tools (aider, custom tools)
"""

# DOC_ID: DOC-CORE-ENGINE-PATCH-CONVERTER-152

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict


@dataclass
class UnifiedPatch:
    """Unified patch format."""

    patch_id: str
    workstream_id: str
    content: str
    status: str
    created_at: str
    metadata: Dict[str, Any]


class PatchConverter:
    """Convert tool-specific patches to unified diff format."""

    def __init__(self):
        self.patch_count = 0

    def convert_aider_patch(self, tool_result: Dict) -> UnifiedPatch:
        """Convert aider output to unified patch."""
        self.patch_count += 1
        patch_id = f"patch-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{self.patch_count:04d}"

        # Extract git diff from aider output
        content = tool_result.get("output", "")
        git_diff = self.extract_git_diff(content)

        return UnifiedPatch(
            patch_id=patch_id,
            workstream_id=tool_result.get("workstream_id", "unknown"),
            content=git_diff,
            status="created",
            created_at=datetime.now(UTC).isoformat(),
            metadata={"tool": "aider", "original_output_length": len(content)},
        )

    def convert_tool_patch(
        self, tool_id: str, output: str, workstream_id: str = "unknown"
    ) -> UnifiedPatch:
        """Convert generic tool output to unified patch."""
        self.patch_count += 1
        patch_id = f"patch-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{self.patch_count:04d}"

        git_diff = self.extract_git_diff(output)

        return UnifiedPatch(
            patch_id=patch_id,
            workstream_id=workstream_id,
            content=git_diff if git_diff else output,
            status="created",
            created_at=datetime.now(UTC).isoformat(),
            metadata={"tool": tool_id, "has_git_diff": bool(git_diff)},
        )

    def extract_git_diff(self, output: str) -> str:
        """Extract git diff from tool output."""
        # Look for git diff markers
        diff_pattern = r"diff --git.*?(?=diff --git|\Z)"
        matches = re.findall(diff_pattern, output, re.DOTALL)

        if matches:
            return "\n".join(matches)

        # Fallback: look for unified diff format
        unified_pattern = r"---.*?\n\+\+\+.*?(?=---|\Z)"
        matches = re.findall(unified_pattern, output, re.DOTALL)

        if matches:
            return "\n".join(matches)

        return ""

    def validate_unified_diff(self, diff: str) -> bool:
        """Validate that string is a valid unified diff."""
        if not diff:
            return False

        # Check for diff markers
        has_header = "---" in diff and "+++" in diff
        has_hunks = "@@" in diff

        return has_header or has_hunks
