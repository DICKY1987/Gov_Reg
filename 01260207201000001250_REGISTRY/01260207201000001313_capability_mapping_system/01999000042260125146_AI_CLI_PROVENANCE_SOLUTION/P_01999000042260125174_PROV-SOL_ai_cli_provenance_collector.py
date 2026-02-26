#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1011
"""
AI CLI Provenance Collector
Created: 2026-01-04

Main collector that:
1. Discovers AI CLI log files (Claude, Codex, Copilot)
2. Parses logs using specialized parsers
3. Maps file paths → doc_ids via DOC_ID_REGISTRY
4. Stores provenance data in SQLite
5. Provides evidence query interface

Usage:
    collector = AIProvenanceCollector(db_path, doc_id_registry_path)
    collector.ingest_all_logs()
    evidence = collector.query_evidence("DOC-123", "provenance.ai_cli_logs.timeline.session_count")
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from glob import glob

try:
    import yaml
except ImportError:
    yaml = None

# Import local parsers and schema
from claude_log_parser import ClaudeLogParser
from codex_log_parser import CodexLogParser
from copilot_log_parser import CopilotCommandHistoryParser
from sqlite_schema import AIProvenanceSchema


# ============================================================================
# FILE PATH UTILITIES
# ============================================================================

def normalize_path(file_path: str, repo_root: Optional[Path] = None) -> str:
    """Normalize file path for consistent hashing.

    Args:
        file_path: File path to normalize
        repo_root: Optional repo root for relative paths

    Returns:
        Normalized path string
    """
    try:
        path = Path(file_path).resolve()

        # Convert to relative if repo_root provided
        if repo_root:
            try:
                path = path.relative_to(repo_root.resolve())
            except ValueError:
                pass  # Not relative to repo_root

        # Normalize separators
        return str(path).replace('\\', '/')
    except Exception:
        return file_path.replace('\\', '/')


def hash_path(file_path: str, repo_root: Optional[Path] = None) -> str:
    """Create SHA256 hash of normalized file path.

    Args:
        file_path: File path to hash
        repo_root: Optional repo root for normalization

    Returns:
        Hexadecimal SHA256 hash
    """
    normalized = normalize_path(file_path, repo_root)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


# ============================================================================
# DOC ID MAPPER
# ============================================================================

class DocIdMapper:
    """Maps file paths to doc_ids using DOC_ID_REGISTRY."""

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize mapper.

        Args:
            registry_path: Path to DOC_ID_REGISTRY.yaml (optional)
        """
        self.registry_path = Path(registry_path) if registry_path else None
        self.cache: Dict[str, str] = {}
        self._load_registry()

    def _load_registry(self):
        """Load DOC_ID_REGISTRY.yaml into cache."""
        if not self.registry_path or not self.registry_path.exists():
            return

        if not yaml:
            print("WARNING: PyYAML not available, doc_id mapping disabled")
            return

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            documents = data.get('documents', [])
            for doc in documents:
                doc_id = doc.get('doc_id')
                file_path = doc.get('file_path')

                if doc_id and file_path:
                    # Normalize path for matching
                    normalized = normalize_path(file_path)
                    self.cache[normalized] = doc_id

        except Exception as e:
            print(f"WARNING: Failed to load DOC_ID_REGISTRY: {e}")

    def get_doc_id(self, file_path: str) -> Optional[str]:
        """Get doc_id for file path.

        Args:
            file_path: File path to lookup

        Returns:
            doc_id if found, None otherwise
        """
        normalized = normalize_path(file_path)
        return self.cache.get(normalized)


# ============================================================================
# AI CLI PROVENANCE COLLECTOR
# ============================================================================

class AIProvenanceCollector:
    """Main collector for AI CLI provenance data."""

    def __init__(
        self,
        db_path: Path,
        doc_id_registry_path: Optional[Path] = None,
        repo_root: Optional[Path] = None
    ):
        """Initialize collector.

        Args:
            db_path: Path to SQLite database
            doc_id_registry_path: Path to DOC_ID_REGISTRY.yaml
            repo_root: Repository root for path filtering
        """
        self.db_path = Path(db_path)
        self.repo_root = Path(repo_root) if repo_root else None

        # Initialize schema
        self.schema = AIProvenanceSchema(db_path)
        if not self.db_path.exists():
            self.schema.initialize()

        # Initialize doc_id mapper
        self.doc_id_mapper = DocIdMapper(doc_id_registry_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def ingest_claude_log(self, log_path: Path) -> int:
        """Ingest Claude JSONL log file.

        Args:
            log_path: Path to Claude log file

        Returns:
            Number of events ingested
        """
        parser = ClaudeLogParser(log_path, self.repo_root)

        conn = self._get_connection()
        try:
            # Insert session
            session_meta = parser.get_session_metadata()
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, cli_agent, start_time, end_time, log_file_path, record_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_meta['session_id'],
                session_meta['cli_agent'],
                session_meta['start_time'],
                session_meta['end_time'],
                session_meta['log_file_path'],
                session_meta['record_count']
            ))

            # Insert file events
            event_count = 0
            for event in parser.parse_file_events():
                # Map to doc_id
                doc_id = self.doc_id_mapper.get_doc_id(event.file_path)
                file_path_hash = hash_path(event.file_path, self.repo_root)
                repo_relative = normalize_path(event.file_path, self.repo_root)

                conn.execute("""
                    INSERT INTO file_events
                    (session_id, doc_id, file_path_hash, file_path_repo_relative,
                     timestamp, cli_agent, tool_name, tool_category, message_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.session_id,
                    doc_id,
                    file_path_hash,
                    repo_relative,
                    event.timestamp,
                    'claude',
                    event.tool_name,
                    event.tool_category,
                    event.message_id
                ))
                event_count += 1

            # Insert intent signals
            for signal in parser.parse_intent_signals():
                conn.execute("""
                    INSERT INTO intent_signals
                    (session_id, prompt_hash, detected_keywords,
                     migration_intent, deprecation_intent, removal_intent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_meta['session_id'],
                    signal.prompt_hash,
                    json.dumps(signal.detected_keywords),
                    signal.migration_intent,
                    signal.deprecation_intent,
                    signal.removal_intent,
                    signal.timestamp
                ))

            conn.commit()
            return event_count

        finally:
            conn.close()

    def ingest_codex_log(self, log_path: Path) -> int:
        """Ingest Codex JSONL log file."""
        parser = CodexLogParser(log_path, self.repo_root)

        conn = self._get_connection()
        try:
            session_meta = parser.get_session_metadata()
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, cli_agent, start_time, end_time, log_file_path, record_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_meta['session_id'],
                session_meta['cli_agent'],
                session_meta['start_time'],
                session_meta['end_time'],
                session_meta['log_file_path'],
                session_meta['record_count']
            ))

            event_count = 0
            for event in parser.parse_file_events():
                doc_id = self.doc_id_mapper.get_doc_id(event.file_path)
                file_path_hash = hash_path(event.file_path, self.repo_root)
                repo_relative = normalize_path(event.file_path, self.repo_root)

                conn.execute("""
                    INSERT INTO file_events
                    (session_id, doc_id, file_path_hash, file_path_repo_relative,
                     timestamp, cli_agent, tool_name, tool_category, message_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.session_id,
                    doc_id,
                    file_path_hash,
                    repo_relative,
                    event.timestamp,
                    'codex',
                    event.tool_name,
                    event.tool_category,
                    event.message_id
                ))
                event_count += 1

            conn.commit()
            return event_count

        finally:
            conn.close()

    def ingest_copilot_history(self, history_path: Path) -> int:
        """Ingest Copilot command history JSON."""
        parser = CopilotCommandHistoryParser(history_path)

        conn = self._get_connection()
        try:
            # Create synthetic session for Copilot
            session_id = f"copilot_{history_path.stem}"

            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, cli_agent, start_time, log_file_path, record_count)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, 'copilot', datetime.utcnow(), str(history_path), 0))

            signal_count = 0
            for signal in parser.parse_intent_signals():
                conn.execute("""
                    INSERT INTO intent_signals
                    (session_id, prompt_hash, detected_keywords,
                     migration_intent, deprecation_intent, removal_intent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    signal.prompt_hash,
                    json.dumps(signal.detected_keywords),
                    signal.migration_intent,
                    signal.deprecation_intent,
                    signal.removal_intent,
                    signal.timestamp
                ))
                signal_count += 1

            conn.commit()
            return signal_count

        finally:
            conn.close()

    def discover_logs(self, log_base_dir: Optional[Path] = None) -> Dict[str, List[Path]]:
        """Discover AI CLI log files.

        Args:
            log_base_dir: Base directory to search (defaults to user home)

        Returns:
            Dictionary mapping CLI agent to list of log files
        """
        if not log_base_dir:
            log_base_dir = Path.home()

        discovered = {
            'claude': [],
            'codex': [],
            'copilot': []
        }

        # Claude logs
        claude_pattern = log_base_dir / ".claude" / "projects" / "**" / "*.jsonl"
        discovered['claude'] = [Path(p) for p in glob(str(claude_pattern), recursive=True)]

        # Codex logs
        codex_pattern = log_base_dir / ".codex" / "sessions" / "**" / "*.jsonl"
        discovered['codex'] = [Path(p) for p in glob(str(codex_pattern), recursive=True)]

        # Copilot logs
        copilot_cmd_history = log_base_dir / ".copilot" / "command-history-state.json"
        if copilot_cmd_history.exists():
            discovered['copilot'].append(copilot_cmd_history)

        return discovered

    def ingest_all_logs(self, log_base_dir: Optional[Path] = None) -> Dict[str, int]:
        """Discover and ingest all AI CLI logs.

        Args:
            log_base_dir: Base directory to search

        Returns:
            Dictionary with ingestion statistics
        """
        logs = self.discover_logs(log_base_dir)
        stats = {'claude': 0, 'codex': 0, 'copilot': 0}

        # Ingest Claude logs
        for log_path in logs['claude']:
            try:
                count = self.ingest_claude_log(log_path)
                stats['claude'] += count
            except Exception as e:
                print(f"Error ingesting {log_path}: {e}")

        # Ingest Codex logs
        for log_path in logs['codex']:
            try:
                count = self.ingest_codex_log(log_path)
                stats['codex'] += count
            except Exception as e:
                print(f"Error ingesting {log_path}: {e}")

        # Ingest Copilot logs
        for log_path in logs['copilot']:
            try:
                count = self.ingest_copilot_history(log_path)
                stats['copilot'] += count
            except Exception as e:
                print(f"Error ingesting {log_path}: {e}")

        return stats

    def query_evidence(self, doc_id: str, evidence_path: str) -> Any:
        """Query evidence for a specific doc_id.

        Args:
            doc_id: Document ID to query
            evidence_path: Evidence path (e.g., "provenance.ai_cli_logs.timeline.session_count")

        Returns:
            Evidence value or default
        """
        conn = self._get_connection()
        try:
            # Use pre-computed view for performance
            if evidence_path == "provenance.ai_cli_logs.timeline.exists":
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM file_events WHERE doc_id = ?",
                    (doc_id,)
                )
                count = cursor.fetchone()[0]
                return count > 0

            elif evidence_path == "provenance.ai_cli_logs.timeline.session_count":
                cursor = conn.execute(
                    "SELECT session_count FROM v_file_activity_summary WHERE doc_id = ?",
                    (doc_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else 0

            elif evidence_path.startswith("provenance.ai_cli_logs.timeline.tool_use_count."):
                tool_category = evidence_path.split('.')[-1]
                cursor = conn.execute(
                    f"SELECT {tool_category}_count FROM v_file_activity_summary WHERE doc_id = ?",
                    (doc_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else 0

            elif evidence_path == "provenance.ai_cli_logs.timeline.cli_agents":
                cursor = conn.execute(
                    "SELECT cli_agents FROM v_file_activity_summary WHERE doc_id = ?",
                    (doc_id,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0].split(',')
                return []

            elif "intent" in evidence_path:
                intent_type = evidence_path.split('.')[-1].replace('_intent', '')
                cursor = conn.execute(
                    f"SELECT has_{intent_type}_intent FROM v_intent_signals_by_doc WHERE doc_id = ?",
                    (doc_id,)
                )
                row = cursor.fetchone()
                return bool(row[0]) if row else False

            else:
                # Default: return None for unknown paths
                return None

        finally:
            conn.close()


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_cli_provenance_collector.py <db_path> [doc_id_registry]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    doc_id_registry = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"Initializing collector...")
    collector = AIProvenanceCollector(db_path, doc_id_registry)

    print(f"Ingesting test logs...")
    test_logs = Path("tests/fixtures/sample_logs")
    if test_logs.exists():
        stats = {}
        stats['claude'] = collector.ingest_claude_log(test_logs / "claude_sample.jsonl")
        stats['codex'] = collector.ingest_codex_log(test_logs / "codex_sample.jsonl")
        stats['copilot'] = collector.ingest_copilot_history(test_logs / "copilot_command_history.json")

        print(f"\nIngestion Statistics:")
        print(f"  Claude events: {stats['claude']}")
        print(f"  Codex events: {stats['codex']}")
        print(f"  Copilot signals: {stats['copilot']}")

    print(f"\nDatabase Statistics:")
    db_stats = collector.schema.get_stats()
    for key, value in db_stats.items():
        print(f"  {key}: {value}")

    print(f"\nDatabase created at: {db_path.absolute()}")
