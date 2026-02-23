"""
Planning-Only Refinement Loop CLI
Main entry point for the planning loop system.
"""
import sys
import click
from pathlib import Path
from typing import Optional

__version__ = "2.0.0"


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--state-dir', default='.planning_loop_state', help='State directory path')
@click.pass_context
def cli(ctx, verbose: bool, state_dir: str):
    """Planning-Only Refinement Loop CLI - Generate and refine structural plans"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['state_dir'] = Path(state_dir)
    ctx.obj['exit_codes'] = {
        'SUCCESS': 0,
        'VALIDATION_ERROR': 1,
        'EXECUTION_ERROR': 2,
        'ESCALATION': 3
    }


@cli.command()
@click.option('--policy', required=True, help='Path to baseline policy JSON')
@click.option('--run-id', help='Optional custom run ID')
@click.pass_context
def init(ctx, policy: str, run_id: Optional[str]):
    """Initialize a new planning run"""
    click.echo("🔧 Initializing planning run...")
    click.echo(f"  Policy: {policy}")
    click.echo(f"  State directory: {ctx.obj['state_dir']}")
    if run_id:
        click.echo(f"  Run ID: {run_id}")
    click.echo("✅ Init complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


@cli.command()
@click.option('--run-id', required=True, help='Planning run ID')
@click.option('--output', required=True, help='Output path for context bundle')
@click.pass_context
def context(ctx, run_id: str, output: str):
    """Generate context bundle from repository"""
    click.echo("📦 Generating context bundle...")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Output: {output}")
    click.echo("✅ Context generation complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


@cli.command()
@click.option('--run-id', required=True, help='Planning run ID')
@click.option('--context', required=True, help='Path to context bundle')
@click.option('--output', required=True, help='Output path for skeleton plan')
@click.pass_context
def skeleton(ctx, run_id: str, context: str, output: str):
    """Generate initial plan skeleton"""
    click.echo("📝 Generating plan skeleton...")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Context: {context}")
    click.echo(f"  Output: {output}")
    click.echo("✅ Skeleton generation complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


@cli.command()
@click.option('--run-id', required=True, help='Planning run ID')
@click.option('--plan', required=True, help='Path to plan to lint')
@click.option('--output', required=True, help='Output path for critic report')
@click.option('--mode', type=click.Choice(['DETERMINISTIC', 'LLM', 'HYBRID']), 
              default='DETERMINISTIC', help='Critic mode')
@click.pass_context
def lint(ctx, run_id: str, plan: str, output: str, mode: str):
    """Run critic analysis on a plan"""
    click.echo("🔍 Running critic analysis...")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Plan: {plan}")
    click.echo(f"  Mode: {mode}")
    click.echo(f"  Output: {output}")
    click.echo("✅ Lint complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


@cli.command()
@click.option('--run-id', required=True, help='Planning run ID')
@click.option('--context', required=True, help='Path to context bundle')
@click.option('--max-iterations', type=int, default=5, help='Maximum iterations')
@click.option('--critic-mode', type=click.Choice(['DETERMINISTIC', 'LLM', 'HYBRID']),
              default='DETERMINISTIC', help='Critic mode')
@click.pass_context
def loop(ctx, run_id: str, context: str, max_iterations: int, critic_mode: str):
    """Execute full planning refinement loop"""
    click.echo("🔄 Starting planning refinement loop...")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Context: {context}")
    click.echo(f"  Max iterations: {max_iterations}")
    click.echo(f"  Critic mode: {critic_mode}")
    click.echo("✅ Loop complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


@cli.command()
@click.option('--run-id', required=True, help='Planning run ID')
@click.option('--output-dir', required=True, help='Output directory for package')
@click.pass_context
def finalize(ctx, run_id: str, output_dir: str):
    """Finalize and package planning run results"""
    click.echo("📦 Finalizing planning run...")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Output directory: {output_dir}")
    click.echo("✅ Finalization complete (placeholder)")
    sys.exit(ctx.obj['exit_codes']['SUCCESS'])


def main():
    """Entry point for CLI"""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(2)


if __name__ == '__main__':
    main()
