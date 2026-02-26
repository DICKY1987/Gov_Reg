#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0991
"""
Copilot Log Parser
Created: 2026-01-04

Parses GitHub Copilot logs (JSON format) to extract:
- Intent signals from command history
- File mentions from prompts

Log Format: JSON
Log Locations:
  - C:\\Users\\richg\\.copilot\\command-history-state.json
  - C:\\Users\\richg\\.copilot\\session-state\\*.jsonl
"""

import json
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent))
from claude_log_parser import IntentSignal, detect_intent, hash_text


class CopilotCommandHistoryParser:
    """Parses Copilot command history JSON."""

    def __init__(self, history_path: Path):
        self.history_path = Path(history_path)

    def parse_intent_signals(self) -> Iterator[IntentSignal]:
        """Parse intent signals from command history.

        Yields:
            IntentSignal objects
        """
        if not self.history_path.exists():
            return

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            commands = data.get('commands', [])

            for idx, command in enumerate(commands):
                # Already has prompt_hash in fixture
                prompt_hash = command.get('prompt_hash', f'copilot_cmd_{idx}')
                keywords = command.get('keywords', [])
                timestamp_str = command.get('timestamp')

                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except Exception:
                    timestamp = datetime.utcnow()

                # Detect intent from keywords
                keywords_text = ' '.join(keywords)
                intent = detect_intent(keywords_text)

                # Only yield if intent detected
                if any(intent[k] for k in ['migration_intent', 'deprecation_intent', 'removal_intent']):
                    yield IntentSignal(
                        message_id=f'copilot_cmd_{idx}',
                        timestamp=timestamp,
                        prompt_hash=prompt_hash,
                        detected_keywords=intent['detected_keywords'],
                        migration_intent=intent['migration_intent'],
                        deprecation_intent=intent['deprecation_intent'],
                        removal_intent=intent['removal_intent']
                    )

        except json.JSONDecodeError:
            return
        except Exception:
            return


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python copilot_log_parser.py <history_file>")
        sys.exit(1)

    history_path = Path(sys.argv[1])

    parser = CopilotCommandHistoryParser(history_path)

    signals = list(parser.parse_intent_signals())
    print(f"Intent Signals: {len(signals)}")
    for signal in signals:
        intents = []
        if signal.migration_intent:
            intents.append("MIGRATION")
        if signal.deprecation_intent:
            intents.append("DEPRECATION")
        if signal.removal_intent:
            intents.append("REMOVAL")

        print(f"  {', '.join(intents):20} | {', '.join(signal.detected_keywords)}")
