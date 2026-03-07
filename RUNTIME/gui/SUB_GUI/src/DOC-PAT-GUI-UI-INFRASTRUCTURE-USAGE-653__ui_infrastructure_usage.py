# DOC_LINK: DOC-PAT-GUI-UI-INFRASTRUCTURE-USAGE-653
"""Example usage of the UI infrastructure.

This module demonstrates how to use the event bus, file lifecycle tracking,
error records, and tool instrumentation to create a fully observable pipeline.
"""

# DOC_ID: DOC-PAT-GUI-UI-INFRASTRUCTURE-USAGE-653


from core.error_records import create_error_record
from core.file_lifecycle import (
    mark_file_committed,
    mark_file_quarantined,
    record_tool_touch,
    register_file,
    update_file_state,
)
from core.tool_instrumentation import track_tool_invocation, update_tool_health_status


def example_file_processing_workflow():
    """Example: Process a file through the pipeline with full tracking."""

    # Setup
    run_id = "run-example-001"
    ws_id = "ws-refactor-001"
    file_path = "src/example.py"

    print("=" * 60)
    print("EXAMPLE: File Processing Workflow")
    print("=" * 60)

    # Create run and workstream first
    from datetime import datetime, timezone

    from core.state.db import get_connection

    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT OR IGNORE INTO runs (run_id, status, created_at, updated_at)
            VALUES (?, 'running', ?, ?)
        """,
            (run_id, now, now),
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO workstreams (ws_id, run_id, status, created_at, updated_at)
            VALUES (?, ?, 'running', ?, ?)
        """,
            (ws_id, run_id, now, now),
        )

        conn.commit()
    finally:
        conn.close()

    # 1. Register file when discovered
    print("\n1. Discovering file...")
    file_id = register_file(
        file_path=file_path,
        origin_path="sandbox_repos/project/src/example.py",
        file_role="code",
        workstream_id=ws_id,
        run_id=run_id,
    )
    print(f"   Registered: {file_id}")

    # 2. Classify the file
    print("\n2. Classifying file...")
    update_file_state(
        file_id=file_id, new_state="classified", run_id=run_id, workstream_id=ws_id
    )
    print("   State: discovered → classified")

    # 3. Move to processing with Aider
    print("\n3. Processing with Aider...")
    update_file_state(
        file_id=file_id,
        new_state="processing",
        tool_id="aider",
        run_id=run_id,
        workstream_id=ws_id,
    )

    # Use context manager to track tool invocation
    try:
        with track_tool_invocation(
            tool_id="aider",
            tool_name="Aider",
            action="refactor",
            run_id=run_id,
            workstream_id=ws_id,
            file_id=file_id,
        ) as tracker:
            # Simulate tool work
            print("   Aider running...")

            # Simulate some output
            tracker.set_output_size(1024)

            print("   Aider completed successfully")

        # Record the touch
        record_tool_touch(
            file_id=file_id,
            tool_id="aider",
            tool_name="Aider",
            action="refactor",
            status="success",
        )

    except Exception as e:
        # Record failure
        record_tool_touch(
            file_id=file_id,
            tool_id="aider",
            tool_name="Aider",
            action="refactor",
            status="failure",
            error_message=str(e),
        )

        # Create error record
        error_id = create_error_record(
            entity_type="file",
            human_message=f"Aider failed to refactor file: {str(e)}",
            severity="error",
            category="tool_timeout" if "timeout" in str(e).lower() else "unknown",
            file_id=file_id,
            ws_id=ws_id,
            run_id=run_id,
            tool_id="aider",
            plugin="aider_adapter",
            technical_details=str(e),
            recommendation="Retry with increased timeout or different model",
        )

        # Quarantine the file
        mark_file_quarantined(
            file_id=file_id,
            reason="Aider processing failed",
            quarantine_folder=".quarantine/aider-failed",
            run_id=run_id,
            workstream_id=ws_id,
            tool_id="aider",
        )

        print(f"   ERROR: {error_id}")
        return

    # 4. Run tests
    print("\n4. Running tests...")
    update_file_state(
        file_id=file_id,
        new_state="in_flight",
        tool_id="pytest",
        run_id=run_id,
        workstream_id=ws_id,
    )

    with track_tool_invocation(
        tool_id="pytest",
        tool_name="PyTest",
        action="test",
        run_id=run_id,
        workstream_id=ws_id,
        file_id=file_id,
    ):
        print("   Tests running...")
        # Simulate test execution
        print("   Tests passed")

    record_tool_touch(
        file_id=file_id,
        tool_id="pytest",
        tool_name="PyTest",
        action="test",
        status="success",
    )

    # 5. Await review
    print("\n5. Awaiting review...")
    update_file_state(
        file_id=file_id, new_state="awaiting_review", run_id=run_id, workstream_id=ws_id
    )

    # 6. Commit to repository
    print("\n6. Committing to repository...")
    mark_file_committed(
        file_id=file_id,
        commit_sha="abc123def456",
        repo_path=file_path,
        run_id=run_id,
        workstream_id=ws_id,
    )
    print("   Committed: abc123def456")

    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 60)


def example_tool_health_monitoring():
    """Example: Monitor tool health status."""

    print("\n" + "=" * 60)
    print("EXAMPLE: Tool Health Monitoring")
    print("=" * 60)

    # Update tool health status
    print("\n1. Updating tool health status...")

    update_tool_health_status(
        tool_id="aider", status="healthy", version="0.45.0", category="ai_editor"
    )
    print("   Aider: healthy")

    update_tool_health_status(
        tool_id="codex",
        status="degraded",
        status_reason="API rate limit reached",
        version="1.0.0",
        category="ai_editor",
    )
    print("   Codex: degraded (API rate limit)")

    update_tool_health_status(
        tool_id="pytest", status="healthy", version="7.4.0", category="test_runner"
    )
    print("   PyTest: healthy")

    # Query tool health
    print("\n2. Querying tool health...")
    from core.ui_clients import ToolsClient

    client = ToolsClient()
    tools = client.list_tools()

    for tool in tools:
        print(f"   {tool.display_name}: {tool.status.value}")
        if tool.status_reason:
            print(f"     Reason: {tool.status_reason}")
        print(f"     Success rate: {tool.metrics.success_rate:.1%}")
        print(f"     Mean latency: {tool.metrics.mean_latency:.2f}s")


def example_dashboard_query():
    """Example: Query dashboard summary."""

    print("\n" + "=" * 60)
    print("EXAMPLE: Dashboard Query")
    print("=" * 60)

    from core.ui_clients import StateClient

    client = StateClient()
    summary = client.get_pipeline_summary()

    print("\nWorkstreams:")
    print(f"  Running:    {summary.workstreams_running}")
    print(f"  Queued:     {summary.workstreams_queued}")
    print(f"  Completed:  {summary.workstreams_completed}")
    print(f"  Failed:     {summary.workstreams_failed}")

    print("\nFiles:")
    print(f"  In Flight:   {summary.files_in_flight}")
    print(f"  Committed:   {summary.files_committed}")
    print(f"  Quarantined: {summary.files_quarantined}")

    print("\nThroughput:")
    print(f"  Files/hour: {summary.files_per_hour:.1f}")
    print(f"  Errors/hour: {summary.errors_per_hour:.1f}")


def example_cli_usage():
    """Example: Using the CLI interface."""

    print("\n" + "=" * 60)
    print("EXAMPLE: CLI Usage")
    print("=" * 60)

    print("\nQuery commands:")
    print("  python -m core.ui_cli dashboard --json")
    print("  python -m core.ui_cli files --state in_flight --json")
    print("  python -m core.ui_cli workstreams --run-id run-123 --json")
    print("  python -m core.ui_cli tools --json")
    print("  python -m core.ui_cli errors --severity error --json")

    print("\nExample output:")
    print("  {")
    print('    "workstreams_running": 3,')
    print('    "files_committed": 120,')
    print('    "errors_per_hour": 1.5')
    print("  }")


if __name__ == "__main__":
    # Initialize database schema first
    print("Initializing database schema...")
    from core.state.db import init_db

    init_db()
    print("Schema initialized.\n")

    # Run examples
    try:
        example_file_processing_workflow()
        example_tool_health_monitoring()
        example_dashboard_query()
        example_cli_usage()
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()
