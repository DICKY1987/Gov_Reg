#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-CORE-UI-SETTINGS-CLI-130
"""UI Settings CLI

Command-line interface for managing UI settings, particularly the interactive tool selection.

Usage:
    python -m core.ui_settings_cli show
    python -m core.ui_settings_cli set-interactive aim
    python -m core.ui_settings_cli set-interactive aider
    python -m core.ui_settings_cli list-tools
"""
# DOC_ID: DOC-CORE-CORE-UI-SETTINGS-CLI-130

import argparse
import json
import sys

from core.ui_settings import UISettingsManager


def cmd_show(args: argparse.Namespace) -> int:
    """Show current UI settings."""
    settings = UISettingsManager()
    summary = settings.get_settings_summary()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("\n=== UI Settings ===\n")
        print(f"Interactive Tool:        {summary['interactive_tool']}")
        print(f"Mode:                    {summary['interactive_mode']}")
        print(f"Layout:                  {summary['interactive_layout']}")
        print(f"Auto-launch Interactive: {summary['auto_launch_interactive']}")

        if summary["auto_launch_headless"]:
            print(
                f"Auto-launch Headless:    {', '.join(summary['auto_launch_headless'])}"
            )

        print("\nAvailable Interactive Tools:")
        for tool in summary["available_interactive_tools"]:
            marker = " (current)" if tool == summary["interactive_tool"] else ""
            print(f"  - {tool}{marker}")

    return 0


def cmd_set_interactive(args: argparse.Namespace) -> int:
    """Set the interactive tool."""
    settings = UISettingsManager()
    tool_name = args.tool_name

    if not tool_name:
        print("Error: tool_name is required", file=sys.stderr)
        return 1

    # Check if tool is available
    available = settings.get_available_interactive_tools()
    if tool_name not in available:
        print(
            f"Error: '{tool_name}' is not available as an interactive tool",
            file=sys.stderr,
        )
        print(f"Available tools: {', '.join(available)}", file=sys.stderr)
        return 1

    # Get current tool
    current_tool = settings.get_interactive_tool()

    if current_tool == tool_name:
        print(f"'{tool_name}' is already the interactive tool")
        return 0

    # Set new interactive tool
    success = settings.set_interactive_tool(tool_name)

    if success:
        print(f"Interactive tool changed: {current_tool} → {tool_name}")
        print(f"Settings saved to: {settings.config_path}")
        return 0
    else:
        print(
            f"Error: Failed to set interactive tool to '{tool_name}'", file=sys.stderr
        )
        return 1


def cmd_list_tools(args: argparse.Namespace) -> int:
    """List all configured tools and their modes."""
    settings = UISettingsManager()
    all_tools = settings.list_all_tools()
    interactive_tool = settings.get_interactive_tool()

    if args.json:
        output = {}
        for tool_name, config in all_tools.items():
            mode = settings.get_tool_mode(tool_name)
            output[tool_name] = {
                "mode": mode,
                "is_interactive": tool_name == interactive_tool,
                "supports_headless": config.get("supports_headless", True),
                "description": config.get("description", ""),
            }
        print(json.dumps(output, indent=2))
    else:
        print("\n=== Tool Configurations ===\n")
        print(f"{'Tool':<20} {'Mode':<15} {'Description':<50}")
        print("-" * 85)

        for tool_name, config in all_tools.items():
            mode = settings.get_tool_mode(tool_name)
            desc = (
                config.get("description", "")[:47] + "..."
                if len(config.get("description", "")) > 50
                else config.get("description", "")
            )

            marker = " *" if tool_name == interactive_tool else ""
            print(f"{tool_name:<20} {mode:<15} {desc:<50}{marker}")

        print("\n* = Current interactive tool")

    return 0


def cmd_get_mode(args: argparse.Namespace) -> int:
    """Get execution mode for a specific tool."""
    settings = UISettingsManager()
    tool_name = args.tool_name

    if not tool_name:
        print("Error: tool_name is required", file=sys.stderr)
        return 1

    mode = settings.get_tool_mode(tool_name)
    is_headless = settings.is_headless(tool_name)

    if args.json:
        output = {
            "tool": tool_name,
            "mode": mode,
            "is_headless": is_headless,
            "is_interactive": not is_headless,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Tool: {tool_name}")
        print(f"Mode: {mode}")
        print(f"Headless: {is_headless}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Manage UI settings for the AI Development Pipeline"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show current UI settings")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.set_defaults(func=cmd_show)

    # Set-interactive command
    set_parser = subparsers.add_parser(
        "set-interactive", help="Set which tool runs in interactive mode"
    )
    set_parser.add_argument(
        "tool_name",
        help="Name of the tool to make interactive (e.g., aim, aider, codex)",
    )
    set_parser.set_defaults(func=cmd_set_interactive)

    # List-tools command
    list_parser = subparsers.add_parser(
        "list-tools", help="List all tools and their execution modes"
    )
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_list_tools)

    # Get-mode command
    mode_parser = subparsers.add_parser(
        "get-mode", help="Get execution mode for a specific tool"
    )
    mode_parser.add_argument("tool_name", help="Name of the tool")
    mode_parser.add_argument("--json", action="store_true", help="Output as JSON")
    mode_parser.set_defaults(func=cmd_get_mode)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        if "--verbose" in sys.argv:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
