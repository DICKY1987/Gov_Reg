# DOC_LINK: DOC-CORE-TESTS-MANUAL-TEST-POOL-624
"""Manual test for ToolProcessPool with mock aider.

Tests the core functionality of ToolProcessPool using the mock aider fixture.
"""
DOC_ID: DOC-CORE-TESTS-MANUAL-TEST-POOL-624

DOC_ID: DOC - CORE - TESTS - MANUAL - TEST - POOL - 624

import sys
import DOC-ERROR-UTILS-TIME-145__time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
)

from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.aim.bridge import ToolProcessPool


def test_pool_with_mock_aider():
    """Test pool with mock aider process."""
    print("=" * 60)
    print("Testing ToolProcessPool with Mock Aider")
    print("=" * 60)

    # Create mock registry
    mock_registry = {
        "tools": {
            "mock_aider": {
                "detectCommands": [
                    [
                        "python",
                        str(
                            project_root
                            / "tests"
                            / "aim"
                            / "fixtures"
                            / "mock_aider.py"
                        ),
                    ]
                ],
                "capabilities": ["code_generation"],
            }
        }
    }

    print("\n1. Spawning 2 mock aider instances...")
    try:
        pool = ToolProcessPool("mock_aider", count=2, registry=mock_registry)
        print(f"   ✓ Pool created with {len(pool.instances)} instances")
    except Exception as e:
        print(f"   ✗ Failed to create pool: {e}")
        return False

    # Check initial status
    print("\n2. Checking initial status...")
    statuses = pool.get_status()
    print(f"   Status: {statuses}")

    # Send prompts
    print("\n3. Sending prompts...")
    success1 = pool.send_prompt(0, "/add core/state.py")
    success2 = pool.send_prompt(1, "/add error/engine.py")
    print(f"   Instance 0: {success1}")
    print(f"   Instance 1: {success2}")

    # Read responses
    print("\n4. Reading responses (timeout=3s)...")
    time.sleep(0.5)  # Give mock time to process

    # Read startup banner first
    banner0 = pool.read_response(0, timeout=3.0)
    print(f"   Banner 0: {banner0}")

    # Read prompt
    prompt0 = pool.read_response(0, timeout=3.0)
    print(f"   Prompt 0: {prompt0}")

    # Now read actual response
    resp1 = pool.read_response(0, timeout=3.0)
    resp2 = pool.read_response(1, timeout=3.0)
    print(f"   Response 0: {resp1}")
    print(f"   Response 1: {resp2}")

    # Check stderr for errors
    print("\n4b. Checking stderr...")
    if not pool.instances[0].stderr_queue.empty():
        stderr0 = pool.instances[0].stderr_queue.get_nowait()
        print(f"   STDERR 0: {stderr0}")
    if not pool.instances[1].stderr_queue.empty():
        stderr1 = pool.instances[1].stderr_queue.get_nowait()
        print(f"   STDERR 1: {stderr1}")

    # Check health
    print("\n5. Health check...")
    health = pool.check_health()
    print(f"   Health: {health}")

    # Shutdown
    print("\n6. Shutting down pool...")
    pool.shutdown()
    print("   ✓ Shutdown complete")

    # Final status
    final_statuses = pool.get_status()
    all_dead = all(s["return_code"] is not None for s in final_statuses)
    print(f"   All processes terminated: {all_dead}")

    print("\n" + "=" * 60)
    print("Test completed successfully!" if all_dead else "Test had issues")
    print("=" * 60)

    return all_dead


if __name__ == "__main__":
    success = test_pool_with_mock_aider()
    sys.exit(0 if success else 1)
