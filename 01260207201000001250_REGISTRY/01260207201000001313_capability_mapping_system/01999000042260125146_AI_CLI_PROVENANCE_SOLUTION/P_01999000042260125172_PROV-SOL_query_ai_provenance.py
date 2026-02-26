#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0997
"""
AI Provenance Query CLI Tool
Created: 2026-01-04

Query AI CLI provenance data for specific doc_ids or files.

Usage:
    # Query by doc_id
    python query_ai_provenance.py --db ai_provenance.db --doc-id DOC-123

    # Query by file path
    python query_ai_provenance.py --db ai_provenance.db --file-path test.py

    # Query specific evidence path
    python query_ai_provenance.py --db ai_provenance.db --doc-id DOC-123 --evidence provenance.ai_cli_logs.timeline.session_count

    # List all sessions
    python query_ai_provenance.py --db ai_provenance.db --list-sessions

    # Export to JSON
    python query_ai_provenance.py --db ai_provenance.db --doc-id DOC-123 --output result.json
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

from ai_cli_provenance_collector import AIProvenanceCollector, DocIdMapper


# ============================================================================
# QUERY CLI
# ============================================================================

class AIProvenanceQueryCLI:
    """CLI for querying AI provenance data."""

    def __init__(self, db_path: Path, doc_id_registry_path: Optional[Path] = None):
        self.db_path = db_path
        self.collector = AIProvenanceCollector(db_path, doc_id_registry_path)
        self.doc_id_mapper = DocIdMapper(doc_id_registry_path) if doc_id_registry_path else None

    def query_doc_id(self, doc_id: str) -> Dict[str, Any]:
        """Query all evidence for a doc_id."""
        result = {
            'doc_id': doc_id,
            'provenance': {
                'ai_cli_logs': {
                    'timeline': {
                        'exists': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.exists'),
                        'session_count': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.session_count'),
                        'tool_use_count': {
                            'view': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.tool_use_count.view'),
                            'edit': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.tool_use_count.edit'),
                            'create': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.tool_use_count.create')
                        },
                        'cli_agents': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.timeline.cli_agents')
                    },
                    'intent_signals': {
                        'migration_intent': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.intent_signals.migration_intent'),
                        'deprecation_intent': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.intent_signals.deprecation_intent'),
                        'removal_intent': self.collector.query_evidence(doc_id, 'provenance.ai_cli_logs.intent_signals.removal_intent')
                    }
                }
            }
        }

        return result

    def query_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Query evidence by file path (requires doc_id registry)."""
        if not self.doc_id_mapper:
            print("ERROR: Doc ID registry required for file path queries")
            return None

        doc_id = self.doc_id_mapper.get_doc_id(file_path)
        if not doc_id:
            print(f"WARNING: No doc_id found for file: {file_path}")
            return None

        result = self.query_doc_id(doc_id)
        result['file_path'] = file_path
        return result

    def query_evidence_path(self, doc_id: str, evidence_path: str) -> Any:
        """Query specific evidence path."""
        return self.collector.query_evidence(doc_id, evidence_path)

    def list_sessions(self) -> Dict[str, Any]:
        """List all sessions in database."""
        conn = self.collector._get_connection()
        try:
            cursor = conn.execute("""
                SELECT session_id, cli_agent, start_time, end_time, record_count
                FROM sessions
                ORDER BY start_time DESC
                LIMIT 100
            """)

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'cli_agent': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'record_count': row[4]
                })

            return {'sessions': sessions, 'total': len(sessions)}

        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self.collector._get_connection()
        try:
            # Count tables
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM file_events")
            file_event_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM intent_signals")
            intent_signal_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT doc_id) FROM file_events WHERE doc_id IS NOT NULL")
            doc_id_count = cursor.fetchone()[0]

            # Get CLI agent distribution
            cursor = conn.execute("""
                SELECT cli_agent, COUNT(*) as count
                FROM sessions
                GROUP BY cli_agent
            """)
            cli_agents = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'sessions': session_count,
                'file_events': file_event_count,
                'intent_signals': intent_signal_count,
                'unique_doc_ids': doc_id_count,
                'cli_agents': cli_agents
            }

        finally:
            conn.close()

    def print_result(self, result: Dict[str, Any]):
        """Pretty print query result."""
        if 'doc_id' in result:
            print(f"\n{'='*60}")
            print(f"AI Provenance for {result.get('doc_id', 'Unknown')}")
            if 'file_path' in result:
                print(f"File: {result['file_path']}")
            print(f"{'='*60}\n")

            prov = result.get('provenance', {}).get('ai_cli_logs', {})

            timeline = prov.get('timeline', {})
            print(f"Timeline:")
            print(f"  Exists: {timeline.get('exists', False)}")
            print(f"  Sessions: {timeline.get('session_count', 0)}")
            print(f"  CLI Agents: {', '.join(timeline.get('cli_agents', []))}")

            tool_use = timeline.get('tool_use_count', {})
            print(f"\nTool Usage:")
            print(f"  View: {tool_use.get('view', 0)}")
            print(f"  Edit: {tool_use.get('edit', 0)}")
            print(f"  Create: {tool_use.get('create', 0)}")

            intent = prov.get('intent_signals', {})
            print(f"\nIntent Signals:")
            print(f"  Migration: {intent.get('migration_intent', False)}")
            print(f"  Deprecation: {intent.get('deprecation_intent', False)}")
            print(f"  Removal: {intent.get('removal_intent', False)}")

            print(f"\n{'='*60}\n")

        elif 'sessions' in result:
            print(f"\n{'='*60}")
            print(f"Sessions ({result.get('total', 0)})")
            print(f"{'='*60}\n")

            for session in result['sessions'][:20]:  # Show first 20
                print(f"- {session['session_id']}")
                print(f"  Agent: {session['cli_agent']}")
                print(f"  Start: {session['start_time']}")
                print(f"  Records: {session['record_count']}")
                print()

        elif 'file_events' in result:
            print(f"\n{'='*60}")
            print(f"Database Statistics")
            print(f"{'='*60}\n")

            print(f"Sessions: {result['sessions']:,}")
            print(f"File Events: {result['file_events']:,}")
            print(f"Intent Signals: {result['intent_signals']:,}")
            print(f"Unique Doc IDs: {result['unique_doc_ids']:,}")

            print(f"\nCLI Agents:")
            for agent, count in result['cli_agents'].items():
                print(f"  {agent}: {count} sessions")

            print(f"\n{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query AI CLI provenance data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query by doc_id
  python query_ai_provenance.py --db ai_provenance.db --doc-id DOC-123

  # Query by file path
  python query_ai_provenance.py --db ai_provenance.db --file-path test.py --registry DOC_ID_REGISTRY.yaml

  # Query specific evidence
  python query_ai_provenance.py --db ai_provenance.db --doc-id DOC-123 --evidence provenance.ai_cli_logs.timeline.session_count

  # List sessions
  python query_ai_provenance.py --db ai_provenance.db --list-sessions

  # Get statistics
  python query_ai_provenance.py --db ai_provenance.db --stats
        """
    )

    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to AI provenance database"
    )

    parser.add_argument(
        "--registry",
        type=Path,
        help="Path to DOC_ID_REGISTRY.yaml (required for file path queries)"
    )

    parser.add_argument(
        "--doc-id",
        help="Query by doc_id"
    )

    parser.add_argument(
        "--file-path",
        help="Query by file path (requires --registry)"
    )

    parser.add_argument(
        "--evidence",
        help="Query specific evidence path (e.g., provenance.ai_cli_logs.timeline.session_count)"
    )

    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all sessions"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Save result to JSON file"
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = AIProvenanceQueryCLI(args.db, args.registry)

    # Execute query
    result = None

    if args.list_sessions:
        result = cli.list_sessions()
    elif args.stats:
        result = cli.get_statistics()
    elif args.doc_id:
        if args.evidence:
            value = cli.query_evidence_path(args.doc_id, args.evidence)
            result = {'doc_id': args.doc_id, 'evidence_path': args.evidence, 'value': value}
            print(f"\n{args.evidence}: {value}\n")
        else:
            result = cli.query_doc_id(args.doc_id)
    elif args.file_path:
        result = cli.query_file_path(args.file_path)
    else:
        parser.print_help()
        sys.exit(1)

    # Print result
    if result and not args.evidence:
        cli.print_result(result)

    # Save to file if requested
    if args.output and result:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Result saved to: {args.output}")

    sys.exit(0)


if __name__ == "__main__":
    main()
