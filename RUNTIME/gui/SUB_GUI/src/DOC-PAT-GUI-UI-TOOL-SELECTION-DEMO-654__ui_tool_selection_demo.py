# DOC_LINK: DOC-PAT-GUI-UI-TOOL-SELECTION-DEMO-654
"""Example: UI Startup with Interactive Tool Selection

This demonstrates how the UI should use the UISettingsManager to:
1. Determine which tool runs interactively
2. Launch tools in headless vs interactive mode
3. Allow users to change the interactive tool selection
"""

# DOC_ID: DOC-PAT-GUI-UI-TOOL-SELECTION-DEMO-654

from core.ui_settings import UISettingsManager


def simulate_ui_startup():
    """Simulate UI startup process with tool launching."""

    print("=" * 70)
    print("UI STARTUP SIMULATION")
    print("=" * 70)

    # Initialize settings manager
    settings = UISettingsManager()

    # Get startup configuration
    print("\n1. Loading UI Settings...")
    summary = settings.get_settings_summary()

    print(f"   Interactive Tool: {summary['interactive_tool']}")
    print(f"   Auto-launch Interactive: {summary['auto_launch_interactive']}")
    print(f"   Layout: {summary['interactive_layout']}")

    # Launch interactive tool
    if summary["auto_launch_interactive"]:
        interactive_tool = summary["interactive_tool"]
        print(f"\n2. Launching Interactive Tool: {interactive_tool}")
        print("   Mode: INTERACTIVE (normal execution with user interaction)")
        print(f"   Layout: {summary['interactive_layout']}")

        # In real UI, this would:
        # - Open a terminal panel/window
        # - Launch the tool without headless flags
        # - Allow user to send commands

        tool_config = settings.get_tool_config(interactive_tool)
        if tool_config:
            print(f"   Description: {tool_config.get('description', 'N/A')}")

    # Launch headless tools
    headless_tools = summary["auto_launch_headless"]
    if headless_tools:
        print(f"\n3. Launching Headless Tools: {', '.join(headless_tools)}")

        for tool in headless_tools:
            mode = settings.get_tool_mode(tool)
            print(f"   - {tool}: {mode.upper()}")

            # In real UI, this would:
            # - Start the process in background
            # - Redirect output to logs
            # - No user interaction required

    # List all tools and their modes
    print("\n4. Tool Execution Modes:")
    all_tools = settings.list_all_tools()
    for tool_name, config in all_tools.items():
        mode = settings.get_tool_mode(tool_name)
        is_interactive = tool_name == summary["interactive_tool"]
        marker = " (USER INTERFACE)" if is_interactive else ""
        print(f"   {tool_name:<15} {mode.upper():<12} {marker}")


def simulate_tool_switching():
    """Simulate switching the interactive tool from the UI."""

    print("\n" + "=" * 70)
    print("TOOL SWITCHING SIMULATION")
    print("=" * 70)

    settings = UISettingsManager()
    current_tool = settings.get_interactive_tool()

    print(f"\nCurrent Interactive Tool: {current_tool}")

    # Show available tools
    available = settings.get_available_interactive_tools()
    print("\nAvailable Interactive Tools:")
    for tool in available:
        is_current = tool == current_tool
        marker = " (current)" if is_current else ""
        print(f"  - {tool}{marker}")

    # Simulate user selecting a new tool
    new_tool = "aider"
    if new_tool != current_tool and new_tool in available:
        print(f"\nUser selects: {new_tool}")
        print("Switching interactive tool...")

        # In real UI, this would:
        # 1. Stop the current interactive tool process
        # 2. Update the configuration
        # 3. Launch the new tool in interactive mode
        # 4. Update the UI to show new tool is active

        success = settings.set_interactive_tool(new_tool)

        if success:
            print(f"✓ Interactive tool changed: {current_tool} → {new_tool}")
            print(f"  - {current_tool} will now run in HEADLESS mode")
            print(f"  - {new_tool} will now run in INTERACTIVE mode")
            print("  - Configuration saved")

            # Show updated modes
            print("\nUpdated Tool Modes:")
            for tool in available:
                mode = settings.get_tool_mode(tool)
                print(f"  {tool:<15} {mode.upper()}")
        else:
            print("✗ Failed to change interactive tool")

    # Change back for consistency
    print(f"\nChanging back to: {current_tool}")
    settings.set_interactive_tool(current_tool)


def demonstrate_api_usage():
    """Demonstrate programmatic API usage."""

    print("\n" + "=" * 70)
    print("API USAGE EXAMPLES")
    print("=" * 70)

    settings = UISettingsManager()

    # Example 1: Check if a tool should run headless
    print("\nExample 1: Check execution mode")
    print("```python")
    print("from core.ui_settings import UISettingsManager")
    print("settings = UISettingsManager()")
    print("is_headless = settings.is_headless('aider')")
    print("print(f'Aider headless: {is_headless}')")
    print("```")
    print(f"Output: Aider headless: {settings.is_headless('aider')}")

    # Example 2: Get tool configuration
    print("\nExample 2: Get tool configuration")
    print("```python")
    print("config = settings.get_tool_config('aim')")
    print("print(config)")
    print("```")
    config = settings.get_tool_config("aim")
    print(f"Output: {config}")

    # Example 3: Change interactive tool
    print("\nExample 3: Change interactive tool from code")
    print("```python")
    print("current = settings.get_interactive_tool()")
    print("settings.set_interactive_tool('codex')")
    print("new = settings.get_interactive_tool()")
    print("```")
    print(f"Current: {settings.get_interactive_tool()}")

    # Example 4: Integration with orchestrator
    print("\nExample 4: Orchestrator integration")
    print("```python")
    print("# In orchestrator.py:")
    print("from core.ui_settings import get_settings_manager")
    print("")
    print("settings = get_settings_manager()")
    print("tool_name = 'aider'")
    print("")
    print("if settings.is_headless(tool_name):")
    print("    # Add headless flags")
    print("    command += ['--yes', '--no-auto-commits']")
    print("else:")
    print("    # Interactive mode - allow user input")
    print("    command += ['--interactive']")
    print("```")


def main():
    """Run all demonstrations."""

    print("\n" + "=" * 70)
    print(" UI INTERACTIVE TOOL SELECTION - DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates the new UI settings system that allows:")
    print("- Configuring which tool runs interactively vs headless")
    print("- Changing the interactive tool from the UI")
    print("- Managing tool execution modes at startup")
    print()

    simulate_ui_startup()
    simulate_tool_switching()
    demonstrate_api_usage()

    print("\n" + "=" * 70)
    print(" DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Files:")
    print("  - config/ui_settings.yaml       - Configuration file")
    print("  - core/ui_settings.py           - Settings manager module")
    print("  - core/ui_settings_cli.py       - CLI interface")
    print("\nCLI Commands:")
    print("  python -m core.ui_settings_cli show")
    print("  python -m core.ui_settings_cli set-interactive <tool>")
    print("  python -m core.ui_settings_cli list-tools")
    print()


if __name__ == "__main__":
    main()
