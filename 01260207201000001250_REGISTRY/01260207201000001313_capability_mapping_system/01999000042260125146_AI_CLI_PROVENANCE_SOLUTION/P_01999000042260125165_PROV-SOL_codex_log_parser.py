#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0990
"""
Codex Log Parser
Created: 2026-01-04

Parses Codex session logs (JSONL format) to extract:
- File events from tool requests
- Session metadata

Log Format: JSONL
Log Location: C:\\Users\\richg\\.codex\\sessions\\**\\*.jsonl
"""

import json
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Reuse from Claude parser
import sys
sys.path.insert(0, str(Path(__file__).parent))
from claude_log_parser import FileEvent, categorize_tool, hash_text


@dataclass
class CodexSession:
    """Codex session metadata."""
    session_id: str
    timestamp: datetime
    cwd: str
    model: str
    provider: str


class CodexLogParser:
    """Parses Codex JSONL logs."""

    def __init__(self, log_path: Path, repo_root: Optional[Path] = None):
        self.log_path = Path(log_path)
        self.repo_root = Path(repo_root) if repo_root else None
        self.session_id = None

    def _is_file_in_repo(self, file_path: str) -> bool:
        """Check if file is in repo scope."""
        if not self.repo_root:
            return True

        try:
            file_abs = Path(file_path).resolve()
            repo_abs = self.repo_root.resolve()
            return str(file_abs).startswith(str(repo_abs))
        except Exception:
            return False

    def parse_file_events(self) -> Iterator[FileEvent]:
        """Parse file events from Codex log.

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

                    # Extract session ID from metadata
                    if entry.get('type') == 'session_metadata':
                        self.session_id = entry.get('session_id', f'codex_line_{line_num}')

                    # Parse tool requests
                    if entry.get('type') == 'tool_request':
                        session_id = entry.get('session_id', self.session_id or f'codex_line_{line_num}')
                        tool_name = entry.get('tool')
                        file_path = entry.get('file_path')

                        if not file_path or not tool_name:
                            continue

                        if not self._is_file_in_repo(file_path):
                            continue

                        # Parse timestamp
                        timestamp_str = entry.get('timestamp')
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except Exception:
                            timestamp = datetime.utcnow()

                        yield FileEvent(
                            message_id=f"codex_{line_num}",
                            timestamp=timestamp,
                            file_path=file_path,
                            tool_name=tool_name,
                            tool_category=categorize_tool(tool_name),
                            session_id=session_id
                        )

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

    def get_session_metadata(self) -> Dict[str, Any]:
        """Get session metadata."""
        metadata = {
            'session_id': None,
            'cli_agent': 'codex',
            'log_file_path': str(self.log_path),
            'start_time': None,
            'end_time': None,
            'record_count': 0
        }

        if not self.log_path.exists():
            return metadata

        with open(self.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            metadata['record_count'] = len(lines)

            # Find session metadata and timestamps
            for line in lines:
                try:
                    entry = json.loads(line.strip())

                    if entry.get('type') == 'session_metadata':
                        metadata['session_id'] = entry.get('session_id')
                        timestamp_str = entry.get('timestamp')
                        if timestamp_str and not metadata['start_time']:
                            metadata['start_time'] = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                    # Get last timestamp
                    timestamp_str = entry.get('timestamp')
                    if timestamp_str:
                        metadata['end_time'] = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                except Exception:
                    continue

        if not metadata['session_id']:
            metadata['session_id'] = f"codex_{self.log_path.stem}"

        return metadata


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python codex_log_parser.py <log_file_path> [repo_root]")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    parser = CodexLogParser(log_path, repo_root)

    metadata = parser.get_session_metadata()
    print(f"Session: {metadata['session_id']}")
    print(f"Records: {metadata['record_count']}")

    events = list(parser.parse_file_events())
    print(f"\nFile Events: {len(events)}")
    for event in events:
        print(f"  {event.tool_category:6} | {event.file_path}")
