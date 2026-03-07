#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-CORE-UI-CLI-127
"""CLI interface for UI data queries.

Provides JSON-emitting commands for querying pipeline state, suitable for
consumption by TUI/GUI frontends or external tools.

Usage:
    python -m core.ui_cli files --state in_flight --json
    python -m core.ui_cli workstreams --run-id run-123 --json
    python -m core.ui_cli dashboard --json
    python -m core.ui_cli tools --json
    python -m core.ui_cli errors --severity error --json
"""
# DOC_ID: DOC-CORE-CORE-UI-CLI-127

import argparse
import json
import sys
from datetime import datetime
from typing import Any, List

from core.ui_clients import StateClient, ToolsClient
from core.ui_models import ErrorCategory, ErrorSeverity, FileState, WorkstreamStatus


def serialize_model(obj: Any) -> Any:
    """Convert dataclass/enum to JSON-serializable dict."""
    if hasattr(obj, "__dataclass_fields__"):
        # Dataclass
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = serialize_model(value)
        return result
    elif isinstance(obj, (list, tuple)):
        return [serialize_model(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_model(v) for k, v in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "value"):
        # Enum
        return obj.value
    else:
        return obj


def output_json(data: Any) -> None:
    """Output data as formatted JSON."""
    serialized = serialize_model(data)
    print(json.dumps(serialized, indent=2))


def output_table(headers: List[str], rows: List[List[str]]) -> None:
    """Output data as a simple table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_files(args: argparse.Namespace) -> None:
    """Query file lifecycle records."""
    client = StateClient(args.db_path)

    state = FileState(args.state) if args.state else None
    files = client.list_files(
        state=state,
        workstream_id=args.workstream_id,
        run_id=args.run_id,
        tool_id=args.tool_id,
        limit=args.limit,
    )

    if args.json:
        output_json(files)
    else:
        headers = ["File ID", "Path", "State", "Workstream", "Last Processed"]
        rows = [
            [
                f.file_id[:12],
                f.current_path[:40],
                f.current_state.value,
                f.workstream_id[:12] if f.workstream_id else "-",
                (
                    f.last_processed.strftime("%Y-%m-%d %H:%M")
                    if f.last_processed
                    else "-"
                ),
            ]
            for f in files
        ]
        output_table(headers, rows)
        print(f"\nTotal: {len(files)} files")


def cmd_file_counts(args: argparse.Namespace) -> None:
    """Get file counts by state."""
    client = StateClient(args.db_path)
    counts = client.get_file_counts_by_state(args.run_id)

    if args.json:
        output_json(counts)
    else:
        headers = ["State", "Count"]
        rows = [[state, count] for state, count in sorted(counts.items())]
        output_table(headers, rows)


def cmd_workstreams(args: argparse.Namespace) -> None:
    """Query workstream records."""
    client = StateClient(args.db_path)

    status = WorkstreamStatus(args.status) if args.status else None
    workstreams = client.list_workstreams(
        run_id=args.run_id, status=status, limit=args.limit
    )

    if args.json:
        output_json(workstreams)
    else:
        headers = ["Workstream ID", "Status", "Files", "Duration", "Started"]
        rows = [
            [
                ws.ws_id[:12],
                ws.status.value,
                f"{ws.files_succeeded}/{ws.files_processed}",
                f"{ws.total_duration_sec:.1f}s" if ws.total_duration_sec else "-",
                ws.start_time.strftime("%Y-%m-%d %H:%M") if ws.start_time else "-",
            ]
            for ws in workstreams
        ]
        output_table(headers, rows)
        print(f"\nTotal: {len(workstreams)} workstreams")


def cmd_workstream_counts(args: argparse.Namespace) -> None:
    """Get workstream counts by status."""
    client = StateClient(args.db_path)
    counts = client.get_workstream_counts_by_status(args.run_id)

    if args.json:
        output_json(counts)
    else:
        headers = ["Status", "Count"]
        rows = [[status, count] for status, count in sorted(counts.items())]
        output_table(headers, rows)


def cmd_errors(args: argparse.Namespace) -> None:
    """Query error records."""
    client = StateClient(args.db_path)

    severity = ErrorSeverity(args.severity) if args.severity else None
    category = ErrorCategory(args.category) if args.category else None
    errors = client.list_errors(
        run_id=args.run_id,
        ws_id=args.workstream_id,
        severity=severity,
        category=category,
        tool_id=args.tool_id,
        limit=args.limit,
    )

    if args.json:
        output_json(errors)
    else:
        headers = ["Error ID", "Severity", "Category", "Message", "Count"]
        rows = [
            [
                e.error_id[:12],
                e.severity.value,
                e.category.value,
                e.human_message[:50],
                str(e.occurrence_count),
            ]
            for e in errors
        ]
        output_table(headers, rows)
        print(f"\nTotal: {len(errors)} errors")


def cmd_tools(args: argparse.Namespace) -> None:
    """Query tool health status."""
    client = ToolsClient(args.db_path)

    if args.tool_id:
        tool = client.get_tool_health(args.tool_id)
        if args.json:
            output_json(tool)
        else:
            if tool:
                print(f"Tool: {tool.display_name}")
                print(f"Status: {tool.status.value}")
                print(f"Success Rate: {tool.metrics.success_rate:.1%}")
                print(f"P95 Latency: {tool.metrics.p95_latency:.2f}s")
                print(
                    f"Requests (5m/15m/60m): {tool.metrics.requests_5min}/{tool.metrics.requests_15min}/{tool.metrics.requests_60min}"
                )
            else:
                print(f"Tool not found: {args.tool_id}")
    else:
        if args.summary:
            tools = client.get_tools_summary()
            if args.json:
                output_json(tools)
            else:
                headers = ["Tool", "Status", "Success Rate", "P95 Latency"]
                rows = [
                    [
                        t.tool_name,
                        t.status.value,
                        f"{t.success_rate:.1%}",
                        f"{t.p95_latency:.2f}s",
                    ]
                    for t in tools
                ]
                output_table(headers, rows)
        else:
            tools = client.list_tools()
            if args.json:
                output_json(tools)
            else:
                headers = ["Tool ID", "Name", "Status", "Success Rate", "Requests (5m)"]
                rows = [
                    [
                        t.tool_id,
                        t.display_name,
                        t.status.value,
                        f"{t.metrics.success_rate:.1%}",
                        str(t.metrics.requests_5min),
                    ]
                    for t in tools
                ]
                output_table(headers, rows)
                print(f"\nTotal: {len(tools)} tools")


def cmd_dashboard(args: argparse.Namespace) -> None:
    """Get pipeline dashboard summary."""
    client = StateClient(args.db_path)
    summary = client.get_pipeline_summary(args.run_id)

    if args.json:
        output_json(summary)
    else:
        print("PIPELINE DASHBOARD")
        print("=" * 60)
        print("\nWorkstreams:")
        print(f"  Running:    {summary.workstreams_running}")
        print(f"  Queued:     {summary.workstreams_queued}")
        print(f"  Completed:  {summary.workstreams_completed}")
        print(f"  Failed:     {summary.workstreams_failed}")
        print("\nFiles:")
        print(f"  Intake:           {summary.files_intake}")
        print(f"  Classified:       {summary.files_classified}")
        print(f"  In Flight:        {summary.files_in_flight}")
        print(f"  Awaiting Review:  {summary.files_awaiting_review}")
        print(f"  Committed:        {summary.files_committed}")
        print(f"  Quarantined:      {summary.files_quarantined}")
        print("\nThroughput:")
        print(f"  Files/hour:  {summary.files_per_hour:.1f}")
        print(f"  Jobs/hour:   {summary.jobs_per_hour:.1f}")
        print("\nErrors:")
        print(f"  Errors/hour: {summary.errors_per_hour:.1f}")
        if summary.top_error_types:
            print("  Top errors:")
            for error_type, count in summary.top_error_types:
                print(f"    - {error_type}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Query pipeline state for UI components"
    )
    parser.add_argument(
        "--db-path",
        help="Path to SQLite database (default: from env or .worktrees/pipeline_state.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Files command
    files_parser = subparsers.add_parser("files", help="Query file lifecycle records")
    files_parser.add_argument(
        "--state", choices=[s.value for s in FileState], help="Filter by state"
    )
    files_parser.add_argument("--workstream-id", help="Filter by workstream ID")
    files_parser.add_argument("--run-id", help="Filter by run ID")
    files_parser.add_argument("--tool-id", help="Filter by tool ID")
    files_parser.add_argument("--limit", type=int, default=100, help="Max results")
    files_parser.add_argument("--json", action="store_true", help="Output as JSON")
    files_parser.set_defaults(func=cmd_files)

    # File counts command
    file_counts_parser = subparsers.add_parser(
        "file-counts", help="Get file counts by state"
    )
    file_counts_parser.add_argument("--run-id", help="Filter by run ID")
    file_counts_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    file_counts_parser.set_defaults(func=cmd_file_counts)

    # Workstreams command
    ws_parser = subparsers.add_parser("workstreams", help="Query workstream records")
    ws_parser.add_argument("--run-id", help="Filter by run ID")
    ws_parser.add_argument(
        "--status", choices=[s.value for s in WorkstreamStatus], help="Filter by status"
    )
    ws_parser.add_argument("--limit", type=int, default=100, help="Max results")
    ws_parser.add_argument("--json", action="store_true", help="Output as JSON")
    ws_parser.set_defaults(func=cmd_workstreams)

    # Workstream counts command
    ws_counts_parser = subparsers.add_parser(
        "workstream-counts", help="Get workstream counts by status"
    )
    ws_counts_parser.add_argument("--run-id", help="Filter by run ID")
    ws_counts_parser.add_argument("--json", action="store_true", help="Output as JSON")
    ws_counts_parser.set_defaults(func=cmd_workstream_counts)

    # Errors command
    errors_parser = subparsers.add_parser("errors", help="Query error records")
    errors_parser.add_argument("--run-id", help="Filter by run ID")
    errors_parser.add_argument("--workstream-id", help="Filter by workstream ID")
    errors_parser.add_argument(
        "--severity",
        choices=[s.value for s in ErrorSeverity],
        help="Filter by severity",
    )
    errors_parser.add_argument(
        "--category",
        choices=[c.value for c in ErrorCategory],
        help="Filter by category",
    )
    errors_parser.add_argument("--tool-id", help="Filter by tool ID")
    errors_parser.add_argument("--limit", type=int, default=100, help="Max results")
    errors_parser.add_argument("--json", action="store_true", help="Output as JSON")
    errors_parser.set_defaults(func=cmd_errors)

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="Query tool health status")
    tools_parser.add_argument("--tool-id", help="Get specific tool by ID")
    tools_parser.add_argument(
        "--summary", action="store_true", help="Get one-line summary per tool"
    )
    tools_parser.add_argument("--json", action="store_true", help="Output as JSON")
    tools_parser.set_defaults(func=cmd_tools)

    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Get pipeline dashboard summary"
    )
    dashboard_parser.add_argument("--run-id", help="Filter by run ID")
    dashboard_parser.add_argument("--json", action="store_true", help="Output as JSON")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
