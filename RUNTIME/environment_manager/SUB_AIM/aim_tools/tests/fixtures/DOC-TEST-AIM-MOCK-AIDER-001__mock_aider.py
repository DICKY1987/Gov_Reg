# DOC_LINK: DOC-TEST-AIM-MOCK-AIDER-001
"""Mock Aider Process for Testing

Provides a mock subprocess that simulates aider's stdin/stdout protocol.
Used for unit testing process pool without requiring real aider installation.
"""
# DOC_ID: DOC-TEST-AIM-MOCK-AIDER-001

import sys
import DOC-ERROR-UTILS-TIME-145__time
from typing import List, Optional


class MockAiderProcess:
    """Simulates aider CLI subprocess behavior.

    Provides:
    - Prompt-based responses
    - Simulated processing delays
    - Error injection for testing failure scenarios
    """

    def __init__(self, delay_ms: int = 100, fail_on_command: Optional[str] = None):
        """Initialize mock aider.

        Args:
            delay_ms: Simulated processing delay per command
            fail_on_command: Command prefix that triggers error response
        """
        self.delay_ms = delay_ms
        self.fail_on_command = fail_on_command
        self.commands_received: List[str] = []

    def run(self):
        """Run mock aider event loop (stdin → stdout)."""
        # Print startup banner
        print("Aider v0.50.0 (mock)")
        print(">", end=" ", flush=True)

        # Read commands from stdin
        for line in sys.stdin:
            command = line.strip()
            self.commands_received.append(command)

            # Simulate processing delay
            time.sleep(self.delay_ms / 1000.0)

            # Generate response
            response = self._handle_command(command)
            print(response, flush=True)
            print(">", end=" ", flush=True)

    def _handle_command(self, command: str) -> str:
        """Generate response for command.

        Args:
            command: Command received from stdin

        Returns:
            Response string to print to stdout
        """
        # Check for error injection
        if self.fail_on_command and command.startswith(self.fail_on_command):
            return f"Error: Failed to execute {command}"

        # Handle common aider commands
        if command.startswith("/add"):
            filename = command.replace("/add", "").strip()
            return f"Added {filename} to the chat"

        elif command.startswith("/ask"):
            prompt = command.replace("/ask", "").strip()
            return f"Processing: {prompt}\nCommit: mock_commit_abc123"

        elif command.startswith("/help"):
            return "Available commands: /add, /ask, /commit, /quit"

        elif command.startswith("/quit"):
            sys.exit(0)

        else:
            return f"Unknown command: {command}"


if __name__ == "__main__":
    # Parse command line args for delay and fail_on
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay-ms", type=int, default=100)
    parser.add_argument("--fail-on", type=str, default=None)
    args = parser.parse_args()

    mock = MockAiderProcess(delay_ms=args.delay_ms, fail_on_command=args.fail_on)
    mock.run()
