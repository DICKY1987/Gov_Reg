#!/usr/bin/env python
# DOC_LINK: DOC-CORE-DETERMINISTIC-DEBUG-AUDIT-DEBUG-AUDIT-1113
"""Main CLI application for the Deterministic Debugging/Audit System."""
DOC_ID: DOC-CORE-DETERMINISTIC-DEBUG-AUDIT-DEBUG-AUDIT-1113

import sys
import json
import click
import yaml
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress

from src.schemas.ccis import CCIS
from src.core.config_manager import ConfigManager
from src.core.determinism import DeterministicContext
from src.core.event_capture import EventCapture
from src.core.trace_storage import TraceStorage
from src.core.ccis_validator import CCISValidator
from src.pipeline.engine import PipelineEngine
from src.replay.engine import ReplayEngine
from src.audit.viewer import AuditViewer
from src.core.exceptions import PipelineException

console = Console()


@click.group()
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Deterministic Debugging/Audit System CLI."""
    ctx.ensure_object(dict)

    # Load configuration
    config_path = Path(config) if config else None
    ctx.obj['config_manager'] = ConfigManager(config_path)

    # Initialize storage
    storage_config = ctx.obj['config_manager'].get_storage_config()
    ctx.obj['storage'] = TraceStorage(storage_config.database_url)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--seed', type=int, default=42, help='Random seed for determinism')
@click.option('--output', type=click.Path(), help='Output JSON file path')
@click.option('--no-store', is_flag=True, help='Do not store trace in database')
@click.pass_context
def run(ctx, input_file, seed, output, no_store):
    """Run the pipeline with a CCIS input file."""
    console.print(f"[bold blue]Running pipeline with seed={seed}[/bold blue]")

    # Load CCIS from file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            if input_file.endswith('.yaml') or input_file.endswith('.yml'):
                ccis_data = yaml.safe_load(f)
            else:
                ccis_data = json.load(f)

        ccis = CCIS(**ccis_data)
        console.print(f"[green]✓[/green] Loaded CCIS: {ccis.ccis_id}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load CCIS: {e}")
        sys.exit(1)

    # Validate CCIS
    validator = CCISValidator()
    try:
        is_valid, errors = validator.validate(ccis, strict=False)
        if is_valid:
            console.print(f"[green]✓[/green] CCIS validation passed")
        else:
            console.print(f"[yellow]![/yellow] CCIS validation warnings:")
            for error in errors:
                console.print(f"  - {error}")
    except Exception as e:
        console.print(f"[red]✗[/red] CCIS validation failed: {e}")
        sys.exit(1)

    # Execute pipeline
    context = DeterministicContext(seed=seed)
    pipeline = PipelineEngine(deterministic_context=context)
    event_capture = EventCapture()

    started_at = datetime.utcnow()

    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing pipeline...", total=9)

            result = pipeline.execute(ccis, event_capture)
            progress.update(task, completed=9)

        console.print(f"[green]✓[/green] Pipeline execution succeeded")
        console.print(f"  PSJP ID: {result['psjp']['doc_id']}")

        # Save output if requested
        if output:
            output_path = Path(output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result['psjp'], f, indent=2, default=str)
            console.print(f"[green]✓[/green] Output saved to: {output}")

        # Store trace if not disabled
        if not no_store:
            completed_at = datetime.utcnow()
            storage = ctx.obj['storage']
            storage.store_trace(
                trace_id=event_capture.trace_id,
                ccis_id=ccis.ccis_id,
                project_id=ccis.project_id,
                seed=seed,
                input_ccis=ccis.model_dump(),
                output_psjp=result['psjp'],
                events=event_capture.export_to_dict()['events'],
                started_at=started_at,
                completed_at=completed_at,
                success=True,
            )
            console.print(f"[green]✓[/green] Trace stored: {event_capture.trace_id}")

    except PipelineException as e:
        console.print(f"[red]✗[/red] Pipeline execution failed: {e}")

        if not no_store:
            completed_at = datetime.utcnow()
            storage = ctx.obj['storage']
            storage.store_trace(
                trace_id=event_capture.trace_id,
                ccis_id=ccis.ccis_id,
                project_id=ccis.project_id,
                seed=seed,
                input_ccis=ccis.model_dump(),
                output_psjp=None,
                events=event_capture.export_to_dict()['events'],
                started_at=started_at,
                completed_at=completed_at,
                success=False,
                error_message=str(e),
            )

        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True, help='Show detailed validation errors')
def validate(input_file, verbose):
    """Validate a CCIS file without executing."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            if input_file.endswith('.yaml') or input_file.endswith('.yml'):
                ccis_data = yaml.safe_load(f)
            else:
                ccis_data = json.load(f)

        ccis = CCIS(**ccis_data)

        validator = CCISValidator()
        is_valid, errors = validator.validate(ccis, strict=False)

        if is_valid:
            console.print(f"[green]✓[/green] CCIS is valid: {ccis.ccis_id}")
        else:
            console.print(f"[yellow]![/yellow] CCIS has validation issues:")
            for error in errors:
                console.print(f"  - {error}")
            if verbose:
                console.print("\nFull CCIS data:")
                console.print(json.dumps(ccis.model_dump(), indent=2, default=str))

    except Exception as e:
        console.print(f"[red]✗[/red] Validation failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('trace_id')
@click.option('--no-verify', is_flag=True, help='Skip determinism verification')
@click.pass_context
def replay(ctx, trace_id, no_verify):
    """Replay a previous pipeline execution."""
    console.print(f"[bold blue]Replaying trace: {trace_id}[/bold blue]")

    storage = ctx.obj['storage']
    replay_engine = ReplayEngine(storage)

    try:
        result = replay_engine.replay(trace_id, verify_determinism=not no_verify)

        console.print(f"[green]✓[/green] Replay succeeded")
        if result['determinism_verified']:
            console.print(f"[green]✓[/green] Determinism verified - outputs match")

    except Exception as e:
        console.print(f"[red]✗[/red] Replay failed: {e}")
        sys.exit(1)


@cli.group()
def audit():
    """Audit log viewing commands."""
    pass


@audit.command('list')
@click.option('--limit', type=int, default=20, help='Number of traces to show')
@click.option('--project', type=str, help='Filter by project ID')
@click.option('--success-only', is_flag=True, help='Show only successful traces')
@click.pass_context
def audit_list(ctx, limit, project, success_only):
    """List execution traces."""
    storage = ctx.obj['storage']
    viewer = AuditViewer(storage)

    table = viewer.list_traces(
        limit=limit,
        project_id=project,
        success_only=success_only,
    )

    console.print(table)


@audit.command('show')
@click.argument('trace_id')
@click.option('--events', is_flag=True, help='Include event details')
@click.option('--stages', is_flag=True, help='Show stage details')
@click.pass_context
def audit_show(ctx, trace_id, events, stages):
    """Show detailed trace information."""
    storage = ctx.obj['storage']
    viewer = AuditViewer(storage)

    if stages:
        output = viewer.show_stage_details(trace_id)
    else:
        output = viewer.show_trace(trace_id, include_events=events)

    console.print(output)


@audit.command('cleanup')
@click.option('--days', type=int, default=90, help='Delete traces older than N days')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def audit_cleanup(ctx, days, confirm):
    """Delete old traces."""
    if not confirm:
        if not click.confirm(f'Delete traces older than {days} days?'):
            return

    storage = ctx.obj['storage']
    try:
        deleted = storage.cleanup_old_traces(days)
        console.print(f"[green]✓[/green] Deleted {deleted} old traces")
    except Exception as e:
        console.print(f"[red]✗[/red] Cleanup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
