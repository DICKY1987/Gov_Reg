"""AIM+ Unified CLI

Main entry point for the AIM+ command-line interface.

Commands:
- aim secrets    - Secret management
- aim health     - Health checks
- aim setup      - Bootstrap environment (Phase 2B)
- aim tools      - Tool management (Phase 2B)
- aim scan       - Environment scanner (Phase 3A)
- aim version    - Version control (Phase 3B)

Contract Version: AIM_PLUS_V1
"""
# DOC_ID: DOC-PAT-AIM-CLI-M01001A-MAIN-471

import click
from rich.console import Console

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.secrets import secrets_cli
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.health import health_cli
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.tools import tools
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.scan import scan_cli
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.version import version_cli
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.cli.commands.audit import audit


console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="AIM+")
def cli():
    """AIM+ - Unified AI Development Environment Manager

    Manage AI tools, secrets, environment configuration, and system health.

    Examples:
        aim secrets list
        aim health check
        aim tools install-all
        aim scan all
        aim version check
        aim --help
    """
    pass


# Register command groups
cli.add_command(secrets_cli)
cli.add_command(health_cli)
cli.add_command(tools)
cli.add_command(scan_cli)
cli.add_command(version_cli)
cli.add_command(audit)


@cli.command(name="status")
def status():
    """Quick status overview.

    Shows system health and configuration summary.
    """
    from modules.aim_environment import HealthMonitor
    from modules.aim_registry import load_config

    console.print("\n[bold cyan]AIM+ System Status[/bold cyan]\n")

    # Load config
    try:
        config = load_config(validate=False)
        console.print(f"[green]✓[/green] Config: v{config.get('version', 'unknown')}")

        # Show tool count
        tools = config.get("registry", {}).get("tools", {})
        console.print(f"[green]✓[/green] AI Tools: {len(tools)} configured")
    except Exception as e:
        console.print(f"[red]✗[/red] Config: {e}")

    # Run quick health check
    try:
        monitor = HealthMonitor()
        report = monitor.generate_report()

        status_color = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red"
        }.get(report["overall_status"], "white")

        console.print(f"[{status_color}]●[/{status_color}] Health: {report['overall_status']}")

        summary = report["summary"]
        console.print(f"  Pass: {summary['pass']}, Warn: {summary['warn']}, Fail: {summary['fail']}")
    except Exception as e:
        console.print(f"[red]✗[/red] Health check failed: {e}")

    console.print()


@cli.command(name="setup")
@click.option(
    "--all",
    is_flag=True,
    help="Complete setup (tools + health check + version sync)"
)
@click.option(
    "--tools",
    is_flag=True,
    help="Install tools only"
)
@click.option(
    "--sync",
    is_flag=True,
    help="Sync tool versions only"
)
@click.option(
    "--manager",
    "-m",
    type=click.Choice(["pipx", "npm", "all"]),
    default="all",
    help="Package manager to setup (default: all)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without doing it"
)
def setup(all: bool, tools: bool, sync: bool, manager: str, dry_run: bool):
    """Bootstrap AIM+ development environment.

    This command sets up your development environment by:
    - Installing all configured tools
    - Syncing to pinned versions
    - Running health checks

    Examples:
        aim setup --all          # Complete setup
        aim setup --tools        # Install tools only
        aim setup --sync         # Sync versions only
        aim setup --dry-run --all  # Preview what would be done
    """
    import asyncio
    from modules.aim_registry import ConfigLoader
    from modules.aim_environment import ToolInstaller
    from modules.aim_environment import VersionControl
    from modules.aim_environment import HealthMonitor

    try:
        console.print("\n[bold cyan]AIM+ Environment Setup[/bold cyan]\n")

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

        # Load config
        with console.status("[bold blue]Loading configuration..."):
            config = ConfigLoader().load()
            installer = ToolInstaller(config)
            vc = VersionControl(config, installer)

        # Determine what to do
        do_tools = all or tools
        do_sync = all or sync

        if not (do_tools or do_sync):
            # Default: do everything
            do_tools = True
            do_sync = True

        results = []

        # Install tools
        if do_tools:
            console.print("[bold blue]Installing tools...[/bold blue]")

            if dry_run:
                console.print("[dim]Would install tools from config[/dim]")
            else:
                managers = ["pipx", "npm"] if manager == "all" else [manager]
                for mgr in managers:
                    console.print(f"\n[cyan]Installing {mgr} tools...[/cyan]")

                    install_results = asyncio.run(
                        installer.install_from_config(mgr, rollback_on_failure=False)
                    )

                    success_count = sum(1 for r in install_results if r.success)
                    total_count = len(install_results)

                    if success_count == total_count:
                        console.print(f"[green]✓[/green] {mgr}: {success_count}/{total_count} installed")
                    else:
                        console.print(f"[yellow]⚠[/yellow] {mgr}: {success_count}/{total_count} installed")

                    results.extend(install_results)

        # Sync versions
        if do_sync:
            console.print("\n[bold blue]Syncing versions...[/bold blue]")

            sync_results = asyncio.run(vc.sync(dry_run=dry_run))

            success_count = sum(1 for _, success, _ in sync_results if success)
            total_count = len(sync_results)

            if success_count == total_count:
                console.print(f"[green]✓[/green] Versions: {success_count}/{total_count} synced")
            else:
                console.print(f"[yellow]⚠[/yellow] Versions: {success_count}/{total_count} synced")

        # Run health check
        if all and not dry_run:
            console.print("\n[bold blue]Running health check...[/bold blue]")

            monitor = HealthMonitor()
            report = monitor.generate_report()

            status = report["overall_status"]
            if status == "healthy":
                console.print(f"[green]✓[/green] Health: {status}")
            else:
                console.print(f"[yellow]⚠[/yellow] Health: {status}")

        # Summary
        console.print("\n[bold green]Setup complete![/bold green]")

        if dry_run:
            console.print("\n[yellow]This was a dry run. Run without --dry-run to apply changes.[/yellow]")
        else:
            console.print("\nNext steps:")
            console.print("  - Run [cyan]aim health check[/cyan] for detailed system status")
            console.print("  - Run [cyan]aim version check[/cyan] to verify tool versions")
            console.print("  - Run [cyan]aim --help[/cyan] for more commands")

    except Exception as e:
        console.print(f"\n[red]Setup failed:[/red] {str(e)}")
        import traceback
        if "--verbose" in click.get_current_context().args:
            console.print(traceback.format_exc())
        raise click.Abort()


@cli.command(name="status")
def status():
    """Quick status overview.

    Shows system health and configuration summary.
    """
    from modules.aim_environment import HealthMonitor
    from modules.aim_registry import load_config

    console.print("\n[bold cyan]AIM+ System Status[/bold cyan]\n")

    # Load config
    try:
        config = load_config(validate=False)
        console.print(f"[green]✓[/green] Config: v{config.get('version', 'unknown')}")

        # Show tool count
        tools = config.get("registry", {}).get("tools", {})
        console.print(f"[green]✓[/green] AI Tools: {len(tools)} configured")
    except Exception as e:
        console.print(f"[red]✗[/red] Config: {e}")

    # Run quick health check
    try:
        monitor = HealthMonitor()
        report = monitor.generate_report()

        status_color = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red"
        }.get(report["overall_status"], "white")

        console.print(f"[{status_color}]●[/{status_color}] Health: {report['overall_status']}")

        summary = report["summary"]
        console.print(f"  Pass: {summary['pass']}, Warn: {summary['warn']}, Fail: {summary['fail']}")
    except Exception as e:
        console.print(f"[red]✗[/red] Health check failed: {e}")

    console.print()


if __name__ == "__main__":
    cli()
