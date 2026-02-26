#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0989
"""
Claude Log Parser
Created: 2026-01-04

Parses Claude Code project logs (JSONL format) to extract:
- File events (read_file, edit_file, write_file tool calls)
- Session metadata
- Intent signals from prompts (migration, deprecation, removal keywords)

Log Format: JSONL (one JSON object per line)
Log Location: C:\\Users\\richg\\.claude\\projects\\C--Users-richg-ALL-AI\\*.jsonl

Privacy: Only stores SHA256 hashes of prompts, never raw text
"""

import json
import hashlib
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FileEvent:
    """Represents a file operation event from Claude logs."""
    message_id: str
    timestamp: datetime
    file_path: str
    tool_name: str
    tool_category: str  # view, edit, create
    session_id: Optional[str] = None


@dataclass
class IntentSignal:
    """Represents detected intent from prompts."""
    message_id: str
    timestamp: datetime
    prompt_hash: str
    detected_keywords: List[str]
    migration_intent: bool = False
    deprecation_intent: bool = False
    removal_intent: bool = False


# ============================================================================
# INTENT KEYWORD DETECTION
# ============================================================================

INTENT_KEYWORDS = {
    'migration': ['migrate', 'migration', 'move to', 'replace with', 'switch to', 'port to'],
    'deprecation': ['deprecate', 'deprecated', 'phase out', 'sunset', 'end of life'],
    'removal': ['remove', 'delete', 'cleanup', 'clean up', 'prune', 'purge', 'eliminate']
}


def detect_intent(text: str) -> Dict[str, Any]:
    """Detect intent keywords in text.

    Args:
        text: Text to analyze (prompt or message)

    Returns:
        Dictionary with detected intents and keywords
    """
    text_lower = text.lower()
    detected = {
        'migration_intent': False,
        'deprecation_intent': False,
        'removal_intent': False,
        'detected_keywords': []
    }

    for intent_type, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected[f'{intent_type}_intent'] = True
                if keyword not in detected['detected_keywords']:
                    detected['detected_keywords'].append(keyword)

    return detected


def hash_text(text: str) -> str:
    """Create SHA256 hash of text.

    Args:
        text: Text to hash

    Returns:
        Hexadecimal SHA256 hash
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ============================================================================
# TOOL NAME MAPPING
# ============================================================================

TOOL_CATEGORY_MAP = {
    # Read operations
    'read_file': 'view',
    'glob': 'view',
    'grep': 'view',
    'list_directory': 'view',

    # Edit operations
    'edit_file': 'edit',
    'replace_in_file': 'edit',

    # Create operations
    'write_file': 'create',
    'create_file': 'create',
    'write_new_file': 'create',

    # Other operations
    'bash': 'other',
    'execute': 'other'
}


def categorize_tool(tool_name: str) -> str:
    """Categorize tool into view/edit/create/other.

    Args:
        tool_name: Name of the tool

    Returns:
        Category: view, edit, create, or other
    """
    tool_lower = tool_name.lower()

    # Direct mapping
    if tool_lower in TOOL_CATEGORY_MAP:
        return TOOL_CATEGORY_MAP[tool_lower]

    # Pattern matching
    if 'read' in tool_lower or 'view' in tool_lower or 'get' in tool_lower:
        return 'view'
    elif 'edit' in tool_lower or 'modify' in tool_lower or 'update' in tool_lower:
        return 'edit'
    elif 'write' in tool_lower or 'create' in tool_lower:
        return 'create'
    else:
        return 'other'


# ============================================================================
# CLAUDE LOG PARSER
# ============================================================================

class ClaudeLogParser:
    """Parses Claude Code JSONL logs."""

    def __init__(self, log_path: Path, repo_root: Optional[Path] = None):
        """Initialize parser.

        Args:
            log_path: Path to Claude JSONL log file
            repo_root: Optional repo root for path filtering
        """
        self.log_path = Path(log_path)
        self.repo_root = Path(repo_root) if repo_root else None
        self.session_id = self._extract_session_id()

    def _extract_session_id(self) -> str:
        """Extract session ID from log file name or path.

        Returns:
            Session ID string
        """
        # Use file name as session ID (can be enhanced)
        return f"claude_{self.log_path.stem}"

    def _is_file_in_repo(self, file_path: str) -> bool:
        """Check if file path is within repo scope.

        Args:
            file_path: File path to check

        Returns:
            True if file is in repo scope
        """
        if not self.repo_root:
            return True  # No filtering if no repo root specified

        try:
            file_abs = Path(file_path).resolve()
            repo_abs = self.repo_root.resolve()
            return str(file_abs).startswith(str(repo_abs))
        except Exception:
            return False

    def _extract_file_path(self, tool_input: Dict[str, Any]) -> Optional[str]:
        """Extract file path from tool input.

        Args:
            tool_input: Tool input dictionary

        Returns:
            File path if found, None otherwise
        """
        # Common file path field names
        path_fields = ['file_path', 'path', 'file', 'filename']

        for field in path_fields:
            if field in tool_input:
                return tool_input[field]

        return None

    def parse_file_events(self) -> Iterator[FileEvent]:
        """Parse file events from log.

        Yields:
            FileEvent objects
        """
        if not self.log_path.exists():
            return

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Look for tool_use entries
                    if entry.get('type') != 'tool_use':
                        continue

                    tool = entry.get('tool', {})
                    tool_name = tool.get('name')
                    tool_input = tool.get('input', {})

                    if not tool_name:
                        continue

                    # Extract file path
                    file_path = self._extract_file_path(tool_input)
                    if not file_path:
                        continue

                    # Filter by repo scope
                    if not self._is_file_in_repo(file_path):
                        continue

                    # Parse timestamp
                    timestamp_str = entry.get('timestamp')
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except Exception:
                        timestamp = datetime.utcnow()

                    # Create file event
                    yield FileEvent(
                        message_id=entry.get('messageId', f'line_{line_num}'),
                        timestamp=timestamp,
                        file_path=file_path,
                        tool_name=tool_name,
                        tool_category=categorize_tool(tool_name),
                        session_id=self.session_id
                    )

                except json.JSONDecodeError:
                    continue  # Skip malformed lines
                except Exception as e:
                    # Log error but continue processing
                    continue

    def parse_intent_signals(self) -> Iterator[IntentSignal]:
        """Parse intent signals from log.

        Yields:
            IntentSignal objects
        """
        if not self.log_path.exists():
            return

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Look for user messages or prompts
                    message_type = entry.get('type')
                    text = None
                    message_id = entry.get('messageId', f'line_{line_num}')

                    if message_type == 'user_message':
                        text = entry.get('text', '')
                    elif message_type == 'prompt':
                        text = entry.get('content', '')

                    if not text:
                        continue

                    # Detect intent
                    intent = detect_intent(text)

                    # Only yield if some intent was detected
                    if any(intent[k] for k in ['migration_intent', 'deprecation_intent', 'removal_intent']):
                        # Parse timestamp
                        timestamp_str = entry.get('timestamp')
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except Exception:
                            timestamp = datetime.utcnow()

                        yield IntentSignal(
                            message_id=message_id,
                            timestamp=timestamp,
                            prompt_hash=hash_text(text),
                            detected_keywords=intent['detected_keywords'],
                            migration_intent=intent['migration_intent'],
                            deprecation_intent=intent['deprecation_intent'],
                            removal_intent=intent['removal_intent']
                        )

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

    def get_session_metadata(self) -> Dict[str, Any]:
        """Get session metadata.

        Returns:
            Dictionary with session info
        """
        metadata = {
            'session_id': self.session_id,
            'cli_agent': 'claude',
            'log_file_path': str(self.log_path),
            'start_time': None,
            'end_time': None,
            'record_count': 0
        }

        if not self.log_path.exists():
            return metadata

        # Find first and last timestamps
        with open(self.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            metadata['record_count'] = len(lines)

            # First timestamp
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    timestamp_str = entry.get('timestamp')
                    if timestamp_str:
                        metadata['start_time'] = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        break
                except Exception:
                    continue

            # Last timestamp
            for line in reversed(lines):
                try:
                    entry = json.loads(line.strip())
                    timestamp_str = entry.get('timestamp')
                    if timestamp_str:
                        metadata['end_time'] = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        break
                except Exception:
                    continue

        return metadata


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python claude_log_parser.py <log_file_path> [repo_root]")
        print("\nExample:")
        print("  python claude_log_parser.py tests/fixtures/sample_logs/claude_sample.jsonl")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"Parsing Claude log: {log_path}")
    if repo_root:
        print(f"Repo root: {repo_root}")
    print("-" * 60)

    parser = ClaudeLogParser(log_path, repo_root)

    # Session metadata
    metadata = parser.get_session_metadata()
    print(f"\nSession Metadata:")
    print(f"  Session ID: {metadata['session_id']}")
    print(f"  CLI Agent: {metadata['cli_agent']}")
    print(f"  Start Time: {metadata['start_time']}")
    print(f"  End Time: {metadata['end_time']}")
    print(f"  Record Count: {metadata['record_count']}")

    # File events
    print(f"\nFile Events:")
    events = list(parser.parse_file_events())
    for event in events:
        print(f"  [{event.timestamp}] {event.tool_category.upper():6} | {event.tool_name:15} | {event.file_path}")

    print(f"\nTotal file events: {len(events)}")

    # Intent signals
    print(f"\nIntent Signals:")
    signals = list(parser.parse_intent_signals())
    for signal in signals:
        intents = []
        if signal.migration_intent:
            intents.append("MIGRATION")
        if signal.deprecation_intent:
            intents.append("DEPRECATION")
        if signal.removal_intent:
            intents.append("REMOVAL")

        print(f"  [{signal.timestamp}] {', '.join(intents):20} | Keywords: {', '.join(signal.detected_keywords)}")

    print(f"\nTotal intent signals: {len(signals)}")
