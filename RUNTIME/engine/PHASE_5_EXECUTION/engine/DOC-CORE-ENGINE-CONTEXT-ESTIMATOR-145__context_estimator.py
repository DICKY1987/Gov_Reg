# DOC_LINK: DOC-CORE-ENGINE-CONTEXT-ESTIMATOR-145
"""Context window management and estimation.

Phase I WS-I8: Enhanced context optimization for parallel execution.
"""

# DOC_ID: DOC-CORE-ENGINE-CONTEXT-ESTIMATOR-145

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ContextProfile:
    """Context usage profile."""

    estimated_tokens: int
    file_count: int
    total_chars: int
    optimization_applied: bool = False
    pruned_files: List[str] = None

    def __post_init__(self):
        if self.pruned_files is None:
            self.pruned_files = []


class ContextEstimator:
    """Context window management."""

    TOKEN_PER_CHAR = 0.25  # Rough estimate: 4 chars per token
    DEFAULT_MAX_TOKENS = 128000  # GPT-4 Turbo context limit

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        """Initialize context estimator.

        Args:
            max_tokens: Maximum token limit
        """
        self.max_tokens = max_tokens

    def estimate_tokens(self, files: List[str], additional_context: str = "") -> int:
        """Estimate total token count for context."""
        total_chars = 0

        for f in files:
            try:
                total_chars += len(Path(f).read_text(encoding="utf-8"))
            except Exception:
                pass

        total_chars += len(additional_context)

        return int(total_chars * self.TOKEN_PER_CHAR)

    def optimize_context(
        self,
        files: List[str],
        additional_context: str = "",
        priority_files: Optional[List[str]] = None,
    ) -> ContextProfile:
        """Optimize context to fit within token limit.

        Args:
            files: List of file paths
            additional_context: Additional context string
            priority_files: Files that must be included

        Returns:
            ContextProfile with optimization results
        """
        priority_files = priority_files or []

        # Calculate tokens for each file
        file_tokens = {}
        for f in files:
            try:
                content = Path(f).read_text(encoding="utf-8")
                tokens = int(len(content) * self.TOKEN_PER_CHAR)
                file_tokens[f] = tokens
            except:
                file_tokens[f] = 0

        # Add additional context
        additional_tokens = int(len(additional_context) * self.TOKEN_PER_CHAR)
        total_tokens = sum(file_tokens.values()) + additional_tokens

        # If within limit, no optimization needed
        if total_tokens <= self.max_tokens:
            return ContextProfile(
                estimated_tokens=total_tokens,
                file_count=len(files),
                total_chars=int(total_tokens / self.TOKEN_PER_CHAR),
                optimization_applied=False,
            )

        # Prioritize files
        priority_tokens = sum(file_tokens.get(f, 0) for f in priority_files)
        remaining_budget = self.max_tokens - priority_tokens - additional_tokens

        # Select non-priority files by size (smallest first to include more files)
        non_priority = [
            (f, tokens) for f, tokens in file_tokens.items() if f not in priority_files
        ]
        non_priority.sort(key=lambda x: x[1])  # Sort by tokens ascending

        selected_files = list(priority_files)
        pruned_files = []
        current_tokens = priority_tokens

        for f, tokens in non_priority:
            if current_tokens + tokens <= remaining_budget:
                selected_files.append(f)
                current_tokens += tokens
            else:
                pruned_files.append(f)

        final_tokens = current_tokens + additional_tokens

        return ContextProfile(
            estimated_tokens=final_tokens,
            file_count=len(selected_files),
            total_chars=int(final_tokens / self.TOKEN_PER_CHAR),
            optimization_applied=True,
            pruned_files=pruned_files,
        )

    def split_context(
        self, files: List[str], chunk_size: int = 64000
    ) -> List[List[str]]:
        """Split files into chunks that fit within token limit.

        Args:
            files: List of file paths
            chunk_size: Maximum tokens per chunk

        Returns:
            List of file chunks
        """
        chunks = []
        current_chunk = []
        current_tokens = 0

        for f in files:
            try:
                content = Path(f).read_text(encoding="utf-8")
                tokens = int(len(content) * self.TOKEN_PER_CHAR)

                if current_tokens + tokens > chunk_size and current_chunk:
                    # Start new chunk
                    chunks.append(current_chunk)
                    current_chunk = [f]
                    current_tokens = tokens
                else:
                    current_chunk.append(f)
                    current_tokens += tokens
            except:
                pass

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def get_file_statistics(self, files: List[str]) -> Dict[str, Any]:
        """Get statistics about file sizes and tokens.

        Args:
            files: List of file paths

        Returns:
            Statistics dictionary
        """
        file_stats = []
        total_tokens = 0

        for f in files:
            try:
                content = Path(f).read_text(encoding="utf-8")
                tokens = int(len(content) * self.TOKEN_PER_CHAR)
                file_stats.append({"file": f, "tokens": tokens, "chars": len(content)})
                total_tokens += tokens
            except:
                pass

        # Sort by token count descending
        file_stats.sort(key=lambda x: x["tokens"], reverse=True)

        return {
            "total_files": len(files),
            "total_tokens": total_tokens,
            "largest_files": file_stats[:5],  # Top 5 largest
            "average_tokens": total_tokens // len(files) if files else 0,
        }
